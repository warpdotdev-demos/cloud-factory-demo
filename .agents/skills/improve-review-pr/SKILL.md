---
name: improve-review-pr
description: Daily outer loop that reviews human reactions to automated review-pr comments, synthesizes durable organizational knowledge, and opens a PR to update the review-pr skill when the feedback is worth remembering. Use when improving code-review quality from human feedback, running a scheduled review-skill retrospective, or incorporating maintainer corrections into review guidance.
---

# Improve Review PR

Run a once-per-day outer loop over the automated code-review stage.

The inner loop is already running: `review-pr` comments on pull requests throughout the day. This skill is the outer loop: read how humans reacted to those comments, extract durable organizational knowledge, and update the review skill so the next inner-loop runs get better.

## Goal

Improve future automated reviews by learning from human validation and correction of previous `review-pr` comments.

Do not re-review product code. Do not restate one-off PR opinions. Only capture knowledge that should change how the review agent behaves on future PRs.

## Inputs

- The current checkout of the repository that owns `.agents/skills/review-pr/SKILL.md`
- GitHub API access via authenticated `gh`
- Optional lookback window, default last 24 hours
- Optional `feedback_corpus.json` produced by:
  ```sh
  python3 .agents/skills/improve-review-pr/scripts/collect_review_feedback.py \
    --repo OWNER/REPO \
    --since-hours 24 \
    --output feedback_corpus.json
  ```

If `feedback_corpus.json` is missing, run the collector yourself before analyzing.

## Workflow

### 1. Collect the day's review-agent interactions

Run or read `feedback_corpus.json`.

The corpus should include, for the lookback window:

- Pull requests that received an automated review from the review agent
- The review agent's top-level review bodies and inline comments
- Human replies to those comments
- Human reactions (for example `+1`, `eyes`, `confused`, `thumbs down`) when available
- Whether the human accepted a suggestion, dismissed it, edited around it, or explicitly disagreed
- Whether the PR author or another reviewer later fixed the same issue, ignored it, or called it wrong

Identify the review agent by login when possible (`github-actions[bot]`, a bot account, or a configured login). Prefer comments that originated from the `review-pr` publish path.

### 2. Score each feedback item

For each human interaction, classify the outcome:

- `validated` — human agreed, accepted the suggestion, or fixed the issue as recommended
- `corrected` — human said the finding was wrong, incomplete, too noisy, or the wrong severity
- `refined` — human mostly agreed but adjusted the guidance, scope, or preferred pattern
- `ambiguous` — not enough signal to learn from

Ignore pure acknowledgements with no substantive judgment.

### 3. Synthesize durable organizational knowledge

Look across the day's validated/corrected/refined items for patterns worth remembering. Good candidates:

- Repo conventions the review agent repeatedly misses
- False-positive classes that should be demoted or avoided
- Severity calibration mistakes
- Preferred alternatives to common suggestions
- Missing checks that humans keep adding manually
- Guidance about when not to comment

Reject learnings that are:

- One-off to a single PR or file
- Already covered well by `review-pr` or a local companion skill
- Product-feature preferences unrelated to review quality
- Temporary project constraints unlikely to recur
- Changes that would break the review-pr output schema, severity labels, safety rules, evidence rules, suggestion-block constraints, or annotated-diff line contract

Prefer a small number of high-confidence learnings over many weak ones.

### 4. Decide whether to update the skill

Choose exactly one outcome:

- `no_changes` — no durable learning worth encoding
- `update_review_pr` — update core `.agents/skills/review-pr/SKILL.md`
- `update_review_pr_local` — update or create `.agents/skills/review-pr-local/SKILL.md` for repository-specific guidance
- `both` — core and local updates are both warranted

Use `review-pr-local` for repository-specific conventions. Keep portable review behavior in core `review-pr`.

If no durable learning exists, stop after writing the synthesis report. Do not open an empty PR.

### 5. Apply skill updates carefully

When updating a skill:

1. Read the current skill file completely.
2. Make the smallest cohesive edit that captures the learning.
3. Prefer adding or tightening guidance over rewriting large sections.
4. Keep the existing structure, severity labels, JSON contract, and safety rules intact.
5. Write guidance as durable rules or examples, not as a diary of today's PRs.
6. If creating `review-pr-local`, make it a companion that specializes overridable review guidance only. Explicitly state that it must not change the core output schema or contracts.

Validate that the resulting skill still clearly instructs the agent to:

- write only `review.json`
- avoid posting to GitHub directly
- keep suggestion blocks valid
- validate hypothesized fixes before recommending them when practical

### 6. Open a skill-improvement PR when there are changes

If you updated any skill file:

1. Create a branch such as `improve/review-pr-YYYY-MM-DD`
2. Commit only the skill updates and any tiny supporting docs needed to explain them
3. Include `Co-Authored-By: Oz <oz-agent@warp.dev>` in the commit message
4. Push and open a PR against the repository default branch
5. In the PR body, include:
   - Summary of the human-feedback patterns observed
   - Exact learnings encoded
   - Why each learning is durable
   - Links to representative source PRs/comments
   - Explicit non-goals / rejected candidates
   - Note that this PR only updates review guidance, not product code

Do not merge the PR. Leave it for human review.

### 7. Report the result

Return a concise report with:

```markdown
## Improve review-pr result
- **Window:** last N hours
- **PRs inspected:** count
- **Feedback items:** count validated / corrected / refined / ambiguous
- **Decision:** no_changes | update_review_pr | update_review_pr_local | both
- **Learnings encoded:** bullet list, or "none"
- **Skill PR:** URL or "not opened"
- **Next step:** one concrete action for humans
```

If a skill PR was opened, the report must include its URL.

## Guardrails

- Do not update product code, tests, or unrelated skills.
- Do not change the review-pr JSON schema, severity labels, safety rules, evidence rules, suggestion-block constraints, or annotated-diff line contract.
- Do not open a PR for weak, one-off, or already-encoded feedback.
- Do not invent human feedback that is not present in the corpus.
- Do not expose secrets, tokens, private environment variables, or internal reasoning dumps.
- Prefer local companion guidance for repo-specific conventions; keep core `review-pr` portable.
- Keep the skill update small enough for a human to review quickly.
