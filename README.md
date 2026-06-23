# Cloud Factory Demo

This repository is the canonical source for a simple cloud factory: a set of agent skills and GitHub Actions workflows for moving work from an incoming issue to a verified change.

The factory is organized around six stages:

- **Triage** — classify incoming issues, determine implementation readiness, and route work to the right next step.
- **Specking** — turn ambiguous or broad requests into product and technical specs with clear behavior, constraints, and validation criteria.
- **Implementation** — use the approved issue or spec context to make the code change, validate it, and open a pull request.
- **Code review** — review pull requests for correctness, maintainability, security, and alignment with the issue or spec.
- **Verification** — confirm the merged or proposed change satisfies the original request and passes the required checks.
- **Monitoring** — watch outcomes after changes land, surface regressions, and feed new findings back into triage.

## Included skills

- `.agents/skills/Triage/SKILL.md` — triages issue-tracker issues and applies exactly one implementation-readiness label.
- `.agents/skills/implementation/SKILL.md` — implements a ready issue, validates the change, opens a PR, and reports progress back to the original issue.

## Included GitHub Actions workflows

- `.github/workflows/triage-issues.yml` — runs Oz triage when a new GitHub issue is opened.
- `.github/workflows/implement-ready-issues.yml` — runs Oz implementation when an issue receives a `Ready to implement` label.

## Installing into another repository

Consumers can install the skills from this canonical repo with the skills CLI:

```bash
npx skills install warpdotdev-demos/cloud-factory-demo --skill Triage --skill implementation --agent warp --yes
```

If your `skills` CLI version uses `add` instead of `install`, use:

```bash
npx skills add warpdotdev-demos/cloud-factory-demo --skill Triage --skill implementation --agent warp --yes
```

Workflow templates can be copied from `.github/workflows/` into the consuming repository. The workflows expect a `WARP_API_KEY` GitHub Actions secret.

## Default implementation

The default implementation models each factory stage as an agent skill and runs those agents on the Oz platform. In that setup, issue tracker events, labels, pull requests, and other repository signals can trigger Oz cloud agents to perform the appropriate stage of work and write progress back to the source system.

## Portable design

Although the default implementation targets Oz, the factory pattern is platform-independent. The same stages can be adapted to other coding-agent platforms by replacing the trigger mechanism, runtime, and platform-specific instructions while keeping the skill boundaries and handoff contracts intact.

## License

MIT
