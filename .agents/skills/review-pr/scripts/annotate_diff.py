#!/usr/bin/env python3
"""Annotate a unified git/GitHub patch with review line markers.

The review-pr skill and validator expect lines like:

  [OLD:12] removed line
  [NEW:34] added line
  [OLD:12,NEW:34] context line

This script converts a normal unified diff into that form so any
repository can prepare `pr_diff.txt` without host-specific tooling.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


HUNK_HEADER_PATTERN = re.compile(
    r"^@@ -(?P<old_start>\d+)(?:,(?P<old_count>\d+))? "
    r"\+(?P<new_start>\d+)(?:,(?P<new_count>\d+))? @@"
)


def annotate_patch(patch: str) -> str:
    lines: list[str] = []
    old_line: int | None = None
    new_line: int | None = None

    for raw_line in patch.splitlines():
        # Full multi-file `git diff` output starts each file with `diff --git`.
        # Reset hunk counters there so later `---` / `+++` headers pass through
        # the not-in-hunk branch instead of being treated as deleted/added lines.
        # Do not special-case `---` / `+++` themselves: a deleted content line
        # whose text begins with `-- ` is also written as `--- ...` in unified
        # diffs and must still be annotated as hunk content when inside a hunk.
        if raw_line.startswith("diff --git ") or raw_line.startswith("Binary files "):
            old_line = None
            new_line = None
            lines.append(raw_line)
            continue

        header_match = HUNK_HEADER_PATTERN.match(raw_line)
        if header_match:
            old_line = int(header_match.group("old_start"))
            new_line = int(header_match.group("new_start"))
            lines.append(raw_line)
            continue
        if old_line is None or new_line is None or raw_line.startswith("\\"):
            lines.append(raw_line)
            continue

        marker = raw_line[:1]
        text = raw_line[1:]
        if marker == "-":
            lines.append(f"[OLD:{old_line}] {text}")
            old_line += 1
        elif marker == "+":
            lines.append(f"[NEW:{new_line}] {text}")
            new_line += 1
        elif marker == " ":
            lines.append(f"[OLD:{old_line},NEW:{new_line}] {text}")
            old_line += 1
            new_line += 1
        else:
            lines.append(raw_line)

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Annotate a unified diff for review-pr comment placement."
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Path to a unified diff. Reads stdin when omitted.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Path to write the annotated diff. Writes stdout when omitted.",
    )
    args = parser.parse_args()

    if args.input is None:
        patch = sys.stdin.read()
    else:
        try:
            patch = args.input.read_text(encoding="utf-8")
        except FileNotFoundError:
            print(f"annotate_diff failed: {args.input} does not exist", file=sys.stderr)
            return 1

    annotated = annotate_patch(patch)
    if not annotated.endswith("\n"):
        annotated += "\n"

    if args.output is None:
        sys.stdout.write(annotated)
    else:
        args.output.write_text(annotated, encoding="utf-8")
        print(f"wrote annotated diff to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
