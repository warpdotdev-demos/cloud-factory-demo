#!/usr/bin/env bash

# Install Cloud Factory skills and GitHub Actions workflow templates into a consuming repository.
# Run this from the root of the consuming repository.

REPO="${CLOUD_FACTORY_REPO:-warpdotdev-demos/cloud-factory-demo}"
REF="${CLOUD_FACTORY_REF:-main}"
RAW_BASE="https://raw.githubusercontent.com/${REPO}/${REF}"

if ! git rev-parse --show-toplevel >/dev/null 2>&1; then
  printf 'Run this script from inside the consuming Git repository.\n' >&2
  exit 1
fi

if ! command -v npx >/dev/null 2>&1; then
  printf 'npx is required to install Cloud Factory skills. Install Node.js/npm and retry.\n' >&2
  exit 1
fi

# Keep npx from consuming the rest of this script when users install with
# `curl ... | bash`.
npx skills add "${REPO}" --skill triage --skill spec --skill implementation --agent warp --yes < /dev/null
npx skills add warpdotdev/common-skills --skill write-product-spec --skill write-tech-spec --skill validate-changes-match-specs --agent warp --yes < /dev/null

mkdir -p .github/workflows
curl -fsSL "${RAW_BASE}/templates/github/workflows/triage-issues.yml" -o .github/workflows/triage-issues.yml
curl -fsSL "${RAW_BASE}/templates/github/workflows/spec-ready-issues.yml" -o .github/workflows/spec-ready-issues.yml
curl -fsSL "${RAW_BASE}/templates/github/workflows/implement-ready-issues.yml" -o .github/workflows/implement-ready-issues.yml

printf 'Installed Cloud Factory skills and GitHub Actions workflow templates from %s@%s.\n' "${REPO}" "${REF}"
printf 'Ensure the WARP_API_KEY GitHub Actions secret is configured before enabling these workflows.\n'
