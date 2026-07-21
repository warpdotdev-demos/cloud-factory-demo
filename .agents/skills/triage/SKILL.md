---
name: triage
description: Triage an incoming GitHub, Jira, Linear, or other issue-tracker issue against the current codebase and related open issues, then return a structured decision with exactly one implementation-readiness state. Use whenever the user asks to triage, classify, assess, prioritize, or label an issue for implementation readiness, especially when an issue URL, key, or number is supplied in the prompt. For UI or interactive bugs, optionally invoke the verify-behavior skill as a cloud computer-use subagent to reproduce the issue before deciding.
---

# Triage

Assess the issue passed in the user's prompt and decide exactly one implementation-readiness state:

- `Ready to implement`
- `Ready to spec`
- `Needs info`
- `Wait to implement`

The goal is to route work honestly, not to make every issue appear actionable. Base the decision on evidence from the issue tracker, current checkout, and related open issues.

This is a read-only analysis: inspect the issue and codebase but do not mutate the tracker. Return the structured decision described in step 6; the caller applies the label and comment.

## Workflow

### 1. Identify the issue and tracker

Extract the issue URL, key, or number from the prompt. Determine whether it belongs to GitHub Issues, Jira, Linear, or another tracker.

If the prompt does not identify one issue unambiguously, ask the user for the issue rather than guessing.

### 2. Fetch tracker context

Read the issue using the best available integration, in this order:

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

### 3. Inspect the current codebase

Confirm the current checkout is the relevant repository. Search the codebase for the affected feature, behavior, terminology, and likely implementation area.

If `roadmap.md` or `vision.md` exist at the repository root, read them first. Use them to determine whether the issue aligns with the stated product direction before choosing a state.

Assess:

- Whether the described behavior exists today
- Likely files, services, and systems involved
- Whether the issue has a bounded implementation path
- Dependencies, migrations, platform differences, and testing requirements
- Existing abstractions that make the change cohesive or indicate it does not fit
- Whether the issue aligns with the roadmap and vision (if those documents exist)
- Whether related open issues or active work change the recommendation

Prefer targeted searches and reads. This is triage, not implementation: do not edit product code.

### 4. Optionally reproduce visible bugs with verify-behavior

When the issue is a UI, browser, desktop, rendering, layout, or other interactive bug, and visual reproduction would materially improve the readiness decision, use the factory verification skill:

1. If `.agents/skills/verify-behavior/SKILL.md` exists, read it and follow its parent workflow in `reproduce` mode.
2. Launch the verification work as an Oz cloud computer-use **subagent** (do not drive the GUI yourself unless the user explicitly asks).
3. Prefer video evidence of the repro path; accept screenshots when they are clearer or video is unavailable.
4. Fold the reproduction status into your rationale. Confirmed repro strengthens `Ready to implement` or `Ready to spec` when the rest of the rubric fits. Failed or blocked repro often supports `Needs info` when steps or environment details are missing.

Skip this step for non-visual issues, when the skill file is missing, or when computer-use verification is clearly unnecessary overhead for a trivial, already well-specified bug. Never block forever on verification: if the subagent is blocked, record that and continue with the best evidence-based state.

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

Choose when ALL of the following are true:

- The product goal is clear and appears worthwhile
- The work aligns with the product's roadmap and vision
- The issue has either ambiguity or significant complexity:
  - **Ambiguity**: Multiple valid product or technical implementations exist with significant differences; a human should weigh in on which direction to pursue
  - **Complexity**: The implementation is likely more than a few hundred lines of code, spans multiple systems, requires migrations, or carries non-trivial risk

The issue should be clear enough to begin product or technical specification work without first asking the reporter basic questions.

If the repository contains `roadmap.md` or `vision.md`, read them before applying this state. Only apply `ready-to-spec` when the issue fits the stated product direction. If the issue is interesting but does not align with the roadmap or vision, prefer `wait-to-implement` instead.

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

### 6. Return the result

Pick the tracker label that matches the chosen state, preferring an existing label with the same meaning and the tracker's established naming and casing (for example `ready-to-implement` for `Ready to implement`). List any existing triage-state labels that should be removed.

Return a single raw JSON object as your final response — no prose and no markdown code fences:

```json
{
  "state": "Ready to implement | Ready to spec | Needs info | Wait to implement",
  "label": "exact tracker label matching the chosen state",
  "remove_labels": ["existing triage-state labels that should be removed"],
  "comment": "markdown body for the issue"
}
```

Write `comment` as reporter-facing markdown: a short lead sentence with the decision, then the evidence-based rationale and one concrete next step, using a brief bullet list where it aids readability. If verify-behavior ran, include a short reproduction status and any Oz run or evidence links that are safe to share. Oz run links must use `https://oz.warp.dev/runs/<run-id>` (or `https://oz.staging.warp.dev/runs/<run-id>` on staging) — never `app.warp.dev` or `/run/` (singular). Because `comment` is a JSON string, encode every line break as `\n` (a literal newline would make the JSON invalid).

## Guardrails

- Do not mutate the tracker: no comments, labels, status, assignment, or other changes. Return the structured result instead.
- Do not implement the issue during triage or edit product code.
- Do not classify an issue without checking both the tracker context and the current codebase.
- When visual reproduction would help and `verify-behavior` is installed, prefer launching it as a cloud computer-use subagent over ad-hoc local clicking.
- Do not put raw secrets, tokens, private environment variables, command output dumps, or internal reasoning in the result.
- Treat comments from maintainers and linked product/spec documents as stronger evidence than guesses from code alone.
