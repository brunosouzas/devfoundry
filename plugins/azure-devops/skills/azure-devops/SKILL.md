---
name: azure-devops
description: "Rules for Azure Pipelines YAML: naming of variable groups and variables, templates and their callers, deployment jobs and environments, pinned template refs, secrets and Key Vault groups, branch control, release triggers, approvals and pinned agent images. Use when writing, changing, reviewing or debugging an azure-pipelines.yml, a pipeline template, its variable groups, environments and checks, or the scripts a pipeline step runs; recognise it by azure-pipelines.yml, a templates/ folder of stages, jobs or steps, or resources.repositories entries. Triggers: Azure DevOps, Azure Pipelines, ADO, azure-pipelines.yml, variable group, pipeline template, service connection. Not for GitHub Actions workflows (github-actions skill), Jenkinsfiles (jenkins skill), or the shell or Python a step runs on its own (shell or python skill)."
license: MIT
metadata:
  version: "1.0.0"
  aliases: "azure pipelines, ado, azure devops pipelines"
---

# Azure DevOps

What is particular to Azure Pipelines. The branches, releases and promotion a pipeline implements come from the repository's delivery process; this skill says how to write them safely. Scripts called by a step also follow `shell` or `python`, if installed.

## When

- Use for pipeline YAML, templates, variable groups and their variables, environments, checks and approvals.
- Not for choosing a branch strategy or a promotion path: the repository's delivery process decides them. Not for GitHub Actions: `github-actions`, if installed.

## How to work

1. Find every caller of a template you change (`template:` references in this and other repositories) before changing its parameters, and compile each one after the change (ADO-2, ADO-6).
2. Know when each value exists: `${{ }}` is resolved when the template expands, `$[ ]` and `$( )` at runtime. A runtime value is not available to a compile-time condition.
3. Map triggers, `condition:` and environments to each step that publishes or deploys, before and after the change.
4. Run the skill's check on the changed YAML (ADO-5, ADOD-2, ADOD-3):
   ```bash
   python3 <this skill's folder>/scripts/check-pipelines.py <changed files or folders>
   ```
5. Verify: the YAML editor's "Validate", or a run on the change branch with deploy stages kept off. Report a static check and a platform run separately: only a run proves expansion, permissions and deployment.

## Rules

Read [rules.md](rules.md) and follow every rule. A rule marked `(locked)` protects secrets: a project's own convention never overrides it. Cite a rule by its ID and this skill's version when you apply or break it, for example "breaks ADOS-2 (azure-devops 1.0.0)".
