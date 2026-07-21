---
name: spec
description: Coordinate spec-driven development for a GitHub, Jira, Linear, or other issue-tracker issue marked ready-to-spec by using write-product-spec and write-tech-spec, creating PRODUCT.md and TECH.md, opening a pull request, and routing the issue onward.
---

# Spec

Create checked-in product and technical specs for the issue passed in the user's prompt. Do not implement the product change.

This skill is a thin coordinator around the shared common-skills:

- `.agents/skills/write-product-spec/SKILL.md`
- `.agents/skills/write-tech-spec/SKILL.md`

Use those skills for the actual PRODUCT.md and TECH.md content. This skill owns issue intake, artifact location, branch/PR handoff, status comments, and readiness labels.

## Workflow

### 1. Identify the issue and repository

Extract the issue URL, key, or number from the prompt. Determine whether it belongs to GitHub Issues, Jira, Linear, or another tracker.

Confirm the current checkout is the repository where the future implementation should happen. If the prompt does not identify one issue unambiguously, ask for clarification before writing specs.

### 2. Verify required spec-writing skills

Confirm these files exist in the checkout:

- `.agents/skills/write-product-spec/SKILL.md`
- `.agents/skills/write-tech-spec/SKILL.md`

If either file is missing, stop and report that the common spec skills must be installed before spec work can proceed. Do not write substitute specs from memory.

### 3. Post a spec-started status comment

For GitHub Issues, post a short status comment before doing spec work so issue subscribers know an agent has started.

Use the authenticated `gh` CLI when available. Include:

- That automated Oz spec work has started.
- That the output will be checked-in `PRODUCT.md` and `TECH.md` files.
- A follow-along link to the Oz run (see **Oz run URLs** below).

Keep this comment concise.

### Oz run URLs

When posting any follow-along or status link to an Oz cloud run, use the **Oz web app** URL — never invent links from the API host.

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
- If no Oz run id or link is available yet, say the Oz follow-along link is not available yet rather than substituting another URL, and continue spec work.

### 4. Fetch tracker context

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

Do not write specs solely from the issue title. Do not expose credentials or secrets while fetching tracker data.

If tracker context is missing critical product intent, post a concise blocker comment with the specific missing information and stop instead of inventing requirements.

### 5. Choose the spec directory

Write specs under a dedicated issue directory:

```text
specs/<issue-slug>/PRODUCT.md
specs/<issue-slug>/TECH.md
```

Use a stable lowercase slug based on the tracker and issue number, such as `github-123-add-export-options` or `linear-app-321-new-image-export-flow`.

Create the `specs/<issue-slug>/` directory if needed. If the repository already has a different established specs directory convention, follow it while still producing files named exactly `PRODUCT.md` and `TECH.md`.

### 6. Write PRODUCT.md with write-product-spec

Read `.agents/skills/write-product-spec/SKILL.md` and follow it to write `specs/<issue-slug>/PRODUCT.md`.

Provide the common skill with:

- The issue title, description, comments, and linked context
- `roadmap.md` and `vision.md` if present
- Any existing product docs, specs, or related issues
- The chosen output path

The product spec should define user-facing behavior, goals, non-goals, acceptance criteria, and open product questions. If material product questions remain, keep them explicit in PRODUCT.md.

### 7. Write TECH.md with write-tech-spec

After PRODUCT.md exists, read `.agents/skills/write-tech-spec/SKILL.md` and follow it to write `specs/<issue-slug>/TECH.md`.

Provide the common skill with:

- The completed PRODUCT.md
- The issue context and related comments
- `roadmap.md` and `vision.md` if present
- Relevant codebase paths, architecture constraints, tests, build commands, and dependencies found during research
- The chosen output path

The technical spec should describe the implementation approach, affected code areas, alternatives considered, validation plan, rollout or migration concerns, and open technical questions.

### 8. Create a specs pull request

Create a descriptive branch such as `spec/issue-123-short-title`.

Commit only the spec artifacts and any directly necessary documentation changes. Use a clear commit message. When committing, include:

`Co-Authored-By: Oz <oz-agent@warp.dev>`

Push the branch and open a GitHub pull request against the repository's default branch using the authenticated `gh` CLI.

The PR description should include:

- A direct link to the original issue
- Links to `PRODUCT.md` and `TECH.md`
- Summary of the product and technical direction
- Open questions or reviewer decisions needed
- Whether the specs are ready for implementation after review

Do not include a closing keyword such as `Closes #123`; the spec PR does not implement the issue.

### 9. Publish the handoff

For GitHub Issues, post a final comment on the original issue with:

- Link to the specs PR
- Paths to `PRODUCT.md` and `TECH.md`
- Whether the issue is ready for implementation after spec review
- Any remaining product or technical questions

If both PRODUCT.md and TECH.md have no material open questions and the specs PR is ready for review, apply a spec-review label if available, such as `spec-ready-for-review`. Keep or remove `Ready to spec` according to the repository's convention.

Do not apply `Ready to implement` until the spec PR has been reviewed or the repository explicitly treats authored specs as implementation-ready without review.

If permissions prevent creating the branch, opening the PR, commenting, or updating labels, report the completed local artifacts and the permission error.

### 10. Report the result

Keep the final response concise and include:

- Issue identifier and title
- Specs PR URL
- PRODUCT.md path
- TECH.md path
- Label changes made or intended
- Direct link to the issue

Use this format:

## Spec result
- **Issue:** [identifier and title](URL)
- **Specs PR:** URL
- **Product spec:** `specs/<issue-slug>/PRODUCT.md`
- **Tech spec:** `specs/<issue-slug>/TECH.md`
- **Label changes:** concise description
- **Next step:** One concrete action

## Guardrails

- Do not implement the product change during spec work.
- Do not close, assign, reprioritize, or otherwise mutate the issue unless the user asks.
- Do not overwrite unrelated labels.
- Do not claim specs are implementation-ready if material product or technical decisions remain unresolved.
- Do not post raw secrets, tokens, private environment variables, command output dumps, or internal reasoning in status comments, specs, PR descriptions, or issue comments.
- Do not write substitute PRODUCT.md or TECH.md content without reading and following the common `write-product-spec` and `write-tech-spec` skills.
- Post progress sparingly: always post the spec-started comment, then post at most two additional progress comments before the final specs PR unless blocked or explicitly asked for more updates.
