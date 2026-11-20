---
name: shell
description: "Rules for shell scripts: strict mode, quoting, guarded destructive commands, secrets, portability across Bash versions and sh, temporary files, exit codes and short inline pipeline steps. Use when writing, changing, reviewing or fixing a Bash or POSIX sh script, a git hook, an installer or the shell inside a pipeline step; recognise it by *.sh files, a #!/bin/bash, #!/usr/bin/env bash or #!/bin/sh shebang, or a run: or script: block of shell. Triggers: shell, shell script, Bash, sh, zsh, POSIX sh, shellcheck, git hook. Not for logic big enough to need data structures and tests (python skill), or the pipeline YAML around a step (azure-devops, github-actions or jenkins skill)."
license: MIT
metadata:
  version: "1.0.0"
  aliases: "bash, sh, zsh, posix sh"
---

# Shell

What is particular to shell scripts. A script that runs inside a pipeline also follows the pipeline's skill (`azure-devops`, `github-actions` or `jenkins`), if installed.

## When

- Use for `*.sh`, scripts with a shell shebang, git hooks, installers and inline pipeline steps.
- Not for logic big enough to need data structures and tests: write it in Python (`python`, if installed).

## How to work

1. Find where the script really runs and with which shell: Apple's `/bin/bash` is still 3.2, a Linux agent has Bash 5, a container may have only `sh`. Read the shebang and the pipeline's agent image (SHP-1).
2. Read the repository's existing scripts and follow their conventions (options, logging, exit codes).
3. Verify: `bash -n` and `shellcheck` (when installed) on every changed script, the skill's own check, then run it against a temporary folder, never against a live target:
   ```bash
   python3 <this skill's folder>/scripts/check-shell.py <changed files or folders>
   ```

## Rules

Read [rules.md](rules.md) and follow every rule. Cite a rule by its ID and this skill's version when you apply or break it, for example "breaks SH-3 (shell 1.0.0)".
