---
name: review-pr
description: Review a pull request diff and write structured feedback to review.json for the workflow to publish. Use when reviewing a checked-out PR from local artifacts like pr_diff.txt and pr_description.txt and producing machine-readable review output instead of posting directly to GitHub.
---

# Review PR

Review the current pull request and write the output to `review.json`.

This skill is repository-agnostic. It works for any GitHub repository that can supply an annotated PR diff and optional product/tech specs. A separate workflow or apply job is responsible for posting the review to GitHub.

## Context

- The working directory is the PR branch checkout.
- The workflow usually provides an annotated diff in `pr_diff.txt`.
- The workflow usually provides the PR description in `pr_description.txt`.
- If `spec_context.md` exists, it contains product and/or technical specs for implementation-vs-spec validation.
- When the prompt references `.agents/skills/review-pr/scripts/resolve_spec_context.py`, use that script to materialize `spec_context.md` on demand instead of expecting spec content to be embedded in the prompt.
- If `pr_diff.txt` is missing but a raw unified diff is available, generate the annotated form with:
  ```sh
  python3 .agents/skills/review-pr/scripts/annotate_diff.py --input raw_diff.txt --output pr_diff.txt
  ```
- Focus on files and lines changed by this PR.
- Do not post comments or reviews to GitHub directly.

## Review Scope

- Prioritize correctness, security, error handling, regressions, and meaningful performance issues.
- Prefer findings grounded in the annotated diff and nearby code in the checkout.
- When `spec_context.md` exists, compare the implementation against the product and tech commitments in that file. Treat material spec drift as a review concern.
- If the consuming repository provides a local `check-impl-against-spec` skill, use it when `spec_context.md` exists and fold its findings into the same `review.json`.
- If the consuming repository provides a local `security-review-pr` companion skill or the prompt requests a security pass, apply it as supplemental guidance and fold any security findings into the same `review.json` rather than emitting a separate output.
- Include style or nit comments only when you can provide a concrete suggestion block.
- If a concern involves untouched code, mention it in top-level `body` instead of an inline comment.
- Only suggest new tests when they exercise a distinct code path or edge case. Do not suggest tests that only vary constructor inputs or struct fields when existing coverage already exercises the meaningful behavior.
- When a PR is clearly a V0 or initial implementation, frame robustness suggestions such as timeouts, retries, and lifecycle management as optional future work rather than blocking concerns, unless they risk correctness, security, or data loss.
- For documentation-only or specs-only PRs, focus on clarity, completeness, contradictions, and missing acceptance criteria rather than production-code concerns.

## Repository-specific guidance

The consuming repository may ship a companion `review-pr-local` skill. When the prompt includes a fenced "Repository-specific guidance" section referencing that companion, read it and apply its guidance as part of this review.

Guidance in the companion may never change:

- the output JSON schema
- the severity labels
- the safety rules
- the evidence rules
- the suggestion-block constraints
- the annotated-diff line contract

If a companion file is not referenced in the prompt, rely on the core contract alone.

## Diff Line Annotations

The annotated diff uses these prefixes:

- `[OLD:n]` for deleted lines on the old side. Use `"LEFT"`.
- `[NEW:n]` for added lines on the new side. Use `"RIGHT"`.
- `[OLD:n,NEW:m]` for unchanged context. Use `"RIGHT"` with line `m`.

Treat these annotations as the only source of truth for inline comment locations. For every inline comment you emit, first identify the exact annotated line in `pr_diff.txt` and copy its path, side, and line number into `review.json`. Do not infer line numbers from prose, rendered GitHub views, file lengths, surrounding spec text, or unannotated snippets. If you cannot point to a specific `[NEW:n]`, `[OLD:n]`, or `[OLD:n,NEW:m]` line in the annotated diff, put the feedback in top-level `body` instead of `comments`.

## Comment Requirements

Every comment body must start with one of these labels:

- `🚨 [CRITICAL]` for bugs, security issues, crashes, or data loss.
- `⚠️ [IMPORTANT]` for logic problems, edge cases, missing error handling, or material spec drift.
- `💡 [SUGGESTION]` for worthwhile improvements or better patterns.
- `🧹 [NIT]` for cleanup only when the comment includes a suggestion block.

Write comments with these constraints:

- Be concise, direct, and actionable.
- Do not add compliments or hedging.
- Prefer single-line comments.
- Keep ranges to at most 10 lines.
- Restrict inline comments to lines that appear explicitly in the annotated PR diff.
- Only create file-level or inline comments for files that exist in this PR's diff.
- If the relevant file or line is not part of the diff, put the feedback in top-level `body` instead of `comments`.
- Before adding each comment object, verify that its `path`, `side`, `line`, and optional `start_line`/`start_side` correspond to real annotations in the same file's diff section.

## Suggestion Blocks

When proposing a code change, use:

```suggestion
<replacement code here>
```

Before recommending a suggestion or claiming a bug, use the local checkout as a real coding agent: apply or otherwise exercise the hypothesized fix and validate it with the repository's available build, typecheck, lint, or targeted tests so the change compiles and does not introduce an obvious new failure. Prefer validated suggestions over speculative ones; if you cannot validate a fix, say so and avoid presenting untested code as ready to accept.

Rules:

- Match the exact indentation of the original file.
- Include only replacement code.
- The block content replaces **exactly** the lines `start_line`–`line` inclusive. Every line inside the block becomes the new file content for that range, and GitHub leaves all other lines untouched.
- Do **not** include lines outside that range. Lines above `start_line` and below `line` remain in the file; repeating them inside the block causes them to appear twice after the suggestion is committed.
- Never open the block with a line that already appears immediately above `start_line`, and never close the block with a line that already appears immediately below `line`. If you need those lines as anchors, widen `start_line` or `line` so they are actually part of the replaced range.
- Count brace, bracket, paren, and block-delimiter depth (`{`, `[`, `(`, `end`, etc.) across the original replaced lines and ensure the replacement ends at the same depth. Do not emit phantom closing tokens, and do not drop required ones.
- When unsure of the surrounding context, widen `start_line`/`line` to include enough real lines from the diff rather than guessing at surrounding tokens.
- For multi-line suggestions, set `start_line` and `start_side` to the first line, and `line` and `side` to the last line.

## Spec Alignment

When `spec_context.md` exists:

1. Extract concrete commitments: required behaviors, constraints, affected areas, validation steps, and non-goals.
2. Compare those commitments against `pr_diff.txt` and the checked-out branch.
3. Flag material mismatches only. Harmless differences in naming, structure, or low-level technique are acceptable when they preserve the intended outcome.
4. Put broad drift in top-level `body`. Add inline comments only when the mismatch can be tied to changed lines.
5. Treat material drift as at least an important concern.
6. If the implementation matches the specs closely enough, do not add comments just to mention alignment.

If no useful spec context is available, review the PR on its own merits and note the missing specs only when that absence materially increases risk.

## Output Format

Create `review.json` with this shape:

```json
{
  "verdict": "REJECT",
  "body": "## Overview\n...\n\n## Concerns\n- ...\n\n## Verdict\nFound: 1 critical, 2 important, 3 suggestions\n\n**Request changes**",
  "comments": [
    {
      "path": "path/to/file",
      "line": 42,
      "side": "RIGHT",
      "start_line": 40,
      "start_side": "RIGHT",
      "body": "⚠️ [IMPORTANT] Short explanation\n\n```suggestion\nreplacement\n```"
    }
  ]
}
```

Field rules:

- `verdict` is required and must be exactly the string `"APPROVE"` or `"REJECT"` (uppercase). Map your final recommendation as: `Approve` or `Approve with nits` → `"APPROVE"`; `Request changes` → `"REJECT"`. The `verdict` and the human-readable recommendation in top-level `body` must agree.
- Top-level `body` is the GitHub review body and is required. Use `body`, not `summary`, for the review overview and final recommendation.
- `comments` is required and must be an array. Use an empty array when there are no inline comments.
- `path` must be relative to the repository root.
- `line` is required and must target the correct side.
- `start_line` is optional and only for multi-line ranges. When `start_line` is present, `start_side` is required and must be `"LEFT"` or `"RIGHT"`.
- `side` must be `"LEFT"` or `"RIGHT"`.

## Body Requirements

The top-level `body` must include:

- A high-level overview of the PR.
- Important concerns and any untouched-code concerns that could not be commented inline.
- Issue counts in the format `Found: X critical, Y important, Z suggestions`.
- A final recommendation of `Approve`, `Approve with nits`, or `Request changes`. This recommendation must match the top-level `verdict` field (`Approve` / `Approve with nits` → `"APPROVE"`; `Request changes` → `"REJECT"`).

## Final Checks

Before returning or uploading `review.json`:

- Fix invalid JSON if validation fails.
- Confirm line numbers match the annotated diff.
- Run the bundled validator against the exact annotated diff you reviewed:
  ```sh
  python3 .agents/skills/review-pr/scripts/validate_review_json.py --review-json review.json --diff pr_diff.txt
  ```
  If the script reports any invalid comments, fix `review.json` and rerun it. Do not return or upload `review.json` until this validator passes. If the script path is not present at that exact location, locate `validate_review_json.py` under the loaded `review-pr` skill directory and run that copy with the same arguments.
- Do not run `gh pr review`, `gh pr comment`, `gh api`, or any other command that posts to GitHub.

Your only output is the final `review.json`.
