---
name: oz-cloud-factory-demo
description: Sets up a beginner-friendly Oz cloud software factory that automatically triages new GitHub issues and implements issues labeled ready-to-implement. Use when a user wants to install, configure, test, or understand the Cloud Factory demo in a repository of their choice.
---

# Oz Cloud Factory Demo

Guide a user who is new to Oz through setting up this flow in a GitHub repository:

```text
new issue -> Oz triage -> Ready to implement label -> Oz implementation -> pull request
```

Use the canonical installer and workflows from `warpdotdev-demos/cloud-factory-demo`. Explain each action before taking it, keep secrets out of output and files, and stop at explicit activation checkpoints.

## Success criteria

The setup is complete when:

- The target repository contains the `triage` and `implementation` skills.
- The target repository contains the two Cloud Factory GitHub workflows.
- The repository has a team-scoped Oz API key stored as the `WARP_API_KEY` Actions secret.
- The Warp team has team GitHub authorization configured so implementation runs can push branches and open pull requests.
- The setup is committed and pushed to the repository's default branch.
- A newly opened test issue triggers triage and receives exactly one triage-state label.
- Applying `Ready to implement` triggers implementation and, for a suitable issue, produces a pull request.

## Important concepts to explain

- **Oz** runs agents and records their runs. Each run consumes Warp credits.
- **Skills** are reusable agent instructions checked into `.agents/skills/`.
- **GitHub Actions** provides the event triggers and repository checkout for this demo.
- **Triage** classifies each new issue as `Ready to implement`, `Ready to spec`, `Needs info`, or `Wait to implement`.
- **Implementation** runs only when the issue receives a ready-to-implement label.
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

If the user is testing installation from a clean state, verify both the local checkout and the remote default branch are clean:

- Search the checkout for existing `.agents/skills/triage`, `.agents/skills/implementation`, `.github/workflows/triage-issues.yml`, `.github/workflows/implement-ready-issues.yml`, `scripts/bootstrap-cloud-factory.sh`, and Cloud Factory README sections.
- Check `gh workflow list --repo "$TARGET_REPO"` for existing `Triage New Issues` or `Implement Ready Issues` workflows.
- Check `gh secret list --repo "$TARGET_REPO"` for an existing `WARP_API_KEY` secret.
- If any are present, explain that the repository is not a clean activation target. Ask whether to continue against the existing setup or create a fresh test repository.

Before changing anything, show the user the flow, explain that automated runs consume credits, and ask whether they want to proceed with installation.

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

#### Create and enable a Warp team when needed

Use `oz whoami` to determine whether the user belongs to the intended Warp team. If they do not have a Warp team, guide them through this setup before continuing:

1. Open Warp and go to **Settings > Teams**.
2. Follow the prompts to create a team and give it a meaningful organization or project name. The creator becomes the team admin.
3. Optionally copy the invite link from **Settings > Teams** and share it with teammates through a secure channel.
4. Have the team admin confirm the team is on a plan that supports cloud agents and Add-on Credits, and that at least 20 credits are available. Do not start automated runs until billing and credit availability are understood.
5. Have a GitHub organization admin install the [Oz by Warp GitHub App](https://github.com/apps/oz-by-warp) and grant it access to the target repository.
6. In Warp, have a team admin go to **Settings > Admin Panel > Platform** and add the GitHub organization under **Enabled GitHub Orgs**. This enables team API-key runs to clone the repository, push branches, and open pull requests.
7. Run `oz whoami` again and verify it shows the intended team before creating team-scoped keys.

A Warp user can belong to only one team at a time. If the user already belongs to a different team, do not create another or switch teams without explaining the impact and receiving explicit approval.

Treat Oz as enabled for this Cloud Factory only after the team exists, the supported plan and credits are confirmed, the Oz by Warp GitHub App can access the repository, the GitHub organization is enabled in the Admin Panel, and `oz whoami` shows the intended team.

Confirm:

- `gh auth status` succeeds for the GitHub account that will create secrets, push workflow files, open issues, and inspect Actions runs.
- GitHub Actions is enabled for the repository.
- Issues are enabled for the repository.
- The repository allows GitHub Actions to create and approve pull requests, or the workflow is configured to use a PAT or GitHub App token with `pull-requests: write`.
- The user belongs to the intended Warp team and can create or request team-scoped resources.
- The Warp team has Add-on Credits available for cloud runs.
- Team GitHub authorization is configured for the target repository.

Explain that a run failing with `insufficient_credits` means a team admin must purchase Add-on Credits in the Oz web app or Warp billing settings. Never claim a credit balance was verified unless a tool actually exposed it.

### 3. Install the skills and workflows

From `TARGET_DIR`, inspect the existing `.agents/skills/` and `.github/workflows/` files first. If the installer would overwrite customized files, show the differences and ask before continuing.

Run the canonical installer from the target repository root. Prefer downloading it to a temporary file before running it so child commands cannot consume the rest of the script from stdin:

```sh
tmp_installer="$(mktemp)"
curl -fsSL https://raw.githubusercontent.com/warpdotdev-demos/cloud-factory-demo/main/scripts/install-cloud-factory.sh -o "$tmp_installer"
bash "$tmp_installer"
rm "$tmp_installer"
```

The installer must add:

- `.agents/skills/triage/SKILL.md`
- `.agents/skills/implementation/SKILL.md`
- `.github/workflows/triage-issues.yml`
- `.github/workflows/implement-ready-issues.yml`

Review the resulting diff. Explain:

- `triage-issues.yml` triggers when an issue is opened.
- `implement-ready-issues.yml` triggers when an issue receives a ready-to-implement label.
- The workflows use `warpdotdev/oz-agent-action@v1`.
- GitHub's token supplies repository permissions; `WARP_API_KEY` authenticates Oz.

Do not silently customize the installed skills. If the repository has special build, test, security, or contribution requirements, offer to add them to the implementation skill and show the proposed changes first.

### 4. Configure Oz authentication safely

The workflows require a repository Actions secret named `WARP_API_KEY`. It must contain a team-scoped Oz API key so the automation is not tied to an individual account.

If the user already has an appropriate team key, have them put it into an environment variable without printing it. Then store it and clear the local variable:

```sh
printf '%s' "$WARP_API_KEY" | gh secret set WARP_API_KEY --repo "$TARGET_REPO"
unset WARP_API_KEY
```

If they need a key, have them use **Settings > Cloud platform > Oz Cloud API Keys** in Warp or the Oz web app, create a key named `cloud-factory-github-actions`, select `Team`, choose an expiration that follows the team's rotation policy, and copy its one-time value into `WARP_API_KEY` without printing it.

If the installed Oz CLI supports team-scoped API-key creation, it is acceptable to create the key with `oz api-key create` instead. First confirm `oz whoami` shows the intended team, then use the team-scoped form exposed by `oz api-key create --help`. When using JSON output, the one-time secret value is currently in the `raw_api_key` field. Pipe or store only that value directly into the GitHub secret.

After creating a key by any method, verify metadata only, never the raw key value:

```sh
oz api-key list --output-format json
```

The key used for automation must show `scope: "Team"`. Plain `oz api-key create` may create a `Personal` key in some CLI versions; do not use that key for this setup. Never fall back to a personal key. If the user cannot create a team key or configure team GitHub authorization, stop and ask a team admin to complete those steps.

Never print, read back, commit, or write the key to a repository file. Confirm only that the `WARP_API_KEY` secret name exists using `gh secret list --repo "$TARGET_REPO"`.

An optional `WARP_AGENT_PROFILE` repository variable may select a preconfigured team Oz Agent Profile. Do not create or set it to a personal profile.

### 5. Review and activate

Before activation, review:

- The complete git diff
- Workflow permissions
- The team-scoped API key, team GitHub authorization, and any team Agent Profile
- GitHub Actions workflow permissions, especially whether Actions can create and approve pull requests
- The four triage labels and routing behavior
- Expected credit consumption
- The fact that implementation agents can push branches and open PRs

Do not commit or push without explicit user approval. The workflows only activate after they are present on the default branch. If the user prefers review first, create a setup branch and pull request, then explain that automation begins after merge.

After activation, confirm both workflows appear with:

```sh
gh workflow list --repo "$TARGET_REPO"
```

### 6. Test triage first

Ask permission before creating a test issue because opening it triggers a billable cloud run.

Create one small, clear, safe issue that is relevant to the target repository. Avoid an issue likely to cause destructive, security-sensitive, or broad changes. Capture its URL.

Watch the `Triage New Issues` workflow and inspect its result with `gh run list` and `gh run view`. Confirm:

- The workflow ran successfully.
- Oz posted a triage-started comment and final result.
- Exactly one triage-state label was applied.
- The Oz run is visible in the Oz Runs page.

If triage does not choose `Ready to implement`, do not override the label merely to force implementation. Explain the result and either improve the test issue with the user or create a separate clearly implementable test issue with permission.

If triage applies `Ready to implement` but no implementation workflow starts, check whether the label was applied by `github-actions` using GitHub's default token. GitHub does not trigger most new workflow runs from events created by `GITHUB_TOKEN`, so a label applied by the triage workflow may not fire the separate `issues.labeled` implementation workflow. For a smoke test, explain this limitation and ask before manually removing and re-adding the label as a human user. For a durable setup, recommend changing the workflow design to use a PAT or GitHub App token for label writes, dispatch the implementation workflow explicitly, or combine orchestration so implementation is not dependent on a suppressed follow-up event.

### 7. Test implementation

Before allowing a `Ready to implement` label to trigger implementation, remind the user that this starts another billable run that may push a branch and open a PR.

Watch the `Implement Ready Issues` workflow. Confirm:

- The implementation run starts.
- The agent posts progress to the issue.
- The agent validates its change.
- A pull request is opened and linked from the issue.

Do not merge the test PR. Present the PR, validation results, Oz run link, and any failures for human review.

## Troubleshooting

- **Workflow is missing:** Confirm both workflow files are committed to the default branch and Actions is enabled.
- **`WARP_API_KEY` error:** Confirm the repository secret exists and the key is valid. Never expose its value.
- **Team key cannot write to GitHub:** Confirm team GitHub authorization is configured for the target repository.
- **`insufficient_credits`:** Direct a team admin to purchase Add-on Credits in Oz or Warp billing settings, then retry.
- **Permission failure:** Compare the workflow's `permissions` block with the attempted action and check repository or organization Actions policy.
- **PR creation blocked:** Enable repository or organization Actions settings that allow GitHub Actions to create and approve pull requests, or configure a PAT/GitHub App token with pull request write permission.
- **Skill not found:** Confirm the exact installed paths and that the triage workflow references `triage`.
- **Implementation does not trigger:** Confirm the issue received `Ready to implement`, `ready-to-implement`, or `ready to implement`. If triage added the label from `github-actions`, account for GitHub's `GITHUB_TOKEN` event suppression.
- **Agent cannot build the project:** Improve the repository's setup instructions or implementation skill, or update the GitHub Actions runner setup so the required toolchain is available.

## Guardrails

- Never reveal, print, or commit API keys or other secrets.
- Never create or substitute personal Oz API keys, secrets, or Agent Profiles for this setup.
- Never activate workflows, open a test issue, trigger implementation, or push to the default branch without explaining the consequence and receiving explicit approval.
- Never weaken repository protections or broaden workflow permissions just to make the demo pass.
- Never force ambiguous or risky issues into `Ready to implement`.
- Never merge an implementation PR automatically.
- Prefer the canonical installer and templates over manually recreating them.
- Keep the user oriented: after each stage, summarize what changed, what will happen next, and whether the next action triggers a billable run.
