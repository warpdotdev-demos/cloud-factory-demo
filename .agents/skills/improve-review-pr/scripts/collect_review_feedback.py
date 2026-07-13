#!/usr/bin/env python3
"""Collect human feedback on automated review-pr comments.

Produces a JSON corpus the improve-review-pr skill can synthesize.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


DEFAULT_BOT_LOGINS = {
    "github-actions[bot]",
    "github-actions",
    "oz-agent[bot]",
    "oz[bot]",
    "warp[bot]",
}

REVIEW_MARKER_RE = re.compile(
    r"(\u26a0\ufe0f\s*\[IMPORTANT\]|\U0001f6a8\s*\[CRITICAL\]|"
    r"\U0001f4a1\s*\[SUGGESTION\]|\U0001f9f9\s*\[NIT\]|"
    r"Found:\s*\d+\s*critical|Powered by \[Oz\])",
    re.IGNORECASE,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect human feedback on automated PR review comments."
    )
    parser.add_argument(
        "--repo",
        help="OWNER/REPO. Defaults to GITHUB_REPOSITORY.",
    )
    parser.add_argument(
        "--since-hours",
        type=int,
        default=24,
        help="Look back this many hours from now (default: 24).",
    )
    parser.add_argument(
        "--bot-login",
        action="append",
        default=[],
        help="Additional bot login to treat as the review agent. Repeatable.",
    )
    parser.add_argument(
        "--max-prs",
        type=int,
        default=50,
        help="Maximum recently updated PRs to inspect (default: 50).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("feedback_corpus.json"),
        help="Path to write the feedback corpus JSON.",
    )
    return parser.parse_args()


def _default_repo() -> str | None:
    return (os.environ.get("GITHUB_REPOSITORY") or "").strip() or None


def _run_gh_json(args: list[str]) -> Any:
    cmd = ["gh", "api", *args]
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(
            "collect_review_feedback failed:\n"
            f"command: {' '.join(cmd)}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )
    if not result.stdout.strip():
        return None
    return json.loads(result.stdout)


def _paginate(path: str, params: list[str] | None = None) -> list[Any]:
    args = ["--paginate", path]
    if params:
        for item in params:
            args.extend(["-f", item] if "=" in item and not item.startswith("per_page") else ["-F", item])
    # Prefer query string construction for simple GETs.
    if params:
        query = "&".join(params)
        path_with_query = f"{path}?{query}"
        data = _run_gh_json(["--paginate", path_with_query])
    else:
        data = _run_gh_json(["--paginate", path])
    if data is None:
        return []
    if isinstance(data, list):
        return data
    return [data]


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def _is_bot_login(login: str, bot_logins: set[str]) -> bool:
    normalized = (login or "").strip().lower()
    if not normalized:
        return False
    if normalized in {item.lower() for item in bot_logins}:
        return True
    return normalized.endswith("[bot]")


def _looks_like_review_agent_body(body: str) -> bool:
    if not body:
        return False
    return REVIEW_MARKER_RE.search(body) is not None


def _reaction_summary(reactions: dict[str, Any] | None) -> dict[str, int]:
    if not isinstance(reactions, dict):
        return {}
    keys = ["+1", "-1", "laugh", "confused", "heart", "hooray", "rocket", "eyes"]
    return {key: int(reactions.get(key) or 0) for key in keys if int(reactions.get(key) or 0)}


def _classify_reply(body: str) -> str:
    text = (body or "").strip().lower()
    if not text:
        return "ambiguous"
    positive = [
        "good catch",
        "thanks",
        "fixed",
        "done",
        "agreed",
        "makes sense",
        "will do",
        "addressed",
        "lgtm",
        "+1",
    ]
    negative = [
        "incorrect",
        "wrong",
        "false positive",
        "not needed",
        "nitpick",
        "disagree",
        "won't fix",
        "will not fix",
        "out of scope",
        "already handled",
        "intentional",
    ]
    refined = [
        "partially",
        "mostly",
        "prefer",
        "instead",
        "alternative",
        "we usually",
        "in this repo",
        "convention",
    ]
    if any(token in text for token in negative):
        return "corrected"
    if any(token in text for token in refined):
        return "refined"
    if any(token in text for token in positive):
        return "validated"
    if len(text) < 12:
        return "ambiguous"
    return "refined"


def _list_recent_prs(owner: str, repo: str, since: datetime, max_prs: int) -> list[dict[str, Any]]:
    # Search recently updated PRs; still filter client-side by since.
    query = f"repo:{owner}/{repo} is:pr updated:>={since.date().isoformat()}"
    data = _run_gh_json(
        [
            f"search/issues?q={query.replace(' ', '+')}&sort=updated&order=desc&per_page={max_prs}"
        ]
    )
    items = data.get("items") if isinstance(data, dict) else None
    if not isinstance(items, list):
        return []
    prs: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        updated = _parse_dt(str(item.get("updated_at") or ""))
        if updated is not None and updated < since:
            continue
        prs.append(item)
    return prs[:max_prs]


def _collect_for_pr(
    owner: str,
    repo: str,
    pr_number: int,
    *,
    since: datetime,
    bot_logins: set[str],
) -> dict[str, Any]:
    reviews = _paginate(f"/repos/{owner}/{repo}/pulls/{pr_number}/reviews")
    review_comments = _paginate(f"/repos/{owner}/{repo}/pulls/{pr_number}/comments")
    issue_comments = _paginate(f"/repos/{owner}/{repo}/issues/{pr_number}/comments")

    agent_reviews: list[dict[str, Any]] = []
    for review in reviews:
        if not isinstance(review, dict):
            continue
        user = ((review.get("user") or {}).get("login") or "").strip()
        body = str(review.get("body") or "")
        submitted = _parse_dt(str(review.get("submitted_at") or ""))
        if submitted is not None and submitted < since:
            # Keep older agent reviews only if later human replies reference them.
            pass
        if _is_bot_login(user, bot_logins) or _looks_like_review_agent_body(body):
            agent_reviews.append(
                {
                    "id": review.get("id"),
                    "user": user,
                    "state": review.get("state"),
                    "submitted_at": review.get("submitted_at"),
                    "body": body,
                    "html_url": review.get("html_url"),
                }
            )

    agent_comment_ids: set[int] = set()
    agent_inline_comments: list[dict[str, Any]] = []
    for comment in review_comments:
        if not isinstance(comment, dict):
            continue
        user = ((comment.get("user") or {}).get("login") or "").strip()
        body = str(comment.get("body") or "")
        comment_id = comment.get("id")
        created = _parse_dt(str(comment.get("created_at") or ""))
        is_agent = _is_bot_login(user, bot_logins) or _looks_like_review_agent_body(body)
        if not is_agent:
            continue
        if isinstance(comment_id, int):
            agent_comment_ids.add(comment_id)
        agent_inline_comments.append(
            {
                "id": comment_id,
                "user": user,
                "created_at": comment.get("created_at"),
                "updated_at": comment.get("updated_at"),
                "path": comment.get("path"),
                "line": comment.get("line") or comment.get("original_line"),
                "side": comment.get("side"),
                "body": body,
                "html_url": comment.get("html_url"),
                "in_reply_to_id": comment.get("in_reply_to_id"),
                "reactions": _reaction_summary(comment.get("reactions")),
                "in_window": bool(created is None or created >= since),
            }
        )

    human_replies: list[dict[str, Any]] = []
    for comment in review_comments:
        if not isinstance(comment, dict):
            continue
        user = ((comment.get("user") or {}).get("login") or "").strip()
        if _is_bot_login(user, bot_logins):
            continue
        in_reply_to = comment.get("in_reply_to_id")
        created = _parse_dt(str(comment.get("created_at") or ""))
        if created is not None and created < since:
            continue
        if isinstance(in_reply_to, int) and in_reply_to in agent_comment_ids:
            body = str(comment.get("body") or "")
            human_replies.append(
                {
                    "id": comment.get("id"),
                    "user": user,
                    "created_at": comment.get("created_at"),
                    "body": body,
                    "html_url": comment.get("html_url"),
                    "in_reply_to_id": in_reply_to,
                    "classification": _classify_reply(body),
                    "source": "inline_reply",
                }
            )

    # Issue comments that appear to respond to agent reviews in-window.
    for comment in issue_comments:
        if not isinstance(comment, dict):
            continue
        user = ((comment.get("user") or {}).get("login") or "").strip()
        if _is_bot_login(user, bot_logins):
            continue
        created = _parse_dt(str(comment.get("created_at") or ""))
        if created is not None and created < since:
            continue
        body = str(comment.get("body") or "")
        if not body:
            continue
        # Keep only comments that clearly engage with review findings.
        if not any(
            token in body.lower()
            for token in [
                "review",
                "nit",
                "suggestion",
                "false positive",
                "good catch",
                "bot",
                "oz",
                "critical",
                "important",
            ]
        ):
            continue
        human_replies.append(
            {
                "id": comment.get("id"),
                "user": user,
                "created_at": comment.get("created_at"),
                "body": body,
                "html_url": comment.get("html_url"),
                "in_reply_to_id": None,
                "classification": _classify_reply(body),
                "source": "issue_comment",
            }
        )

    # Reaction-only signals on agent inline comments.
    reaction_feedback: list[dict[str, Any]] = []
    for comment in agent_inline_comments:
        reactions = comment.get("reactions") or {}
        if not reactions:
            continue
        if not comment.get("in_window"):
            continue
        classification = "ambiguous"
        if int(reactions.get("+1") or 0) > 0 and int(reactions.get("-1") or 0) == 0:
            classification = "validated"
        elif int(reactions.get("-1") or 0) > 0 or int(reactions.get("confused") or 0) > 0:
            classification = "corrected"
        reaction_feedback.append(
            {
                "agent_comment_id": comment.get("id"),
                "path": comment.get("path"),
                "html_url": comment.get("html_url"),
                "reactions": reactions,
                "classification": classification,
                "source": "reaction",
            }
        )

    return {
        "number": pr_number,
        "title": None,
        "html_url": f"https://github.com/{owner}/{repo}/pull/{pr_number}",
        "agent_reviews": agent_reviews,
        "agent_inline_comments": agent_inline_comments,
        "human_replies": human_replies,
        "reaction_feedback": reaction_feedback,
    }


def main() -> int:
    args = _parse_args()
    repo_slug = args.repo or _default_repo()
    if not repo_slug or "/" not in repo_slug:
        raise SystemExit("Repository slug is required as --repo OWNER/REPO or GITHUB_REPOSITORY.")
    owner, repo = repo_slug.split("/", 1)

    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=max(args.since_hours, 1))
    bot_logins = set(DEFAULT_BOT_LOGINS)
    bot_logins.update(args.bot_login or [])

    recent_prs = _list_recent_prs(owner, repo, since, args.max_prs)
    results: list[dict[str, Any]] = []
    for item in recent_prs:
        number = item.get("number")
        if not isinstance(number, int):
            continue
        collected = _collect_for_pr(
            owner,
            repo,
            number,
            since=since,
            bot_logins=bot_logins,
        )
        collected["title"] = item.get("title")
        # Keep PRs that either had agent activity or human replies in-window.
        has_agent = bool(collected["agent_reviews"] or collected["agent_inline_comments"])
        has_human = bool(collected["human_replies"] or collected["reaction_feedback"])
        if has_agent or has_human:
            results.append(collected)

    validated = corrected = refined = ambiguous = 0
    for pr in results:
        for reply in pr.get("human_replies") or []:
            label = reply.get("classification")
            if label == "validated":
                validated += 1
            elif label == "corrected":
                corrected += 1
            elif label == "refined":
                refined += 1
            else:
                ambiguous += 1
        for reaction in pr.get("reaction_feedback") or []:
            label = reaction.get("classification")
            if label == "validated":
                validated += 1
            elif label == "corrected":
                corrected += 1
            elif label == "refined":
                refined += 1
            else:
                ambiguous += 1

    corpus = {
        "repo": repo_slug,
        "generated_at": now.isoformat(),
        "since": since.isoformat(),
        "since_hours": args.since_hours,
        "bot_logins": sorted(bot_logins),
        "summary": {
            "prs_inspected": len(results),
            "validated": validated,
            "corrected": corrected,
            "refined": refined,
            "ambiguous": ambiguous,
        },
        "pull_requests": results,
    }

    args.output.write_text(json.dumps(corpus, indent=2) + "\n", encoding="utf-8")
    print(
        f"wrote {args.output} "
        f"(prs={len(results)}, validated={validated}, corrected={corrected}, "
        f"refined={refined}, ambiguous={ambiguous})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
