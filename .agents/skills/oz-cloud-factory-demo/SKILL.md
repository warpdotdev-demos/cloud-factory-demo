---
name: oz-cloud-factory-demo
description: Sets up a beginner-friendly Oz cloud software factory that automatically triages new GitHub issues, specs issues labeled ready-to-spec, implements issues labeled ready-to-implement, reviews pull requests, and runs a daily improve-review outer loop. Use when a user wants to install, configure, test, or understand the Cloud Factory demo in a repository of their choice.
---

# Oz Cloud Factory Demo

Guide a user who is new to Oz through setting up this flow in a GitHub repository:

```text
new issue -> Oz triage -> Ready to spec label -> Oz spec -> PRODUCT.md + TECH.md PR
  -> Ready to implement -> Oz implementation -> PR
  -> Oz review-pr -> published GitHub review
  -> (daily) improve-review-pr may open a skill-update PR
```

Use the canonical installer and workflows from `warpdotdev-demos/cloud-factory-demo`. That installer is the source of truth for which skills and workflows belong in a full setup. Explain each action before taking it, keep secrets out of output and files, and stop at explicit activation checkpoints.

## Success criteria

The setup is complete when:

- The target repository contains every skill the canonical installer installs:
  - From `warpdotdev-demos/cloud-factory-demo`: `triage`, `spec`, `implementation`, `review-pr`, and `improve-review-pr`
  - From `warpdotdev/common-skills`: `write-product-spec`, `write-tech-spec`, and `validate-changes-match-specs`
- The target repository contains every Cloud Factory GitHub workflow the installer copies:
  - `triage-issues.yml`
  - `spec-ready-issues.yml`
  - `implement-ready-issues.yml`
  - `review-pull-requests.yml`
  - `improve-review-pr.yml`
- The repository has an Oz API key stored as the `WARP_API_KEY` Actions secret. A team key is preferred for shared automation, but a personal key is supported and may be necessary when creating keys through the Oz CLI.
- If using a team key, the Warp team has team GitHub authorization configured so implementation and improve-review runs can push branches and open pull requests. If using a personal key, runs authenticate as that user and use that user's GitHub permissions.
- The setup is committed and pushed to the repository's default branch.
- A newly opened test issue triggers triage and receives exactly one triage-state label.
- Applying `Ready to spec` triggers spec work and, for a suitable issue, opens a PR containing `PRODUCT.md` and `TECH.md`.
- Applying `Ready to implement` triggers implementation and, for a suitable issue, produces a pull request.
- Opening or updating a non-draft PR triggers automated review and a published GitHub review when the review workflow succeeds.
- The improve-review outer loop workflow is present and can be triggered manually with `workflow_dispatch` even if the daily schedule has not fired yet.

## Important concepts to explain

- **Oz** runs agents and records their runs. Each run consumes Warp credits.
- **Skills** are reusable agent instructions checked into `.agents/skills/`.
- **GitHub Actions** provides the event triggers and repository checkout for this demo.
- **Triage** classifies each new issue as `Ready to implement`, `Ready to spec`, `Needs info`, or `Wait to implement`.
- The triage workflow runs the agent **read-only**: a first job grants the agent only `contents: read` and `issues: read` and has it emit a structured JSON result, and a second deterministic `apply` job (`issues: write`) applies the label and comment to the triggering issue only. The agent never holds issue-write access, so it cannot modify other issues.
- **Spec** runs when the issue receives a ready-to-spec label, delegates spec content to the common `write-product-spec` and `write-tech-spec` skills, and opens a specs PR containing `PRODUCT.md` and `TECH.md`.
- **Implementation** runs only when the issue receives a ready-to-implement label. If `PRODUCT.md` and `TECH.md` specs exist, it reads them first and uses `validate-changes-match-specs` to check the completed diff against the specs before opening a PR.
- The implementation workflow has permission to create branches and pull requests. It does not merge them.
- **Code review** runs on non-draft pull request open/update events via `review-pull-requests.yml`. The agent runs **read-only** with the `review-pr` skill, writes structured findings to `review.json`, and a separate publish job posts the GitHub review. The agent never holds `pull-requests: write`.
- **Improve review** is a daily (and `workflow_dispatch`) outer loop via `improve-review-pr.yml`. It collects human reactions to automated review comments, runs the `improve-review-pr` skill, and may open a PR that updates `review-pr` or creates `review-pr-local` guidance. It does not change product code.
- Optional companion skills such as `review-pr-local` or `check-impl-against-spec` may exist in a consuming repository. They are not installed by the canonical Cloud Factory installer; mention them only if already present or if the user asks to add them.

## Workflow

### 1. Identify the target repository

Accept any of these from the user's prompt:

- A GitHub URL
- An `owner/repo` name
- A local checkout path

If none is supplied, ask for one. Do not guess.

Resolve the target to:

- `TARGET_REPO`: GitHub `owner/repo`
- `TARGET_DIR`: local checkout path
- `DEFAULT_BRANCH`: repository default branch

If no local checkout exists, ask where the user wants it cloned, then clone it with `gh repo clone`. Confirm `gh auth status` succeeds and that the user has permission to manage Actions secrets and push workflow files.

Always inventory the target before changing anything. This skill must support both:

- **Clean installs** for repositories with no Cloud Factory files yet.
- **Incremental upgrades** for repositories that already have some Cloud Factory pieces, including older Part 1 (triage + implementation only) or Part 2 (plus spec) installs that are missing the newer review and improve-review stages.

Before inventorying, re-read the canonical installer at `warpdotdev-demos/cloud-factory-demo` `scripts/install-cloud-factory.sh` (or the local copy if working in that repo) and treat its `npx skills add` skill list plus the workflow files it copies as the complete required set. Do not stop at the older triage/spec/implementation subset if the installer now also installs review skills or workflows.

Inspect the local checkout for every required skill and workflow:

- `.agents/skills/triage/SKILL.md`
- `.agents/skills/spec/SKILL.md`
- `.agents/skills/write-product-spec/SKILL.md`
- `.agents/skills/write-tech-spec/SKILL.md`
- `.agents/skills/validate-changes-match-specs/SKILL.md`
- `.agents/skills/implementation/SKILL.md`
- `.agents/skills/review-pr/SKILL.md`
- `.agents/skills/review-pr/scripts/` helpers used by the review workflow (`annotate_diff.py`, `publish_review.py`, `resolve_spec_context.py`, `validate_review_json.py`)
- `.agents/skills/improve-review-pr/SKILL.md`
- `.agents/skills/improve-review-pr/scripts/collect_review_feedback.py`
- `.github/workflows/triage-issues.yml`
- `.github/workflows/spec-ready-issues.yml`
- `.github/workflows/implement-ready-issues.yml`
- `.github/workflows/review-pull-requests.yml`
- `.github/workflows/improve-review-pr.yml`
- `roadmap.md`
- `vision.md`
- Cloud Factory README sections or other local setup notes

Also inspect the remote repository when possible:

- `gh workflow list --repo "$TARGET_REPO"` for `Triage New Issues`, `Spec Ready Issues`, `Implement Ready Issues`, `Review Pull Requests`, and `Improve Review PR Skill`.
- `gh secret list --repo "$TARGET_REPO"` for `WARP_API_KEY`.
- Existing issue labels that correspond to `Ready to implement`, `Ready to spec`, `Needs info`, and `Wait to implement`.

Classify the setup before proceeding:

- **Clean**: none of the Cloud Factory skills or workflows exist.
- **Part 1 installed**: triage and implementation skills/workflows exist, but later stages are missing.
- **Part 2 installed**: triage, spec, and implementation exist, but review and/or improve-review skills/workflows are missing.
- **Partial**: some Cloud Factory files exist, but one or more required skills or workflows from the canonical installer set are missing.
- **Current**: all expected skills, workflows, roadmap, and vision files from the canonical installer exist.
- **Customized**: expected files exist but differ materially from the canonical templates.

Report the classification, the files present, the files missing, and whether `WARP_API_KEY` appears to be configured. Explicitly call out any missing review-stage pieces even when triage/spec/implementation already look complete. Explain that automated runs consume credits and that workflow files only activate after they are present on the default branch.

Before changing anything, ask whether the user wants to:

1. Perform a clean installation of the full factory, including review and improve-review.
2. Upgrade an older setup by adding missing later stages (spec, review, and/or improve-review).
3. Repair a partial setup by adding missing pieces.
4. Review differences before overwriting any customized files.

Do not reject an existing setup merely because files are present. Treat existing triage, spec, implementation, review, or improve-review setup as reusable unless it conflicts with the desired flow.

### 2. Check prerequisites
#### Install or verify the Oz CLI

First determine whether the user is running the setup from Warp or another terminal.

If the user is running in Warp, explain that the Oz CLI is bundled with the Warp app and should already be available. Verify it rather than reinstalling it:

```sh
command -v oz
oz --version
```

If `oz` is not available in Warp, have the user open the Command Palette, search for **Install Oz CLI Command**, and run that action. Then verify `oz --version` again.

If the user is not running in Warp:

- On macOS, favor the supported Homebrew installation:

  ```sh
  brew tap warpdotdev/warp
  brew update
  brew install --cask oz
  ```

- On Linux, use Warp's supported package repository for the distribution and install `oz-stable` with `apt`, `yum`, or `pacman`.
- On Windows, install the Warp app because a standalone Oz CLI package is not currently available.

After installation, verify:

```sh
command -v oz
oz --version
```

Do not continue until both commands succeed. Use the stable `oz` command, not `oz-preview`, unless the user explicitly asks to use Preview.

#### Verify the remaining prerequisites

Verify these commands are available:

- `git`
- `gh`
- `node` and `npx`
- `curl`

Confirm the user is logged in with `oz whoami`. If not, run `oz login` and let the user complete the interactive login.

#### Choose the API key identity

Use `oz whoami` to determine whether the user belongs to the intended Warp team and whether this setup should run as a team automation or as the installing user.

Prefer a **team API key** when the repository is owned by a team and the team has GitHub authorization configured. Team keys are best for durable shared automation because runs are not tied to one user's account.

Allow a **personal API key** when:

- The user is testing or demoing the factory.
- The Oz CLI only supports creating the needed key as a personal key in the user's current environment.
- Team GitHub authorization is not configured yet, but the user wants runs to use their own GitHub permissions.

When using a personal key, clearly explain:

- Cloud agent runs authenticate as the user who created the key.
- GitHub writes such as branches and pull requests use that user's permissions and attribution.
- The user should rotate or remove the key when the demo or experiment is over.
- A future team setup can replace it with a team key once team GitHub authorization is configured.

If the user wants team-owned automation and does not have a Warp team, guide them through this setup before continuing:

1. Open Warp and go to **Settings > Teams**.
2. Follow the prompts to create a team and give it a meaningful organization or project name. The creator becomes the team admin.
3. Optionally copy the invite link from **Settings > Teams** and share it with teammates through a secure channel.
4. Have the team admin confirm the team is on a plan that supports cloud agents and Add-on Credits, and that at least 20 credits are available. Do not start automated runs until billing and credit availability are understood.
5. Have a GitHub organization admin install the [Oz by Warp GitHub App](https://github.com/apps/oz-by-warp) and grant it access to the target repository.
6. In Warp, have a team admin go to **Settings > Admin Panel > Platform** and add the GitHub organization under **Enabled GitHub Orgs**. This enables team API-key runs to clone the repository, push branches, and open pull requests.
7. Run `oz whoami` again and verify it shows the intended team before creating or storing team keys.

A Warp user can belong to only one team at a time. If the user already belongs to a different team, do not create another or switch teams without explaining the impact and receiving explicit approval.

Treat team-owned Oz automation as enabled for this Cloud Factory only after the team exists, the supported plan and credits are confirmed, the Oz by Warp GitHub App can access the repository, the GitHub organization is enabled in the Admin Panel, and `oz whoami` shows the intended team.

Confirm:

- `gh auth status` succeeds for the GitHub account that will create secrets, push workflow files, open issues, and inspect Actions runs.
- GitHub Actions is enabled for the repository.
- Issues are enabled for the repository.
- The repository allows GitHub Actions to create and approve pull requests, or the workflow is configured to use a PAT or GitHub App token with `pull-requests: write`.
- For a team-key setup, the user belongs to the intended Warp team and can create or request team-scoped resources.
- For a personal-key setup, the user understands that runs use their identity, GitHub permissions, and available credits.
- The relevant account or team has credits available for cloud runs.
- For a team-key setup, team GitHub authorization is configured for the target repository.

Explain that a run failing with `insufficient_credits` means a team admin must purchase Add-on Credits in the Oz web app or Warp billing settings. Never claim a credit balance was verified unless a tool actually exposed it.

### 3. Install the skills and workflows

From `TARGET_DIR`, inspect the existing `.agents/skills/` and `.github/workflows/` files first. If any target file already exists, compare it with the canonical file before overwriting it. Show the differences and ask before replacing customized files.

Keep the skill and workflow inventory aligned with the canonical installer. As of the current Cloud Factory, that full set is:

**Skills from `warpdotdev-demos/cloud-factory-demo`:**

- `triage`
- `spec`
- `implementation`
- `review-pr`
- `improve-review-pr`

**Skills from `warpdotdev/common-skills`:**

- `write-product-spec`
- `write-tech-spec`
- `validate-changes-match-specs`

**Workflows from `templates/github/workflows/`:**

- `triage-issues.yml`
- `spec-ready-issues.yml`
- `implement-ready-issues.yml`
- `review-pull-requests.yml`
- `improve-review-pr.yml`

If the installer on `main` has gained additional skills or workflows since this skill was last read, install those too. Prefer the live installer over any older subset documented elsewhere.

For a **clean install**, run the canonical installer from the target repository root. Prefer downloading it to a temporary file before running it so child commands cannot consume the rest of the script from stdin:

```sh
tmp_installer="$(mktemp)"
curl -fsSL https://raw.githubusercontent.com/warpdotdev-demos/cloud-factory-demo/main/scripts/install-cloud-factory.sh -o "$tmp_installer"
bash "$tmp_installer"
rm "$tmp_installer"
```

After the installer finishes, verify it actually added every required skill and workflow listed above. If any piece is missing, install or copy the missing pieces explicitly rather than treating the run as complete.

If the user only wants skills without workflows, the equivalent manual skill install is:

```sh
npx skills add warpdotdev-demos/cloud-factory-demo --skill triage --skill spec --skill implementation --skill review-pr --skill improve-review-pr --agent warp --yes
npx skills add warpdotdev/common-skills --skill write-product-spec --skill write-tech-spec --skill validate-changes-match-specs --agent warp --yes
```

For an **incremental upgrade**, do not blindly rerun the installer if it would overwrite customized existing files. Add or update only the missing pieces for the stages the repository lacks.

Missing **spec flow** pieces:

```sh
npx skills add warpdotdev-demos/cloud-factory-demo --skill spec --agent warp --yes
npx skills add warpdotdev/common-skills --skill write-product-spec --skill write-tech-spec --skill validate-changes-match-specs --agent warp --yes
mkdir -p .github/workflows
curl -fsSL https://raw.githubusercontent.com/warpdotdev-demos/cloud-factory-demo/main/templates/github/workflows/spec-ready-issues.yml -o .github/workflows/spec-ready-issues.yml
```

Missing **review / improve-review** pieces:

```sh
npx skills add warpdotdev-demos/cloud-factory-demo --skill review-pr --skill improve-review-pr --agent warp --yes
mkdir -p .github/workflows
curl -fsSL https://raw.githubusercontent.com/warpdotdev-demos/cloud-factory-demo/main/templates/github/workflows/review-pull-requests.yml -o .github/workflows/review-pull-requests.yml
curl -fsSL https://raw.githubusercontent.com/warpdotdev-demos/cloud-factory-demo/main/templates/github/workflows/improve-review-pr.yml -o .github/workflows/improve-review-pr.yml
```

Then compare the existing local files against the current canonical versions and ask before updating them:

- `.agents/skills/triage/SKILL.md` may need readiness logic that uses `roadmap.md` and `vision.md` to decide when to return `Ready to spec`.
- `.agents/skills/implementation/SKILL.md` may need the logic that reads `PRODUCT.md` and `TECH.md` before implementation and runs `validate-changes-match-specs` after implementation.
- `.github/workflows/implement-ready-issues.yml` may need the step that installs `validate-changes-match-specs` before running the implementation agent.
- `.agents/skills/review-pr/SKILL.md` and its `scripts/` directory must be present for the review workflow's annotate/publish/validate helpers.
- `.agents/skills/improve-review-pr/SKILL.md` and its collector script must be present for the daily outer loop.
- `roadmap.md` and `vision.md` should be added if they do not already exist, because the triage flow relies on them when deciding between ready-to-spec and ready-to-implement.

For a **partial setup repair**, install or copy only missing required pieces when possible. If a file exists but is incomplete or outdated, show a diff against the canonical template and get approval before overwriting.

Review the resulting diff. Explain:

- `triage-issues.yml` triggers when an issue is opened.
- `spec-ready-issues.yml` triggers when an issue receives a ready-to-spec label and opens a specs PR containing `PRODUCT.md` and `TECH.md`.
- `implement-ready-issues.yml` triggers when an issue receives a ready-to-implement label and validates the completed implementation against `PRODUCT.md` and `TECH.md` when specs exist.
- `review-pull-requests.yml` triggers on non-draft pull request open/synchronize/reopened/ready_for_review events, runs `review-pr` read-only, and publishes `review.json` as a GitHub review.
- `improve-review-pr.yml` runs on a daily schedule and on `workflow_dispatch`, collects human review feedback, and may open a skill-update PR.
- The workflows use `warpdotdev/oz-agent-action@v1`.
- GitHub's token supplies repository permissions; `WARP_API_KEY` authenticates Oz.

Do not silently customize the installed skills. If the repository has special build, test, security, or contribution requirements, offer to add them to the implementation skill or a local `review-pr-local` companion and show the proposed changes first.

### 4. Configure Oz authentication safely

The workflows require a repository Actions secret named `WARP_API_KEY`. It may contain either:

- A **team API key**, preferred for durable shared automation when team GitHub authorization is configured.
- A **personal API key**, supported for demos, experiments, and cases where the Oz CLI can only create a personal key. Personal-key runs use the creating user's identity, credits, GitHub permissions, and GitHub attribution.

If the user already has an appropriate key, have them put it into an environment variable without printing it. Then store it and clear the local variable:

```sh
printf '%s' "$WARP_API_KEY" | gh secret set WARP_API_KEY --repo "$TARGET_REPO"
unset WARP_API_KEY
```

If they need a key, the most explicit path is **Settings > Cloud platform > Oz Cloud API Keys** in Warp or the Oz web app. Create a key named `cloud-factory-github-actions`, choose an expiration appropriate for the demo or automation, and choose `Team` or `Personal` based on the identity decision above. Copy its one-time value into `WARP_API_KEY` without printing it.

If using the Oz CLI to create the key, first run `oz api-key create --help` and use the supported form. If the CLI only supports creating a personal key in the current environment, it is acceptable to use that personal key for this demo. When using JSON output, the one-time secret value is currently in the `raw_api_key` field. Pipe or store only that value directly into the GitHub secret.

After creating a key by any method, verify metadata only, never the raw key value:

```sh
oz api-key list --output-format json
```

The key used for automation should show the intended scope: `Team` for team-owned automation, or `Personal` for a user-owned demo or CLI-created setup. If a personal key is used, document that choice in the setup summary so future maintainers know the automation depends on that user's account.

Never print, read back, commit, or write the key to a repository file. Confirm only that the `WARP_API_KEY` secret name exists using `gh secret list --repo "$TARGET_REPO"`.

An optional `WARP_AGENT_PROFILE` repository variable may select a preconfigured Oz Agent Profile. For team-key automation, prefer a team profile. For personal-key demos, a personal profile is acceptable if the user understands it is tied to their account.

### 5. Review and activate

Before activation, review:

- The complete git diff
- Workflow permissions for all five workflows
- The selected API key scope, GitHub authorization model, and any Agent Profile
- GitHub Actions workflow permissions, especially whether Actions can create and approve pull requests
- The four triage labels and routing behavior
- Expected credit consumption across triage, spec, implementation, review, and improve-review runs
- The fact that spec agents can create branches, open specs PRs, and change readiness labels
- The fact that implementation agents can push branches and open PRs
- The fact that review agents write `review.json` only and a separate publish job posts GitHub reviews
- The fact that improve-review may open skill-update PRs on a schedule

Do not commit or push without explicit user approval. The workflows only activate after they are present on the default branch. If the user prefers review first, create a setup branch and pull request, then explain that automation begins after merge.

After activation, confirm all five workflows appear with:

```sh
gh workflow list --repo "$TARGET_REPO"
```

Expected workflow names:

- `Triage New Issues`
- `Spec Ready Issues`
- `Implement Ready Issues`
- `Review Pull Requests`
- `Improve Review PR Skill`

If this was an incremental upgrade, also confirm:

- Existing earlier-stage files were preserved unless the user approved updates.
- Any previously missing workflows from the full set were added.
- All required skills from the canonical installer exist, including `review-pr` and `improve-review-pr` when those stages are in scope.
- `roadmap.md` and `vision.md` exist or the user explicitly chose to defer adding them.
- The triage skill can return `Ready to spec` for issues that match the roadmap and vision but are too ambiguous or complex to one-shot.

### 6. Test triage first

Ask permission before creating a test issue because opening it triggers a billable cloud run.

Create one small, clear, safe issue that is relevant to the target repository. Avoid an issue likely to cause destructive, security-sensitive, or broad changes. Capture its URL.

Watch the `Triage New Issues` workflow and inspect its result with `gh run list` and `gh run view`. The workflow runs two jobs: a read-only `triage` job (the agent analyzes the issue and emits a JSON result) and a deterministic `apply` job that posts the result comment and applies the label. Confirm:

- Both jobs ran successfully.
- The `apply` job posted the triage result as a comment on the issue.
- Exactly one triage-state label was applied.
- The Oz run is visible in the Oz Runs page.

If triage does not choose `Ready to implement` or `Ready to spec`, do not override the label merely to force a downstream run. Explain the result and either improve the test issue with the user or create a separate suitable test issue with permission.

If triage applies `Ready to spec` but no spec workflow starts, check whether the label was applied by `github-actions` using GitHub's default token. GitHub does not trigger most new workflow runs from events created by `GITHUB_TOKEN`, so a label applied by the triage workflow may not fire the separate `issues.labeled` spec workflow. For a smoke test, explain this limitation and ask before manually removing and re-adding the label as a human user. For a durable setup, recommend changing the workflow design to use a PAT or GitHub App token for label writes, dispatch the spec workflow explicitly, or combine orchestration so spec work is not dependent on a suppressed follow-up event.

If triage applies `Ready to implement` but no implementation workflow starts, check whether the label was applied by `github-actions` using GitHub's default token. GitHub does not trigger most new workflow runs from events created by `GITHUB_TOKEN`, so a label applied by the triage workflow may not fire the separate `issues.labeled` implementation workflow. For a smoke test, explain this limitation and ask before manually removing and re-adding the label as a human user. For a durable setup, recommend changing the workflow design to use a PAT or GitHub App token for label writes, dispatch the implementation workflow explicitly, or combine orchestration so implementation is not dependent on a suppressed follow-up event.

### 7. Test spec work

Before allowing a `Ready to spec` label to trigger spec work, remind the user that this starts another billable run that may create a branch, open a specs PR, post comments, and change labels.

Watch the `Spec Ready Issues` workflow. Confirm:

- The spec run starts.
- The agent posts progress to the issue.
- The agent creates `PRODUCT.md` and `TECH.md` under a specs directory.
- The agent opens a specs pull request and links it from the issue.
- The agent does not apply `Ready to implement` until the specs PR has been reviewed or the repository explicitly treats authored specs as implementation-ready without review.

If spec applies `Ready to implement` but no implementation workflow starts, check whether the label was applied by `github-actions` using GitHub's default token. Account for GitHub's `GITHUB_TOKEN` event suppression in the same way as the triage-to-spec handoff.

### 8. Test implementation

Before allowing a `Ready to implement` label to trigger implementation, remind the user that this starts another billable run that may push a branch and open a PR.

Watch the `Implement Ready Issues` workflow. Confirm:

- The implementation run starts.
- The agent posts progress to the issue.
- The agent validates its change.
- A pull request is opened and linked from the issue.

Do not merge the test PR. Present the PR, validation results, Oz run link, and any failures for human review.

### 9. Test automated code review

Opening or updating a non-draft PR should trigger `Review Pull Requests`. If implementation already opened a non-draft PR, watch that review run. Otherwise, with permission, open a small non-draft PR or mark a draft PR ready for review.

Remind the user that review is another billable cloud run.

Confirm:

- The `review` job starts on the non-draft PR event.
- Review inputs are prepared (`pr_diff.txt`, `pr_description.txt`, and `spec_context.md` when available).
- The Oz agent runs with the `review-pr` skill and produces `review.json`.
- The separate `publish` job posts a GitHub pull request review.
- The review agent itself does not hold write access to pull requests; publishing is deterministic and separate.

If APPROVE events fail while COMMENT still works, check whether the repository or organization allows GitHub Actions to create and approve pull requests. Explain that the publish helper can fall back to COMMENT for approvals when that setting is off.

### 10. Test the improve-review outer loop

The improve-review workflow is scheduled daily and also supports `workflow_dispatch`. Do not wait for the cron schedule during setup. With permission, trigger it manually:

```sh
gh workflow run "Improve Review PR Skill" --repo "$TARGET_REPO"
```

Remind the user that this is another billable run and that it may open a skill-update PR only if durable learnings exist.

Confirm:

- The workflow starts and checks out the default branch.
- The collector writes `feedback_corpus.json`.
- The Oz agent runs with the `improve-review-pr` skill.
- If there is no durable learning, no empty PR is opened.
- If a skill PR is opened, it only changes review guidance (`review-pr` and/or `review-pr-local`) and is left unmerged for human review.

If the repository is brand new and has no prior automated reviews, a no-op improve run with no skill PR is an acceptable successful smoke test.

## Troubleshooting

- **Workflow is missing:** Confirm all five workflow files are committed to the default branch and Actions is enabled.
- **Setup claims complete but review is missing:** Re-check against the canonical installer. Older setup docs only covered triage/spec/implementation; a current setup also requires `review-pr`, `improve-review-pr`, `review-pull-requests.yml`, and `improve-review-pr.yml`.
- **`WARP_API_KEY` error:** Confirm the repository secret exists and the key is valid. Never expose its value.
- **Team key cannot write to GitHub:** Confirm team GitHub authorization is configured for the target repository, or switch to an explicitly user-approved personal key for a demo or user-owned setup.
- **Personal key writes as the wrong user:** Replace the `WARP_API_KEY` secret with a key created by the intended user, or move to a team key with team GitHub authorization.
- **`insufficient_credits`:** Direct a team admin to purchase Add-on Credits in Oz or Warp billing settings, then retry.
- **Permission failure:** Compare the workflow's `permissions` block with the attempted action and check repository or organization Actions policy.
- **PR creation blocked:** Enable repository or organization Actions settings that allow GitHub Actions to create and approve pull requests, or configure a PAT/GitHub App token with pull request write permission.
- **Skill not found:** Confirm the exact installed paths and that each workflow references the correct skill (`triage`, `spec`, `implementation` via prompt, `review-pr`, `improve-review-pr`).
- **Review helper scripts missing:** Confirm `.agents/skills/review-pr/scripts/` contains `annotate_diff.py`, `publish_review.py`, `resolve_spec_context.py`, and `validate_review_json.py`. Reinstall `review-pr` if the skill was copied without its scripts.
- **Spec does not trigger:** Confirm the issue received `Ready to spec`, `ready-to-spec`, or `ready to spec`. If triage added the label from `github-actions`, account for GitHub's `GITHUB_TOKEN` event suppression.
- **Implementation does not trigger:** Confirm the issue received `Ready to implement`, `ready-to-implement`, or `ready to implement`. If triage added the label from `github-actions`, account for GitHub's `GITHUB_TOKEN` event suppression.
- **Review does not trigger:** Confirm the PR is not a draft, the event was `opened`/`synchronize`/`reopened`/`ready_for_review`, and `review-pull-requests.yml` is on the default branch. Draft PRs are intentionally skipped.
- **Review publishes no GitHub review:** Confirm the `publish` job has `pull-requests: write`, `review.json` was uploaded, and `publish_review.py` ran against the annotated diff.
- **Improve-review never runs:** Confirm `improve-review-pr.yml` is on the default branch. Use `workflow_dispatch` for an immediate smoke test instead of waiting for the daily cron.
- **Agent cannot build the project:** Improve the repository's setup instructions or implementation skill, or update the GitHub Actions runner setup so the required toolchain is available.

## Guardrails

- Never reveal, print, or commit API keys or other secrets.
- Never silently choose an API key identity. Personal Oz API keys and personal Agent Profiles are allowed for demos or user-owned setup, but clearly state that runs use that user's identity, credits, GitHub permissions, and attribution.
- Never activate workflows, open a test issue, trigger spec work, trigger implementation, trigger review, trigger improve-review, or push to the default branch without explaining the consequence and receiving explicit approval.
- Never weaken repository protections or broaden workflow permissions just to make the demo pass.
- Never force ambiguous or risky issues into `Ready to implement`.
- Never merge an implementation PR or skill-update PR automatically.
- Prefer the canonical installer and templates over manually recreating them, and treat the live installer skill/workflow list as authoritative over older partial docs.
- Keep the user oriented: after each stage, summarize what changed, what will happen next, and whether the next action triggers a billable run.
