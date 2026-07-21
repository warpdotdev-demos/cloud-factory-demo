---
name: oz-cloud-factory-demo
description: Sets up a beginner-friendly Oz cloud software factory that automatically triages new GitHub issues, specs issues labeled ready-to-spec, implements issues labeled ready-to-implement, reviews PRs, and verifies visible behavior with Oz computer-use subagents. Use when a user wants to install, configure, test, or understand the Cloud Factory demo in a repository of their choice.
---

# Oz Cloud Factory Demo

Guide a user who is new to Oz through setting up this flow in a GitHub repository:

```text
new issue -> Oz triage (+ optional verify-behavior reproduce) -> Ready to spec label -> Oz spec -> PRODUCT.md + TECH.md PR -> Oz implementation (+ optional verify-behavior verify, with parallel story fan-out for features) -> pull request -> Oz review (+ optional verify-behavior)
```

Use the canonical installer and workflows from `warpdotdev-demos/cloud-factory-demo`. Explain each action before taking it, keep secrets out of output and files, and stop at explicit activation checkpoints.

## Success criteria

The setup is complete when:

- The target repository contains the `triage`, `spec`, `write-product-spec`, `write-tech-spec`, `validate-changes-match-specs`, `implementation`, and `verify-behavior` skills.
- The target repository contains the three Cloud Factory GitHub workflows.
- The repository has an Oz API key stored as the `WARP_API_KEY` Actions secret. A team key is preferred for shared automation, but a personal key is supported and may be necessary when creating keys through the Oz CLI.
- If using a team key, the Warp team has team GitHub authorization configured so implementation runs can push branches and open pull requests. If using a personal key, runs authenticate as that user and use that user's GitHub permissions.
- The setup is committed and pushed to the repository's default branch.
- A newly opened test issue triggers triage and receives exactly one triage-state label.
- Applying `Ready to spec` triggers spec work and, for a suitable issue, opens a PR containing `PRODUCT.md` and `TECH.md`.
- Applying `Ready to implement` triggers implementation and, for a suitable issue, produces a pull request.

## Important concepts to explain

- **Oz** runs agents and records their runs. Each run consumes Warp credits.
- **Skills** are reusable agent instructions checked into `.agents/skills/`.
- **GitHub Actions** provides the event triggers and repository checkout for this demo.
- **Triage** classifies each new issue as `Ready to implement`, `Ready to spec`, `Needs info`, or `Wait to implement`.
- The triage workflow runs the agent **read-only**: a first job grants the agent only `contents: read` and `issues: read` and has it emit a structured JSON result, and a second deterministic `apply` job (`issues: write`) applies the label and comment to the triggering issue only. The agent never holds issue-write access, so it cannot modify other issues.
- **Verification (`verify-behavior`)** is a shared skill other stages invoke as Oz cloud subagent work. It chooses **browser use** (Chrome + Puppeteer MCP) for most web flows or **computer use** for native apps and multi-surface journeys. Triage can use it in `reproduce` mode for UI bugs; implementation and review can use it in `verify` mode for greenfield features and fixes. When `PRODUCT.md` defines multiple user stories, feature verification defaults to **parallel story fan-out** with computer-use-capable workers. Default evidence is video of each critical path, with screenshots as keyframes or fallbacks.
- **Spec** runs when the issue receives a ready-to-spec label, delegates spec content to the common `write-product-spec` and `write-tech-spec` skills, and opens a specs PR containing `PRODUCT.md` and `TECH.md`.
- **Implementation** runs only when the issue receives a ready-to-implement label. If `PRODUCT.md` and `TECH.md` specs exist, it reads them first and uses `validate-changes-match-specs` to check the completed diff against the specs before opening a PR. For visible UI features or fixes it should also invoke `verify-behavior` in `verify` mode when cloud verification is available.
- The implementation workflow has permission to create branches and pull requests. It does not merge them.

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
- **Incremental upgrades** for repositories that already followed Part 1 of the Cloud Factory walkthrough and have triage plus implementation installed, but do not yet have the spec flow from Part 2.

Inspect the local checkout for:

- `.agents/skills/triage/SKILL.md`
- `.agents/skills/spec/SKILL.md`
- `.agents/skills/write-product-spec/SKILL.md`
- `.agents/skills/write-tech-spec/SKILL.md`
- `.agents/skills/validate-changes-match-specs/SKILL.md`
- `.agents/skills/implementation/SKILL.md`
- `.agents/skills/verify-behavior/SKILL.md`
- `.github/workflows/triage-issues.yml`
- `.github/workflows/spec-ready-issues.yml`
- `.github/workflows/implement-ready-issues.yml`
- `roadmap.md`
- `vision.md`
- Cloud Factory README sections or other local setup notes

Also inspect the remote repository when possible:

- `gh workflow list --repo "$TARGET_REPO"` for `Triage New Issues`, `Spec Ready Issues`, and `Implement Ready Issues`.
- `gh secret list --repo "$TARGET_REPO"` for `WARP_API_KEY`.
- Existing issue labels that correspond to `Ready to implement`, `Ready to spec`, `Needs info`, and `Wait to implement`.

Classify the setup before proceeding:

- **Clean**: none of the Cloud Factory skills or workflows exist.
- **Part 1 installed**: triage and implementation skills/workflows exist, but spec skill/workflow and common spec skills are missing.
- **Partial**: some Cloud Factory files exist, but one or more required files for triage, spec, implementation, common spec writing, or spec validation are missing.
- **Current**: all expected skills, workflows, roadmap, and vision files exist.
- **Customized**: expected files exist but differ materially from the canonical templates.

Report the classification, the files present, the files missing, and whether `WARP_API_KEY` appears to be configured. Explain that automated runs consume credits and that workflow files only activate after they are present on the default branch.

Before changing anything, ask whether the user wants to:

1. Perform a clean installation.
2. Upgrade an existing Part 1 setup to add the Part 2 spec flow.
3. Repair a partial setup by adding missing pieces.
4. Review differences before overwriting any customized files.

Do not reject an existing setup merely because files are present. Treat existing triage or implementation setup as reusable unless it conflicts with the desired flow.

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

For a **clean install**, run the canonical installer from the target repository root. Prefer downloading it to a temporary file before running it so child commands cannot consume the rest of the script from stdin:

```sh
tmp_installer="$(mktemp)"
curl -fsSL https://raw.githubusercontent.com/warpdotdev-demos/cloud-factory-demo/main/scripts/install-cloud-factory.sh -o "$tmp_installer"
bash "$tmp_installer"
rm "$tmp_installer"
```
The installer should add:

- `.agents/skills/triage/SKILL.md`
- `.agents/skills/spec/SKILL.md`
- `.agents/skills/write-product-spec/SKILL.md`
- `.agents/skills/write-tech-spec/SKILL.md`
- `.agents/skills/validate-changes-match-specs/SKILL.md`
- `.agents/skills/implementation/SKILL.md`
- `.agents/skills/verify-behavior/SKILL.md`
- `.github/workflows/triage-issues.yml`
- `.github/workflows/spec-ready-issues.yml`
- `.github/workflows/implement-ready-issues.yml`

For an **incremental Part 1 → Part 2 upgrade**, do not blindly rerun the installer if it would overwrite customized triage or implementation files. Add or update only the missing spec-flow pieces:

```sh
npx skills add warpdotdev-demos/cloud-factory-demo --skill spec --agent warp --yes
npx skills add warpdotdev/common-skills --skill write-product-spec --skill write-tech-spec --skill validate-changes-match-specs --agent warp --yes
mkdir -p .github/workflows
curl -fsSL https://raw.githubusercontent.com/warpdotdev-demos/cloud-factory-demo/main/templates/github/workflows/spec-ready-issues.yml -o .github/workflows/spec-ready-issues.yml
```

Then compare the existing local files against the current canonical versions and ask before updating them:

- `.agents/skills/triage/SKILL.md` may need the Part 2 readiness logic that uses `roadmap.md` and `vision.md` to decide when to return `Ready to spec`.
- `.agents/skills/implementation/SKILL.md` may need the Part 2 logic that reads `PRODUCT.md` and `TECH.md` before implementation and runs `validate-changes-match-specs` after implementation.
- `.github/workflows/implement-ready-issues.yml` may need the step that installs `validate-changes-match-specs` before running the implementation agent.
- `roadmap.md` and `vision.md` should be added if they do not already exist, because the Part 2 triage flow relies on them.

For a **partial setup repair**, install or copy only missing required pieces when possible. If a file exists but is incomplete or outdated, show a diff against the canonical template and get approval before overwriting.

Review the resulting diff. Explain:

- `triage-issues.yml` triggers when an issue is opened.
- `spec-ready-issues.yml` triggers when an issue receives a ready-to-spec label and opens a specs PR containing `PRODUCT.md` and `TECH.md`.
- `implement-ready-issues.yml` triggers when an issue receives a ready-to-implement label and validates the completed implementation against `PRODUCT.md` and `TECH.md` when specs exist.
- `verify-behavior` is not a separate GitHub workflow. Parent agents (triage, implementation, review) invoke it as a cloud subagent when visual evidence helps.
- Explain that verification children choose browser use (Chrome/Puppeteer MCP) vs computer use based on the app surface, that computer use runs only in Oz cloud sandboxes and is opt-in for the account/team, and that children should capture video by default.
- The workflows use `warpdotdev/oz-agent-action@v1`.
- GitHub's token supplies repository permissions; `WARP_API_KEY` authenticates Oz.

Do not silently customize the installed skills. If the repository has special build, test, security, or contribution requirements, offer to add them to the implementation skill and show the proposed changes first.

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
- Workflow permissions
- The selected API key scope, GitHub authorization model, and any Agent Profile
- GitHub Actions workflow permissions, especially whether Actions can create and approve pull requests
- The four triage labels and routing behavior
- Expected credit consumption
- The fact that spec agents can create branches, open specs PRs, and change readiness labels
- The fact that implementation agents can push branches and open PRs

Do not commit or push without explicit user approval. The workflows only activate after they are present on the default branch. If the user prefers review first, create a setup branch and pull request, then explain that automation begins after merge.

After activation, confirm all three workflows appear with:

```sh
gh workflow list --repo "$TARGET_REPO"
```

If this was an incremental Part 1 → Part 2 upgrade, also confirm:

- Existing triage and implementation files were preserved unless the user approved updates.
- `.github/workflows/spec-ready-issues.yml` was added.
- `.agents/skills/spec/SKILL.md`, `.agents/skills/write-product-spec/SKILL.md`, `.agents/skills/write-tech-spec/SKILL.md`, and `.agents/skills/validate-changes-match-specs/SKILL.md` exist.
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

## Troubleshooting

- **Workflow is missing:** Confirm all three workflow files are committed to the default branch and Actions is enabled.
- **`WARP_API_KEY` error:** Confirm the repository secret exists and the key is valid. Never expose its value.
- **Team key cannot write to GitHub:** Confirm team GitHub authorization is configured for the target repository, or switch to an explicitly user-approved personal key for a demo or user-owned setup.
- **Personal key writes as the wrong user:** Replace the `WARP_API_KEY` secret with a key created by the intended user, or move to a team key with team GitHub authorization.
- **`insufficient_credits`:** Direct a team admin to purchase Add-on Credits in Oz or Warp billing settings, then retry.
- **Permission failure:** Compare the workflow's `permissions` block with the attempted action and check repository or organization Actions policy.
- **PR creation blocked:** Enable repository or organization Actions settings that allow GitHub Actions to create and approve pull requests, or configure a PAT/GitHub App token with pull request write permission.
- **Skill not found:** Confirm the exact installed paths and that the triage workflow references `triage`.
- **Spec does not trigger:** Confirm the issue received `Ready to spec`, `ready-to-spec`, or `ready to spec`. If triage added the label from `github-actions`, account for GitHub's `GITHUB_TOKEN` event suppression.
- **Implementation does not trigger:** Confirm the issue received `Ready to implement`, `ready-to-implement`, or `ready to implement`. If triage added the label from `github-actions`, account for GitHub's `GITHUB_TOKEN` event suppression.
- **Agent cannot build the project:** Improve the repository's setup instructions or implementation skill, or update the GitHub Actions runner setup so the required toolchain is available.

## Guardrails

- Never reveal, print, or commit API keys or other secrets.
- Never silently choose an API key identity. Personal Oz API keys and personal Agent Profiles are allowed for demos or user-owned setup, but clearly state that runs use that user's identity, credits, GitHub permissions, and attribution.
- Never activate workflows, open a test issue, trigger spec work, trigger implementation, or push to the default branch without explaining the consequence and receiving explicit approval.
- Never weaken repository protections or broaden workflow permissions just to make the demo pass.
- Never force ambiguous or risky issues into `Ready to implement`.
- Never merge an implementation PR automatically.
- Prefer the canonical installer and templates over manually recreating them.
- Keep the user oriented: after each stage, summarize what changed, what will happen next, and whether the next action triggers a billable run.
