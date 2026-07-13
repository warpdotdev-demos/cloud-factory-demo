#!/usr/bin/env python3
"""Publish a validated review.json artifact as a GitHub pull request review.

This script is intended for the deterministic apply job in Cloud Factory's
review workflow. It never invents findings: it only posts the agent-authored
review after optional validation against the annotated diff.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


ALLOWED_VERDICTS = {"APPROVE", "REJECT"}
POWERED_BY_SUFFIX = "\n\n---\n_Powered by [Oz](https://warp.dev/oz)_\n"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Publish review.json as a GitHub pull request review."
    )
    parser.add_argument(
        "--review-json",
        type=Path,
        default=Path("review.json"),
        help="Path to the review.json artifact.",
    )
    parser.add_argument(
        "--diff",
        type=Path,
        default=Path("pr_diff.txt"),
        help="Optional annotated diff used for validation before publish.",
    )
    parser.add_argument(
        "--repo",
        help="Repository slug OWNER/REPO. Defaults to GITHUB_REPOSITORY.",
    )
    parser.add_argument(
        "--pr",
        type=int,
        help="Pull request number. Defaults to GitHub Actions context when available.",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip running validate_review_json.py before publishing.",
    )
    parser.add_argument(
        "--event",
        choices=("auto", "APPROVE", "REQUEST_CHANGES", "COMMENT"),
        default="auto",
        help=(
            "GitHub review event. 'auto' maps APPROVE->APPROVE and REJECT->REQUEST_CHANGES."
        ),
    )
    return parser.parse_args()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"publish failed: {path} does not exist") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"publish failed: {path} is invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit(f"publish failed: {path} must contain a JSON object")
    return payload


def _default_repo() -> str | None:
    return (os.environ.get("GITHUB_REPOSITORY") or "").strip() or None


def _default_pr_number() -> int | None:
    event_path = (os.environ.get("GITHUB_EVENT_PATH") or "").strip()
    if event_path:
        try:
            event = json.loads(Path(event_path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            event = None
        if isinstance(event, dict):
            for key in ("pull_request", "issue"):
                number = (event.get(key) or {}).get("number")
                if isinstance(number, int):
                    return number
    ref = (os.environ.get("GITHUB_REF") or "").strip()
    if ref.startswith("refs/pull/"):
        parts = ref.split("/")
        if len(parts) >= 3 and parts[2].isdigit():
            return int(parts[2])
    return None


def _validate(review_json: Path, diff: Path) -> None:
    script = Path(__file__).with_name("validate_review_json.py")
    if not script.is_file():
        raise SystemExit(f"publish failed: validator not found at {script}")
    if not diff.is_file():
        raise SystemExit(f"publish failed: annotated diff not found at {diff}")
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--review-json",
            str(review_json),
            "--diff",
            str(diff),
        ],
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit("publish failed: review.json failed validation")


def _normalize_comments(raw_comments: Any) -> list[dict[str, Any]]:
    if raw_comments is None:
        return []
    if not isinstance(raw_comments, list):
        raise SystemExit("publish failed: comments must be a list")

    comments: list[dict[str, Any]] = []
    for index, item in enumerate(raw_comments):
        if not isinstance(item, dict):
            raise SystemExit(f"publish failed: comments[{index}] must be an object")
        path = str(item.get("path") or "").strip()
        body = str(item.get("body") or "").strip()
        side = str(item.get("side") or "").strip().upper()
        line = item.get("line")
        if not path or not body or side not in {"LEFT", "RIGHT"} or not isinstance(line, int):
            raise SystemExit(
                f"publish failed: comments[{index}] is missing required path/line/side/body"
            )
        comment: dict[str, Any] = {
            "path": path,
            "line": line,
            "side": side,
            "body": body,
        }
        if item.get("start_line") is not None:
            start_line = item.get("start_line")
            start_side = str(item.get("start_side") or "").strip().upper()
            if not isinstance(start_line, int) or start_side not in {"LEFT", "RIGHT"}:
                raise SystemExit(
                    f"publish failed: comments[{index}] has invalid start_line/start_side"
                )
            comment["start_line"] = start_line
            comment["start_side"] = start_side
        comments.append(comment)
    return comments


def _event_for_verdict(verdict: str, requested: str) -> str:
    if requested != "auto":
        return requested
    return "APPROVE" if verdict == "APPROVE" else "REQUEST_CHANGES"


def main() -> int:
    args = _parse_args()
    repo = args.repo or _default_repo()
    pr_number = args.pr or _default_pr_number()
    if not repo or "/" not in repo:
        raise SystemExit("publish failed: --repo OWNER/REPO or GITHUB_REPOSITORY is required")
    if not pr_number:
        raise SystemExit("publish failed: --pr N or GitHub Actions PR context is required")

    if not args.skip_validation:
        _validate(args.review_json, args.diff)

    review = _load_json(args.review_json)
    verdict = str(review.get("verdict") or "").strip().upper()
    if verdict not in ALLOWED_VERDICTS:
        raise SystemExit('publish failed: verdict must be "APPROVE" or "REJECT"')

    body = review.get("body")
    if body is None:
        body = review.get("summary")
    if not isinstance(body, str) or not body.strip():
        raise SystemExit("publish failed: review body is required")

    comments = _normalize_comments(review.get("comments"))
    event = _event_for_verdict(verdict, args.event)

    body_text = body.strip()
    if "warp.dev/oz" not in body_text.lower():
        body_text = body_text + POWERED_BY_SUFFIX

    payload = {
        "body": body_text,
        "event": event,
        "comments": comments,
    }

    payload_path = Path("review_publish_payload.json")

    env = os.environ.copy()
    if "GH_TOKEN" not in env and "GITHUB_TOKEN" in env:
        env["GH_TOKEN"] = env["GITHUB_TOKEN"]

    def post_review(event_name: str) -> subprocess.CompletedProcess[str]:
        payload["event"] = event_name
        payload_path.write_text(json.dumps(payload), encoding="utf-8")
        return subprocess.run(
            [
                "gh",
                "api",
                "--method",
                "POST",
                f"repos/{repo}/pulls/{pr_number}/reviews",
                "--input",
                str(payload_path),
            ],
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )

    try:
        result = post_review(event)
        published_event = event

        # Many repositories leave the default Actions setting that blocks
        # GITHUB_TOKEN from approving pull requests. In that case still publish the
        # review body and inline comments as a plain COMMENT so the factory does not
        # fail after a successful agent review.
        if result.returncode != 0 and event == "APPROVE":
            combined = f"{result.stdout}\n{result.stderr}".lower()
            if (
                "not permitted to approve" in combined
                or "can not approve" in combined
                or "cannot approve" in combined
            ):
                print(
                    "APPROVE is not permitted for this token; falling back to COMMENT",
                    file=sys.stderr,
                )
                result = post_review("COMMENT")
                published_event = "COMMENT"

        if result.returncode != 0:
            sys.stderr.write(result.stdout)
            sys.stderr.write(result.stderr)
            raise SystemExit("publish failed: gh api request failed")

        print(
            f"published review for {repo}#{pr_number}: "
            f"event={published_event}, comments={len(comments)}, verdict={verdict}"
        )
        return 0
    finally:
        try:
            payload_path.unlink(missing_ok=True)
        except OSError:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
