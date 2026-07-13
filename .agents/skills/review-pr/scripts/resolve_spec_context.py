#!/usr/bin/env python3
"""Resolve product and tech spec context for a pull request.

Designed for Cloud Factory and other generic repositories that keep specs as:

  specs/<issue-slug>/PRODUCT.md
  specs/<issue-slug>/TECH.md

It prefers local checkout files, then falls back to the GitHub API when a token
is available. Unlike Warp-specific resolvers, it does not require plan-approved
labels, GH-prefixed issue directories, or oz-agent branch naming.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


API_ROOT = "https://api.github.com"
GRAPHQL_ROOT = f"{API_ROOT}/graphql"
NO_SPEC_CONTEXT_MESSAGE = "No approved or repository spec context was found for this PR."
REPO_ROOT = Path(
    (os.environ.get("OZ_REPO_ROOT") or os.environ.get("GITHUB_WORKSPACE") or "").strip()
    or Path(__file__).resolve().parents[4]
)

_CLOSING_ISSUES_QUERY = (
    "query($owner: String!, $name: String!, $number: Int!, $after: String) {"
    " repository(owner: $owner, name: $name) {"
    " pullRequest(number: $number) {"
    " closingIssuesReferences(first: 100, after: $after) {"
    " pageInfo { hasNextPage endCursor }"
    " nodes {"
    " number"
    " repository { owner { login } name }"
    " }"
    " }"
    " }"
    " }"
    " }"
)

_MANUAL_LINKED_ISSUES_QUERY = (
    "query($owner: String!, $name: String!, $number: Int!, $after: String) {"
    " repository(owner: $owner, name: $name) {"
    " pullRequest(number: $number) {"
    " timelineItems(first: 100, after: $after, itemTypes: [CONNECTED_EVENT, DISCONNECTED_EVENT]) {"
    " pageInfo { hasNextPage endCursor }"
    " nodes {"
    " __typename"
    " ... on ConnectedEvent {"
    " subject {"
    " __typename"
    " ... on Issue {"
    " number"
    " repository { owner { login } name }"
    " }"
    " }"
    " }"
    " ... on DisconnectedEvent {"
    " subject {"
    " __typename"
    " ... on Issue {"
    " number"
    " repository { owner { login } name }"
    " }"
    " }"
    " }"
    " }"
    " }"
    " }"
    " }"
    " }"
)

ISSUE_REF_PATTERN = re.compile(
    r"(?:(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+)?#(\d+)",
    re.IGNORECASE,
)
BRANCH_ISSUE_PATTERN = re.compile(
    r"(?:^|/)(?:spec|implement|feature|fix|issue)[-/]?(\d+)(?:$|[/-])",
    re.IGNORECASE,
)
SPEC_DIR_ISSUE_PATTERN = re.compile(r"^specs/[^/]*?(?:issue[-_])?(\d+)[^/]*/", re.IGNORECASE)
SPEC_FILENAMES = ("PRODUCT.md", "TECH.md", "product.md", "tech.md")


def _resolve_token() -> str | None:
    token = (os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or "").strip()
    return token or None


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resolve product/tech spec context for a pull request."
    )
    parser.add_argument(
        "--repo",
        help="Repository slug in OWNER/REPO format. Defaults to GITHUB_REPOSITORY.",
    )
    parser.add_argument(
        "--pr",
        type=int,
        help="Pull request number. Defaults to the number extracted from GITHUB_REF.",
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=REPO_ROOT,
        help="Local checkout root used to discover checked-in specs.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the rendered markdown. Prints to stdout by default.",
    )
    return parser.parse_args()


def _gh_request(
    path_or_url: str,
    *,
    token: str,
    accept: str = "application/vnd.github+json",
    params: dict[str, str] | None = None,
    method: str = "GET",
    payload: bytes | None = None,
    allow_http_error: bool = False,
) -> tuple[int, bytes, dict[str, str]]:
    url = path_or_url if path_or_url.startswith("https://") else f"{API_ROOT}{path_or_url}"
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, data=payload, method=method)  # noqa: S310
    request.add_header("Authorization", f"Bearer {token}")
    request.add_header("Accept", accept)
    request.add_header("X-GitHub-Api-Version", "2022-11-28")
    request.add_header("User-Agent", "cloud-factory-resolve-spec-context")
    if payload is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request) as response:  # noqa: S310
            return response.status, response.read(), dict(response.headers)
    except urllib.error.HTTPError as exc:
        body = exc.read() if exc.fp is not None else b""
        if allow_http_error:
            return exc.code, body, dict(exc.headers or {})
        detail = body.decode("utf-8", errors="replace")[:500]
        raise SystemExit(
            f"GitHub API request failed ({exc.code}) for {path_or_url}: {detail}"
        ) from exc


def _gh_json(
    path: str,
    *,
    token: str,
    params: dict[str, str] | None = None,
    allow_http_error: bool = False,
) -> tuple[int, Any]:
    status, body, _headers = _gh_request(
        path,
        token=token,
        params=params,
        allow_http_error=allow_http_error,
    )
    return status, json.loads(body.decode("utf-8"))


def _parse_next_link(link_header: str) -> str | None:
    if not link_header:
        return None
    for piece in link_header.split(","):
        segment = piece.strip()
        if not segment.startswith("<"):
            continue
        end = segment.find(">")
        if end == -1:
            continue
        url = segment[1:end]
        rel_part = segment[end + 1 :]
        if 'rel="next"' not in rel_part:
            continue
        parsed = urllib.parse.urlparse(url)
        return parsed.path + (f"?{parsed.query}" if parsed.query else "")
    return None


def _gh_paginated_json(
    path: str,
    *,
    token: str,
    params: dict[str, str] | None = None,
    per_page: int = 100,
) -> list[Any]:
    merged_params = dict(params or {})
    merged_params.setdefault("per_page", str(per_page))
    next_path: str | None = (
        f"{path}?{urllib.parse.urlencode(merged_params)}" if merged_params else path
    )
    items: list[Any] = []
    while next_path:
        status, body, headers = _gh_request(next_path, token=token)
        if status != 200:
            raise SystemExit(f"GitHub API returned status {status} for {next_path}")
        page = json.loads(body.decode("utf-8"))
        if not isinstance(page, list):
            raise SystemExit(
                f"Expected JSON array from {next_path}, got {type(page).__name__}."
            )
        items.extend(page)
        next_path = _parse_next_link(headers.get("Link") or headers.get("link") or "")
    return items


def _gh_graphql_json(query: str, variables: dict[str, Any], *, token: str) -> dict[str, Any]:
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    _status, body, _headers = _gh_request(
        GRAPHQL_ROOT,
        token=token,
        accept="application/json",
        method="POST",
        payload=payload,
    )
    data = json.loads(body.decode("utf-8"))
    errors = data.get("errors") or []
    if errors:
        raise SystemExit(f"GitHub GraphQL request failed: {errors}")
    return data


def _normalize_github_linked_issue(node: Any, *, source: str) -> dict[str, Any] | None:
    if not isinstance(node, dict):
        return None
    number = node.get("number")
    if not isinstance(number, int):
        return None
    repository = node.get("repository") or {}
    owner = ((repository.get("owner") or {}).get("login") or "").strip()
    repo = str(repository.get("name") or "").strip()
    if not owner or not repo:
        return None
    return {
        "owner": owner,
        "repo": repo,
        "number": number,
        "source": source,
    }


def _graphql_pull_request_data(
    owner: str,
    repo: str,
    pr_number: int,
    query: str,
    *,
    token: str,
    after: str | None,
) -> dict[str, Any]:
    data = _gh_graphql_json(
        query,
        {
            "owner": owner,
            "name": repo,
            "number": int(pr_number),
            "after": after,
        },
        token=token,
    )
    return (((data.get("data") or {}).get("repository") or {}).get("pullRequest") or {})


def _fetch_closing_issue_references(
    owner: str,
    repo: str,
    pr_number: int,
    *,
    token: str,
) -> list[dict[str, Any]]:
    linked: dict[tuple[str, str, int, str], dict[str, Any]] = {}
    cursor: str | None = None
    while True:
        pr_data = _graphql_pull_request_data(
            owner,
            repo,
            pr_number,
            _CLOSING_ISSUES_QUERY,
            token=token,
            after=cursor,
        )
        closing_refs = pr_data.get("closingIssuesReferences") or {}
        for node in closing_refs.get("nodes") or []:
            issue_ref = _normalize_github_linked_issue(
                node,
                source="closingIssuesReferences",
            )
            if issue_ref is None:
                continue
            key = (
                issue_ref["owner"].lower(),
                issue_ref["repo"].lower(),
                int(issue_ref["number"]),
                str(issue_ref["source"]),
            )
            linked[key] = issue_ref
        page_info = closing_refs.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")
        if not cursor:
            break
    return list(linked.values())


def _fetch_manual_linked_issue_references(
    owner: str,
    repo: str,
    pr_number: int,
    *,
    token: str,
) -> list[dict[str, Any]]:
    connected: dict[tuple[str, str, int], dict[str, Any]] = {}
    cursor: str | None = None
    while True:
        pr_data = _graphql_pull_request_data(
            owner,
            repo,
            pr_number,
            _MANUAL_LINKED_ISSUES_QUERY,
            token=token,
            after=cursor,
        )
        timeline_items = pr_data.get("timelineItems") or {}
        for node in timeline_items.get("nodes") or []:
            if not isinstance(node, dict):
                continue
            issue_ref = _normalize_github_linked_issue(
                node.get("subject"),
                source="manualLink",
            )
            if issue_ref is None:
                continue
            key = (
                issue_ref["owner"].lower(),
                issue_ref["repo"].lower(),
                int(issue_ref["number"]),
            )
            typename = str(node.get("__typename") or "")
            if typename == "ConnectedEvent":
                connected[key] = issue_ref
            elif typename == "DisconnectedEvent":
                connected.pop(key, None)
        page_info = timeline_items.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")
        if not cursor:
            break
    return list(connected.values())


def _dedupe_ints(values: list[int]) -> list[int]:
    return list(dict.fromkeys(int(value) for value in values))


def _same_repo_issue_numbers(
    owner: str,
    repo: str,
    issue_refs: list[dict[str, Any]],
) -> list[int]:
    normalized_owner = owner.lower()
    normalized_repo = repo.lower()
    return _dedupe_ints(
        [
            int(issue_ref["number"])
            for issue_ref in issue_refs
            if str(issue_ref.get("owner") or "").lower() == normalized_owner
            and str(issue_ref.get("repo") or "").lower() == normalized_repo
        ]
    )


def _issue_numbers_from_text(text: str) -> list[int]:
    return _dedupe_ints([int(match.group(1)) for match in ISSUE_REF_PATTERN.finditer(text or "")])


def _issue_numbers_from_branch(head_ref: str) -> list[int]:
    return _dedupe_ints(
        [int(match.group(1)) for match in BRANCH_ISSUE_PATTERN.finditer(head_ref or "")]
    )


def _issue_numbers_from_changed_files(changed_files: list[str]) -> list[int]:
    return _dedupe_ints(
        [
            int(match.group(1))
            for filename in changed_files
            for match in [SPEC_DIR_ISSUE_PATTERN.match(filename)]
            if match
        ]
    )


def _fetch_pull(owner: str, repo: str, pr_number: int, *, token: str) -> dict[str, Any]:
    _status, payload = _gh_json(f"/repos/{owner}/{repo}/pulls/{pr_number}", token=token)
    if not isinstance(payload, dict):
        raise SystemExit(
            f"Expected object payload for pull request #{pr_number}, got {type(payload).__name__}."
        )
    return payload


def _fetch_pull_files(
    owner: str,
    repo: str,
    pr_number: int,
    *,
    token: str,
) -> list[dict[str, Any]]:
    files = _gh_paginated_json(
        f"/repos/{owner}/{repo}/pulls/{pr_number}/files",
        token=token,
    )
    return [item for item in files if isinstance(item, dict)]


def _fetch_file_contents(
    owner: str,
    repo: str,
    path: str,
    *,
    ref: str,
    token: str,
) -> str | None:
    encoded_path = urllib.parse.quote(path, safe="/")
    status, payload = _gh_json(
        f"/repos/{owner}/{repo}/contents/{encoded_path}",
        token=token,
        params={"ref": ref},
        allow_http_error=True,
    )
    if status == 404:
        return None
    if not isinstance(payload, dict):
        return None
    content = str(payload.get("content") or "").strip()
    encoding = str(payload.get("encoding") or "").strip().lower()
    if not content or encoding != "base64":
        return None
    return base64.b64decode(content.encode("utf-8")).decode("utf-8").strip()


def _local_spec_entries_for_issue(workspace: Path, issue_number: int) -> list[dict[str, str]]:
    specs_root = workspace / "specs"
    if not specs_root.is_dir():
        return []

    candidates: list[Path] = []
    for path in sorted(specs_root.iterdir()):
        if not path.is_dir():
            continue
        name = path.name.lower()
        if (
            re.search(rf"(?:^|[-_])(?:issue[-_]?)?{issue_number}(?:$|[-_])", name)
            or name.endswith(str(issue_number))
            or name.startswith(f"github-{issue_number}")
            or name.startswith(f"gh{issue_number}")
            or name.startswith(f"gh-{issue_number}")
        ):
            candidates.append(path)

    entries: list[dict[str, str]] = []
    for directory in candidates:
        found_for_dir: dict[str, dict[str, str]] = {}
        for filename in SPEC_FILENAMES:
            file_path = directory / filename
            if not file_path.is_file():
                continue
            kind = "PRODUCT.md" if filename.lower().startswith("product") else "TECH.md"
            rel_path = str(file_path.relative_to(workspace))
            found_for_dir[kind] = {
                "path": rel_path,
                "content": file_path.read_text(encoding="utf-8").strip(),
            }
        for kind in ("PRODUCT.md", "TECH.md"):
            if kind in found_for_dir:
                entries.append(found_for_dir[kind])
    return entries


def _remote_spec_entries_for_issue(
    owner: str,
    repo: str,
    issue_number: int,
    *,
    ref: str,
    token: str,
) -> list[dict[str, str]]:
    status, payload = _gh_json(
        f"/repos/{owner}/{repo}/contents/specs",
        token=token,
        params={"ref": ref},
        allow_http_error=True,
    )
    if status == 404 or not isinstance(payload, list):
        return []

    entries: list[dict[str, str]] = []
    for item in payload:
        if not isinstance(item, dict) or item.get("type") != "dir":
            continue
        name = str(item.get("name") or "")
        lowered = name.lower()
        if not (
            re.search(rf"(?:^|[-_])(?:issue[-_]?)?{issue_number}(?:$|[-_])", lowered)
            or lowered.endswith(str(issue_number))
            or lowered.startswith(f"github-{issue_number}")
            or lowered.startswith(f"gh{issue_number}")
            or lowered.startswith(f"gh-{issue_number}")
        ):
            continue
        for filename in ("PRODUCT.md", "TECH.md"):
            path = f"specs/{name}/{filename}"
            content = _fetch_file_contents(owner, repo, path, ref=ref, token=token)
            if content:
                entries.append({"path": path, "content": content})
    return entries


def _local_spec_entries_from_changed_files(
    workspace: Path,
    changed_files: list[str],
) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    seen: set[str] = set()
    for filename in changed_files:
        if not re.search(r"(?i)^specs/.+/(product|tech)\.md$", filename):
            continue
        path = workspace / filename
        if not path.is_file() or filename in seen:
            continue
        seen.add(filename)
        entries.append(
            {
                "path": filename,
                "content": path.read_text(encoding="utf-8").strip(),
            }
        )
    return entries


def resolve_issue_number_for_pr(
    owner: str,
    repo: str,
    pr: dict[str, Any],
    changed_files: list[str],
    *,
    token: str | None,
) -> int | None:
    head_ref = str(((pr.get("head") or {}).get("ref")) or "")
    body = str(pr.get("body") or "")
    title = str(pr.get("title") or "")

    candidates = _dedupe_ints(
        _issue_numbers_from_branch(head_ref)
        + _issue_numbers_from_changed_files(changed_files)
        + _issue_numbers_from_text(f"{title}\n{body}")
    )

    linked: list[dict[str, Any]] = []
    if token:
        linked = _fetch_closing_issue_references(owner, repo, int(pr["number"]), token=token)
        linked.extend(
            _fetch_manual_linked_issue_references(owner, repo, int(pr["number"]), token=token)
        )
        candidates = _dedupe_ints(candidates + _same_repo_issue_numbers(owner, repo, linked))

    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        return None

    # Prefer the most specific sources: branch naming and linked issues over free text.
    preferred = _dedupe_ints(
        _issue_numbers_from_branch(head_ref) + _issue_numbers_from_changed_files(changed_files)
    )
    if token:
        preferred = _dedupe_ints(preferred + _same_repo_issue_numbers(owner, repo, linked))
    if len(preferred) == 1:
        return preferred[0]
    return None


def resolve_spec_context_for_pr(
    owner: str,
    repo: str,
    pr_number: int,
    *,
    workspace: Path,
    token: str | None,
) -> dict[str, Any]:
    if token is None:
        # Local-only fallback: inspect the checkout for specs related to the PR number
        # or any obvious issue-linked directories.
        changed_files: list[str] = []
        local_from_pr_number = _local_spec_entries_for_issue(workspace, pr_number)
        if local_from_pr_number:
            return {
                "issue_number": pr_number,
                "spec_context_source": "directory",
                "spec_entries": local_from_pr_number,
                "changed_files": changed_files,
            }
        return {
            "issue_number": None,
            "spec_context_source": "",
            "spec_entries": [],
            "changed_files": changed_files,
        }

    pr = _fetch_pull(owner, repo, pr_number, token=token)
    files = _fetch_pull_files(owner, repo, pr_number, token=token)
    changed_files = [str(file.get("filename") or "") for file in files]
    head_ref = str(((pr.get("head") or {}).get("ref")) or "HEAD")

    issue_number = resolve_issue_number_for_pr(
        owner,
        repo,
        pr,
        changed_files,
        token=token,
    )

    spec_entries: list[dict[str, str]] = []
    source = ""

    if issue_number is not None:
        local_entries = _local_spec_entries_for_issue(workspace, issue_number)
        if local_entries:
            spec_entries = local_entries
            source = "directory"
        else:
            remote_entries = _remote_spec_entries_for_issue(
                owner,
                repo,
                issue_number,
                ref=head_ref,
                token=token,
            )
            if remote_entries:
                spec_entries = remote_entries
                source = "directory"

    if not spec_entries:
        # Specs-only PRs may change PRODUCT.md/TECH.md directly.
        local_from_diff = _local_spec_entries_from_changed_files(workspace, changed_files)
        if local_from_diff:
            spec_entries = local_from_diff
            source = "directory"
        else:
            for filename in changed_files:
                if not re.search(r"(?i)^specs/.+/(product|tech)\.md$", filename):
                    continue
                content = _fetch_file_contents(
                    owner,
                    repo,
                    filename,
                    ref=head_ref,
                    token=token,
                )
                if content:
                    spec_entries.append({"path": filename, "content": content})
                    source = "directory"

    return {
        "issue_number": issue_number,
        "spec_context_source": source,
        "spec_entries": spec_entries,
        "changed_files": changed_files,
    }


def _format_spec_context(spec_context: dict[str, Any]) -> str:
    sections: list[str] = []
    source = str(spec_context.get("spec_context_source") or "")
    issue_number = spec_context.get("issue_number")
    if source == "directory" and issue_number:
        sections.append(
            f"Repository spec context was found in `specs/` for issue #{int(issue_number)}."
        )
    elif source == "directory":
        sections.append("Repository spec context was found in `specs/`.")
    for entry in spec_context.get("spec_entries") or []:
        if not isinstance(entry, dict):
            continue
        path = str(entry.get("path") or "").strip()
        content = str(entry.get("content") or "").strip()
        if not path or not content:
            continue
        sections.append(f"## {path}\n\n{content}")
    return "\n\n".join(sections).strip() or NO_SPEC_CONTEXT_MESSAGE


def _default_repo() -> str | None:
    return (os.environ.get("GITHUB_REPOSITORY") or "").strip() or None


def _default_pr_number() -> int | None:
    ref = (os.environ.get("GITHUB_REF") or "").strip()
    match = re.match(r"refs/pull/(\d+)/", ref)
    if match:
        return int(match.group(1))
    event_path = (os.environ.get("GITHUB_EVENT_PATH") or "").strip()
    if not event_path:
        return None
    try:
        event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    for key in ("pull_request", "issue"):
        number = ((event.get(key) or {}) if isinstance(event, dict) else {}).get("number")
        if isinstance(number, int):
            return number
    return None


def main() -> None:
    args = _parse_args()
    repo_slug = args.repo or _default_repo()
    pr_number = args.pr or _default_pr_number()
    if not repo_slug or "/" not in repo_slug:
        raise SystemExit(
            "Repository slug is required as --repo OWNER/REPO or GITHUB_REPOSITORY."
        )
    if not pr_number:
        raise SystemExit("Pull request number is required as --pr N or from GitHub Actions context.")

    owner, repo = repo_slug.split("/", 1)
    spec_context = resolve_spec_context_for_pr(
        owner,
        repo,
        pr_number,
        workspace=args.workspace,
        token=_resolve_token(),
    )
    rendered = _format_spec_context(spec_context)
    if args.output is not None:
        args.output.write_text(rendered + "\n", encoding="utf-8")
        print(f"wrote spec context to {args.output}")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
