---
name: spec
description: Write a product and technical specification for a GitHub, Jira, Linear, or other issue-tracker issue that has been marked ready-to-spec, using issue context, roadmap and vision documents, and the current codebase.
---

# Spec

Write a product and technical specification for the issue passed in the user's prompt. Do not implement the issue.

Expect the prompt to contain a link, key, or number for exactly one issue in an issue tracker. Use tracker context, roadmap and vision documents, and the current checkout to turn the request into an implementation-ready spec.

## Workflow

### 1. Identify the issue and repository

Extract the issue URL, key, or number from the prompt. Determine whether it belongs to GitHub Issues, Jira, Linear, or another tracker.

Confirm the current checkout is the repository where the future implementation should happen. If the prompt does not identify one issue unambiguously, ask for clarification before writing a spec.

### 2. Post a spec-started status comment

For GitHub Issues, post a short status comment before doing spec work so issue subscribers know an agent has started.

Use the authenticated `gh` CLI when available. Include:

- That automated Oz spec work has started.
- The issue identifier being specified.
- A follow-along link to the Oz run or Oz session.

Use an Oz run URL or Oz session URL from the agent runtime, action output, environment, or logs. Do not use a GitHub Actions workflow URL as the follow-along link. If no Oz run or session link is available yet, say that the Oz follow-along link is not available yet rather than substituting another URL, and continue spec work.

Keep this comment concise.

### 3. Fetch tracker context

Use the best available integration in this order:

1. A relevant MCP server or native tracker tool
2. The tracker's authenticated CLI, such as `gh`
3. The tracker's API or web page

Fetch:

- Full issue title and description
- Comments and discussion
- Existing labels, status, assignee, project, and linked issues
- Attachments, screenshots, logs, reproduction steps, examples, and acceptance criteria
- Related open issues, likely duplicates, dependencies, and nearby product work

Do not write a spec solely from the issue title. Do not expose credentials or secrets while fetching tracker data.

If tracker context is missing critical product intent, post a concise blocker comment with the specific missing information and stop instead of inventing requirements.

### 4. Inspect roadmap, vision, and codebase context

Read `roadmap.md` and `vision.md` at the repository root if they exist. Use them to confirm the issue fits the stated product direction and to choose constraints or non-goals for the spec.

Search and read the codebase to understand the affected feature, behavior, terminology, and likely implementation area.

Assess:

- Current behavior and user-facing flows
- Likely files, services, UI components, APIs, tests, and data flows involved
- Existing patterns and abstractions to preserve
- Product decisions that need human review
- Technical decisions, edge cases, migrations, compatibility risks, and validation requirements
- Whether related open issues or active work affect the proposed scope

Post a brief progress comment if this investigation reveals a materially useful implementation area or major decision point. Do not post internal reasoning, speculative details, secrets, or raw command output.

### 5. Write the spec

Write a concise but implementation-ready spec. Prefer clarity over length. Include enough detail for a separate implementation agent to build the change without re-litigating product decisions.

Use this structure:

## Spec: ISSUE_TITLE

### Problem

Describe the user problem and why it matters.

### Goals

List the concrete outcomes this change should achieve.

### Non-goals

List related work that should not be included in the implementation.

### Product behavior

Describe the expected user-facing behavior, including important states, edge cases, and acceptance criteria.

### Technical approach

Describe the recommended implementation approach and the code areas likely involved. Include alternatives considered when there are meaningful tradeoffs.

### Validation plan

List the tests, build commands, manual checks, or rollout checks that should validate the implementation.

### Open questions

List only questions that still need human input. If there are no material open questions, write "None."

### Implementation readiness

State whether the issue is ready for implementation after this spec, and if so which label should be applied next.

### Source context

List the issue, linked discussion, roadmap or vision files, and important code paths used to write the spec.

### 6. Publish the spec

For GitHub Issues, post the spec as a comment on the original issue using `gh issue comment`.

If the spec has no material open questions and is ready for implementation, apply the matching implementation-readiness label if available, such as `Ready to implement` or `ready-to-implement`, and remove `Ready to spec` or equivalent labels. Preserve unrelated labels.

If the spec still has material open questions, apply or keep a `Needs info` label if available, and explain the questions in the spec. Do not apply `Ready to implement` until those questions are answered.

If permissions prevent commenting or updating labels, report the completed spec and the intended label change in the final response with the permission error.

### 7. Report the result

Keep the final response concise and include:

- Issue identifier and title
- Where the spec was posted
- Whether the issue is ready to implement
- Exact label changes made or intended
- Direct link to the issue

Use this format:

## Spec result
- **Issue:** [identifier and title](URL)
- **Spec posted:** URL or location
- **Implementation readiness:** `ready` or `blocked`
- **Label changes:** concise description
- **Next step:** One concrete action

## Guardrails

- Do not implement the issue during spec work.
- Do not close, assign, reprioritize, or otherwise mutate the issue unless the user asks.
- Do not overwrite unrelated labels.
- Do not claim a spec is implementation-ready if material product or technical decisions remain unresolved.
- Do not post raw secrets, tokens, private environment variables, command output dumps, or internal reasoning in status comments or specs.
- Post progress sparingly: always post the spec-started comment, then post at most two additional progress comments before the final spec unless blocked or explicitly asked for more updates.
