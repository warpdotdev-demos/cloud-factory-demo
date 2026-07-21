---
name: implementation
description: Implement a fix or feature from a GitHub, Jira, Linear, or other issue-tracker issue by fetching issue context, inspecting the current codebase, making code changes, validating them, optionally verifying visible behavior with the verify-behavior computer-use skill, opening a GitHub pull request, and reporting progress back to the original issue.
---

# Implementation

Implement the issue passed in the user's prompt and open a GitHub pull request with the fix or feature.

Expect the prompt to contain a link, key, or number for exactly one issue in an issue tracker. Use tracker context and the current checkout to understand the requested behavior before changing code.

## Workflow

### 1. Identify the issue and repository

Extract the issue URL, key, or number from the prompt. Determine whether it belongs to GitHub Issues, Jira, Linear, or another tracker.

Confirm the current checkout is the repository where the implementation should happen. If the prompt does not identify one issue unambiguously, ask for clarification before making changes.

### 2. Verify optional helper skills

If the checkout contains `.agents/skills/validate-changes-match-specs/SKILL.md`, use it after implementation whenever `PRODUCT.md` and `TECH.md` specs exist for the issue.

If specs exist but the validation skill is missing, continue only if you can still manually compare the implementation against the specs. Report that the common validation skill was unavailable in the PR description and issue comment.

If the checkout contains `.agents/skills/verify-behavior/SKILL.md`, use it as a cloud computer-use **subagent** when the issue has visible UI or interactive behavior worth proving. Prefer that skill over driving the GUI yourself.

### 3. Post an implementation-started status comment

For GitHub Issues, post a short status comment before doing implementation work so issue subscribers know an agent has started.

Use the authenticated `gh` CLI when available. Include:

- That automated Oz implementation has started.
- The issue identifier being implemented.
- A follow-along link to the Oz run (see **Oz run URLs** below).

Keep this comment concise.

### Oz run URLs

When posting any follow-along, evidence, or status link to an Oz cloud run, use the **Oz web app** URL — never invent links from the API host.

Correct format:

```text
https://oz.warp.dev/runs/<run-id>
```

On staging / WarpDev, use:

```text
https://oz.staging.warp.dev/runs/<run-id>
```

Rules:

- Path is **`/runs/`** (plural), never `/run/`.
- Host is **`oz.warp.dev`** (or `oz.staging.warp.dev`), never `app.warp.dev` or `app.staging.warp.dev`.
- Prefer a full run URL already provided by the runtime, action output, dispatcher, or logs. If you only have a run id, build the URL with the format above.
- If you see `https://app.warp.dev/run/<id>` or `https://app.warp.dev/runs/<id>`, rewrite it to `https://oz.warp.dev/runs/<id>` before posting.
- Do not use a GitHub Actions workflow run URL as the Oz follow-along link.
- If no Oz run id or link is available yet, say the Oz follow-along link is not available yet rather than substituting another URL, and continue implementation.

### 4. Fetch tracker context

Use the best available integration in this order:

1. A relevant MCP server or native tracker tool
2. The tracker's authenticated CLI, such as `gh`
3. The tracker's API or web page

Fetch:

- Full issue title and description
- Comments and discussion
- Links to spec pull requests or checked-in `PRODUCT.md` and `TECH.md` files
- Existing labels, status, assignee, project, and linked issues
- Attachments, screenshots, logs, reproduction steps, and acceptance criteria
- Related open issues, likely duplicates, dependencies, and nearby product work

Do not implement solely from the issue title. Do not expose credentials or secrets while fetching tracker data.

If tracker context is missing critical implementation details, post a concise blocker comment with the specific missing information and stop instead of guessing.

### 5. Locate and read specs first

Before inspecting implementation areas, search for specs related to the issue.

Look for:

- Links to spec pull requests in the issue description or comments
- Checked-in files under `specs/<issue-slug>/PRODUCT.md` and `specs/<issue-slug>/TECH.md`
- Nearby `PRODUCT.md` and `TECH.md` files whose path or contents reference the issue

If both `PRODUCT.md` and `TECH.md` exist:

- Read both specs completely before making code changes.
- Treat the specs as the primary source of product behavior, acceptance criteria, technical direction, non-goals, and validation requirements.
- Check newer issue comments for corrections or decisions that supersede the specs.
- If the specs conflict with the issue or with each other, stop and post a concise blocker comment instead of guessing.

If only one of `PRODUCT.md` or `TECH.md` exists, read the available spec and decide whether the missing spec is a blocker. For broad or risky work, stop and ask for the missing spec.

If no specs exist, continue from the issue context and codebase inspection.

### 6. Inspect the current codebase

Search and read the codebase to understand the affected feature, behavior, terminology, and likely implementation area.

Assess:

- Whether the described behavior exists today
- Whether the requested behavior is already captured in `PRODUCT.md` and `TECH.md`
- Likely files, services, UI components, APIs, tests, and data flows involved
- Existing patterns and abstractions to follow
- Edge cases, migrations, platform differences, or compatibility risks
- Validation commands used by the repository

Post a brief progress comment if this investigation reveals a materially useful implementation area, for example: "I found the relevant editor state flow in `src/...` and am implementing the change there." Do not post internal reasoning, speculative details, secrets, or raw command output. Do not describe the implementation as complete until a pull request has been opened and you can include the PR URL.

### 7. Implement the change

Make the smallest cohesive change that satisfies the issue.

Follow existing code style and architecture. Update tests, fixtures, docs, or configuration when they are part of the expected behavior. Do not bundle unrelated refactors, formatting churn, dependency upgrades, or opportunistic cleanup into the PR.

If the issue turns out to be much larger or more ambiguous than expected, stop and comment with a concise recommendation rather than producing a risky partial implementation.

### 8. Validate the implementation

Run the most relevant validation commands for the repository. Prefer commands documented in README, package scripts, CI config, Makefiles, or existing workflow files.

At minimum, attempt:

- Targeted tests for the changed behavior, if available
- Linting or typechecking, if available
- A build or equivalent compile check, if appropriate

If a validation command fails, investigate and fix failures caused by your changes. If failures appear unrelated or require external services, report them clearly in the PR and issue comment with enough detail for a reviewer to reproduce.

If `PRODUCT.md` and `TECH.md` specs exist for the issue, validate the completed implementation against them before opening the PR:

1. Read `.agents/skills/validate-changes-match-specs/SKILL.md`.
2. Follow that skill to compare the implementation diff against the relevant specs.
3. Fix any material mismatch caused by your implementation.
4. If a mismatch reflects stale or incorrect specs rather than implementation drift, report it clearly and do not claim full spec alignment.

Include the spec-alignment result in the PR description and final issue comment.

### 9. Verify visible behavior with verify-behavior

When the change affects UI, browser, desktop, or other interactive behavior, and `.agents/skills/verify-behavior/SKILL.md` is present:

1. Read that skill and follow its parent workflow in `verify` mode. This covers greenfield features and bug fixes alike.
2. If `PRODUCT.md` exists for the issue, pass its path and treat it as the source of user stories and acceptance criteria verification must exercise.
3. For multi-story features, expect `verify-behavior` to **fan out parallel computer-use (or isolated browser) subagents per key user story** via orchestration, then aggregate results. Do not require a single serial walkthrough when stories are independent.
4. Launch verification against the implementation branch (or the commit about to be pushed).
5. Prefer **video** of each critical path; add screenshots for keyframes or static visual checks.
6. If verification fails because of your change, fix the implementation and re-run verification when practical before opening the PR.
7. If verification is blocked (missing display, secrets, flaky environment), record the blocker and continue with automated tests plus an explicit verification gap in the PR.

Skip this step for non-visual changes, when the skill is missing, or when the repository has no runnable UI in the available environment. Do not claim end-to-end behavioral verification unless verify-behavior ran or you captured equivalent evidence.

### 10. Create a branch and pull request

Create a descriptive branch for the implementation, such as `fix/issue-123-short-title` or `feature/issue-123-short-title`.

Commit only the intended changes. Use a clear commit message. When committing, include:

`Co-Authored-By: Oz <oz-agent@warp.dev>`

Push the branch and open a GitHub pull request against the repository's default branch using the authenticated `gh` CLI. Capture the PR URL returned by `gh pr create`; this URL is required before posting final success back to the issue.

The PR description should include:

- A direct link to the original issue
- Links to `PRODUCT.md` and `TECH.md`, if used
- Summary of the change
- Validation commands run and their results
- Spec-alignment validation results, if specs exist
- Behavior verification results from `verify-behavior` when it ran, including status, Oz run link, and video/screenshot evidence references
- Known limitations, follow-up work, or validation gaps

Associate the PR with the issue in GitHub:

- If the implementation fully resolves the issue, include a closing keyword in the PR body, such as `Closes #123` or `Fixes #123`.
- If the implementation only partially addresses the issue, include a non-closing reference, such as `Related to #123`, and explain the remaining work.

After creating the PR, verify that you have a real PR URL. If `gh pr create` fails, do not post a success comment. Instead, fix the failure if possible, or post a blocker comment explaining that the implementation branch exists but PR creation failed.

### 11. Post the PR link and final status to the issue

Only after opening the PR, post a final comment on the original issue with:

- Link to the PR
- Brief summary of what was implemented
- Validation performed
- Spec-alignment validation result, if specs exist
- Behavior verification summary and evidence links, if `verify-behavior` ran
- Any known limitations or reviewer notes

The final issue comment must include the PR URL. A comment that says implementation is complete or that a PR will be opened later is not acceptable.

If no PR was created, post why implementation did not proceed and what concrete next step is needed. Do not describe this as a successful implementation.

## Guardrails

- Do not implement without fetching tracker context and inspecting the codebase.
- Do not expose secrets, tokens, private environment variables, raw logs containing credentials, or internal reasoning in issue comments or PR descriptions.
- Do not close, assign, reprioritize, or relabel the issue unless explicitly requested.
- Do not overwrite unrelated labels or metadata.
- Do not make unrelated code changes.
- Do not ignore `PRODUCT.md` or `TECH.md` when they exist for the issue.
- Do not claim validation passed if it was not run or failed.
- Do not claim spec alignment if `validate-changes-match-specs` was not run or an equivalent manual comparison was not performed.
- Do not claim interactive behavior was verified unless `verify-behavior` (or equivalent computer-use evidence) was collected.
- Do not post a final success comment unless a pull request has already been opened and the comment includes the PR URL.
- Post progress sparingly: always post the implementation-started comment, then post at most two additional progress comments before the final PR link unless blocked or explicitly asked for more updates.
