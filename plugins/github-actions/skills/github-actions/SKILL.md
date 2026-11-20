---
name: github-actions
description: "Rules for GitHub Actions workflows: actions and reusable workflows pinned by commit SHA, least-privilege permissions per job, no untrusted input in run or script, pull_request instead of pull_request_target, checkout credentials, secrets and environments, app and OIDC tokens, pinned runners, timeouts, required check names, and release and deploy jobs. Use when writing, changing, reviewing or debugging a workflow under .github/workflows/, a reusable workflow (on: workflow_call), a composite action (action.yml) or a job's secrets and environments; recognise it by .github/workflows/*.yml or an action.yml. Triggers: GitHub Actions, GitHub workflow, workflow YAML, reusable workflow, composite action, GITHUB_TOKEN, actions/checkout, actionlint. Not for Azure Pipelines (azure-devops skill), Jenkinsfiles (jenkins skill), or the shell or Python a step runs on its own (shell or python skill)."
license: MIT
metadata:
  version: "1.0.0"
  aliases: "github workflows, gha, github actions workflows"
---

# GitHub Actions

What is particular to GitHub Actions workflows and actions. The branches, releases and environments a workflow implements come from the repository's delivery process; this skill says how to write them safely. Scripts a step calls also follow `shell` or `python`, if installed.

## When

- Use for workflows in `.github/workflows/`, reusable workflows, composite actions, their permissions, secrets, environments and triggers.
- Not for Azure Pipelines or Jenkins: `azure-devops` or `jenkins`, if installed. Not for choosing a branch strategy or a release process.

## How to work

1. Read the trigger first (`on:`): who can start the run, with which token and which secrets. A pull request from a fork gets a read-only `GITHUB_TOKEN` and no secrets under `pull_request`; under `pull_request_target` it gets both (GHAS-4).
2. For a reusable workflow, read it at the ref the caller pins (`git show <tag>:.github/workflows/<file>`), never from a local checkout's branch, and list every caller before changing its inputs, secrets or outputs (GHA-4).
3. Give each job its own `permissions:`; the workflow's default is `{}` or `contents: read` (GHAS-2).
4. Pass every expression a user can influence through `env:` and quote it in the script (GHAS-3).
5. Run the skill's check and actionlint on the workflows and the repository's own actions (GHA-5); leave out `.github/actions` when there is none:
   ```bash
   python3 <this skill's folder>/scripts/check-workflows.py .github/workflows .github/actions
   ```
6. Verify: a run on the pull request for checks, and for a release or deploy job a run on a scratch branch or tag that the environment refuses. Report a static check and a GitHub run separately: only a run proves permissions, environments and secrets.

## Rules

Read [rules.md](rules.md) and follow every rule. A rule marked `(locked)` protects secrets or the repository: a project's own convention never overrides it. Cite a rule by its ID and this skill's version when you apply or break it, for example "breaks GHAS-3 (github-actions 1.0.0)".
