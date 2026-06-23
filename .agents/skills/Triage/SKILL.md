---
name: Triage
description: Triage an incoming GitHub, Jira, Linear, or other issue-tracker issue against the current codebase and related open issues, then apply exactly one implementation-readiness label. Use whenever the user asks to triage, classify, assess, prioritize, or label an issue for implementation readiness, especially when an issue URL, key, or number is supplied in the prompt.
---

# Triage

Assess the issue passed in the user's prompt and mark it with exactly one implementation-readiness state:

- `Ready to implement`
- `Ready to spec`
- `Needs info`
- `Wait to implement`

The goal is to route work honestly, not to make every issue appear actionable. Base the decision on evidence from the issue tracker, current checkout, and related open issues.

## Workflow

### 1. Identify the issue and tracker

Extract the issue URL, key, or number from the prompt. Determine whether it belongs to GitHub Issues, Jira, Linear, or another tracker.

If the prompt does not identify one issue unambiguously, ask the user for the issue rather than guessing.

### 2. Post a triage-started status comment

For GitHub Issues, post a short status comment before doing deeper work so issue subscribers know triage is in progress.

Use the authenticated `gh` CLI when available. Include:

- That automated Oz triage has started.
- The implementation-readiness states being evaluated.
- A follow-along link to the Oz run or Oz session.

Use an Oz run URL or Oz session URL from the agent runtime, action output, environment, or logs. Do not use a GitHub Actions workflow URL as the follow-along link. If no Oz run or session link is available yet, say that the Oz follow-along link is not available yet rather than substituting another URL, and continue triage.

Keep this comment concise. Example:

> Oz triage is running now and will classify this issue as exactly one of: `Ready to implement`, `Ready to spec`, `Needs info`, or `Wait to implement`.
>
> Follow along in Oz: LINK

### 3. Fetch tracker context

Use the best available integration in this order:

1. A relevant MCP server or native tracker tool
2. The tracker's authenticated CLI, such as `gh`
3. The tracker's API or web page

Fetch:

- Full issue title and description
- Comments and discussion
- Existing labels, status, assignee, project, and linked issues
- Attachments or screenshots when they materially affect understanding
- The tracker's available labels
- Related open issues, including likely duplicates, dependencies, and nearby product work

Do not classify solely from the title. Do not expose credentials or secrets while fetching tracker data.

After fetching the issue description, comments, labels, and related open issues, post a brief progress comment only if this step reveals that triage may take longer than expected or needs to inspect a broader part of the codebase. Avoid noisy updates for fast, routine issues.

### 4. Inspect the current codebase

Confirm the current checkout is the relevant repository. Search the codebase for the affected feature, behavior, terminology, and likely implementation area.

Assess:

- Whether the described behavior exists today
- Likely files, services, and systems involved
- Whether the issue has a bounded implementation path
- Dependencies, migrations, platform differences, and testing requirements
- Existing abstractions that make the change cohesive or indicate it does not fit
- Whether related open issues or active work change the recommendation

Prefer targeted searches and reads. This is triage, not implementation: do not edit product code.

If codebase inspection uncovers a useful implementation area or an ambiguity that materially changes the triage direction, post one concise progress comment summarizing what area is being checked. Do not post internal chain-of-thought, speculative reasoning, secrets, or large command output.

### 5. Choose one state

Use the following rubric. When evidence sits between states, choose the more cautious state.

#### Ready to implement

Choose when:

- Desired behavior and success criteria are clear
- Scope is bounded and cohesive with the current product
- Likely implementation area is identifiable
- Complexity and risk are low enough that a coding agent has a good chance of completing it correctly in one pass
- No unresolved product decision or major dependency blocks implementation

Small bugs with clear reproduction steps and straightforward improvements usually belong here.

#### Ready to spec

Choose when:

- The product goal is clear and appears worthwhile
- The work fits the product
- Material product or technical decisions remain
- Multiple valid designs, broad surface-area changes, migrations, or non-trivial dependencies make one-shot implementation risky

The issue should be clear enough to begin product or technical specification work without first asking the reporter basic questions.

#### Needs info

Choose when:

- The expected behavior, problem, scope, or reproduction is ambiguous
- Critical environment details, evidence, or acceptance criteria are missing
- The issue may be actionable, but the available information cannot support a responsible implementation or spec

State the smallest set of concrete questions whose answers would unblock re-triage.

#### Wait to implement

Choose when:

- The request does not fit cohesively into the current product or codebase direction
- It duplicates or conflicts with planned work
- The benefit does not justify the complexity or maintenance cost
- A dependency, platform limitation, or strategic decision makes work premature

Explain what would need to change before reconsidering it. Do not use this state merely because an issue is difficult; complex but cohesive work is usually `Ready to spec`.

### 6. Match and apply the tracker label

Inspect the tracker's existing labels before changing anything.

For the chosen state:

1. Prefer an existing label with the same meaning, even if capitalization or formatting differs, such as `ready-to-implement` for `Ready to implement`.
2. Reuse the tracker's established naming convention rather than adding a duplicate.
3. If no semantic equivalent exists and the tracker supports label creation, create the canonical label using the exact state name.
4. Remove any existing label that semantically corresponds to one of the other three triage states.
5. Preserve all unrelated labels.
6. Apply exactly one triage-state label.

If permissions prevent creating, removing, or applying labels, do not pretend the update succeeded. Report the chosen state, the intended label change, and the permission error.

### 7. Report the result

Keep the final response concise and include:

- Issue identifier and title
- Chosen state and the exact label applied
- Brief evidence-based rationale from the issue, codebase, and related open issues
- Key implementation area or remaining questions, when relevant
- Direct link to the issue

Use this format:

## Triage result
- **Issue:** [identifier and title](URL)
- **State:** `chosen state`
- **Applied label:** `exact tracker label`
- **Rationale:** 2-4 concise sentences
- **Next step:** One concrete action

## Guardrails

- Do not implement the issue during triage.
- Do not close, assign, reprioritize, or otherwise mutate the issue unless the user asks.
- Do not overwrite unrelated labels.
- Do not classify an issue without checking both the tracker context and the current codebase.
- Do not post excessive status comments. Always post the triage-started comment, then post at most two additional progress comments before the final result unless the issue is blocked by permissions or missing information.
- Do not post raw secrets, tokens, private environment variables, command output dumps, or internal reasoning in status comments.
- Treat comments from maintainers and linked product/spec documents as stronger evidence than guesses from code alone.
