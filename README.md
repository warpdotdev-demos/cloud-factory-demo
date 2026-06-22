# Cloud Factory Demo

This repository describes a simple cloud factory: a set of agent skills and workflows for moving work from incoming issue to verified change.

The factory is organized around six stages:

- **Triage** — classify incoming issues, determine implementation readiness, and route work to the right next step.
- **Specking** — turn ambiguous or broad requests into product and technical specs with clear behavior, constraints, and validation criteria.
- **Implementation** — use the approved issue or spec context to make the code change, validate it, and open a pull request.
- **Code review** — review pull requests for correctness, maintainability, security, and alignment with the issue or spec.
- **Verification** — confirm the merged or proposed change satisfies the original request and passes the required checks.
- **Monitoring** — watch outcomes after changes land, surface regressions, and feed new findings back into triage.

## Default implementation

The default implementation models each factory stage as an agent skill and runs those agents on the Oz platform. In that setup, issue tracker events, labels, pull requests, and other repository signals can trigger Oz cloud agents to perform the appropriate stage of work and write progress back to the source system.

## Portable design

Although the default implementation targets Oz, the factory pattern is platform-independent. The same stages can be adapted to other coding-agent platforms by replacing the trigger mechanism, runtime, and platform-specific instructions while keeping the skill boundaries and handoff contracts intact.

## License

MIT
