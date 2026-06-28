# Cloud Factory Demo

This repository is the canonical source for a simple cloud factory: a set of agent skills and GitHub Actions workflows for moving work from an incoming issue to a verified change.

The factory is organized around six stages:

- **Triage** — classify incoming issues, determine implementation readiness, and route work to the right next step.
- **Spec'ing** — turn ambiguous or broad requests into checked-in `PRODUCT.md` and `TECH.md` specs with clear behavior, constraints, and validation criteria.
- **Implementation** — use the approved issue or spec context to make the code change, validate it, and open a pull request.
- **Code review** — review pull requests for correctness, maintainability, security, and alignment with the issue or spec.
- **Verification** — confirm the merged or proposed change satisfies the original request and passes the required checks.
- **Monitoring** — watch outcomes after changes land, surface regressions, and feed new findings back into triage.

## Included skills

- `.agents/skills/triage/SKILL.md` — triages issue-tracker issues and applies exactly one implementation-readiness label.
- `.agents/skills/spec/SKILL.md` — coordinates spec work for issues labeled ready-to-spec by delegating to the common `write-product-spec` and `write-tech-spec` skills, then opening a specs PR containing `PRODUCT.md` and `TECH.md`.
- `.agents/skills/write-product-spec/SKILL.md` — installed from `warpdotdev/common-skills`; writes the product spec artifact.
- `.agents/skills/write-tech-spec/SKILL.md` — installed from `warpdotdev/common-skills`; writes the technical spec artifact after `PRODUCT.md`.
- `.agents/skills/implementation/SKILL.md` — implements a ready issue, validates the change, opens a PR, and reports progress back to the original issue.
- `.agents/skills/oz-cloud-factory-demo/SKILL.md` — walks a user who is new to Oz through installing, configuring, activating, and testing the triage-to-implementation factory in a repository of their choice.

## Included GitHub Actions workflows

This repo keeps workflow templates in `templates/github/workflows/` so they can be copied into consuming repositories:

- `templates/github/workflows/triage-issues.yml` — runs Oz triage when a new GitHub issue is opened.
- `templates/github/workflows/spec-ready-issues.yml` — runs Oz spec work when an issue receives a `Ready to spec` label and opens a PR with `PRODUCT.md` and `TECH.md`.
- `templates/github/workflows/implement-ready-issues.yml` — runs Oz implementation when an issue receives a `Ready to implement` label.

The `.github/workflows/` directory contains the same workflows for this repo to exercise and document the templates.

## Installing into another repository

From the root of a consuming repository, run:

```bash
tmp_installer="$(mktemp)"
curl -fsSL https://raw.githubusercontent.com/warpdotdev-demos/cloud-factory-demo/main/scripts/install-cloud-factory.sh -o "$tmp_installer"
bash "$tmp_installer"
rm "$tmp_installer"
```

The installer:

1. Installs the `triage`, `spec`, and `implementation` skills from this canonical repo with `npx skills add`.
2. Installs `write-product-spec` and `write-tech-spec` from `warpdotdev/common-skills`.
3. Copies the workflow templates from `templates/github/workflows/` into `.github/workflows/` in the consuming repository.

The installed workflows expect a `WARP_API_KEY` GitHub Actions secret.

If you only want to install the skills without copying workflows, run:

```bash
npx skills add warpdotdev-demos/cloud-factory-demo --skill triage --skill spec --skill implementation --agent warp --yes
npx skills add warpdotdev/common-skills --skill write-product-spec --skill write-tech-spec --agent warp --yes
```

To install the guided setup skill, run:

```bash
npx skills add warpdotdev-demos/cloud-factory-demo --skill oz-cloud-factory-demo --agent warp --yes
```

Then invoke `oz-cloud-factory-demo` with a GitHub repository URL, `owner/repo`, or local checkout path. It explains each step, uses the installer above, configures Oz authentication safely, and walks through billable test-run checkpoints before activating automation.

## Default implementation

The default implementation models each factory stage as an agent skill and runs those agents on the Oz platform (https://docs.warp.dev/agent-platform/cloud-agents/overview/). In that setup, issue tracker events, labels, pull requests, and other repository signals can trigger Oz cloud agents to perform the appropriate stage of work and write progress back to the source system.

## Portable design

Although the default implementation targets Oz, the factory pattern is platform-independent. The same stages can be adapted to other coding-agent platforms by replacing the trigger mechanism, runtime, and platform-specific instructions while keeping the skill boundaries and handoff contracts intact.

## License

MIT
