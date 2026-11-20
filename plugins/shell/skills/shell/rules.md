# Shell: rules

Rules for shell scripts, from common practice and what went wrong before. In an existing project, follow the conventions it already uses and report a difference instead of rewriting; these rules decide new scripts.

How to change this file (see CONTRIBUTING.md of this repository):
- **Add a rule:** copy an item, give it the next number in its group, write the rule, why it exists and how to check it. A new rule is a MINOR version.
- **Change a rule:** edit it in place and keep its ID, so old reviews still point at the right rule. A rule that now says the opposite is a MAJOR version; clearer wording is a PATCH.
- **Retire a rule:** keep its ID and heading, replace the text with `(retired in <version>: <reason>)`, and never reuse the number. A retired rule is a MAJOR version.

## Safety (SH)

- **SH-1** Start with `set -euo pipefail` (`set -eu` in POSIX `sh`, where `pipefail` is not portable), unless the project documents another convention, and handle expected failures on purpose (`if`, or `|| true` with a comment).
  Why: without it a failed step continues silently.
  Check: `scripts/check-shell.py` finds the line before the first command; every `|| true` has a comment.

- **SH-2** Quote every expansion (`"$var"`, `"$@"`); use arrays for argument lists.
  Why: an unquoted path with a space or a glob breaks, or deletes the wrong files.
  Check: `shellcheck` reports no SC2086.

- **SH-3** Guard every destructive command (`rm -rf`, `git push`, `git reset`) against an empty or unexpected variable (`"${dir:?}"`).
  Why: `rm -rf "$dir/"` with an empty `dir` deletes from the root.
  Check: each destructive command uses `:?` or an explicit test before it.

- **SH-4** Never print a secret, run `set -x` around one or pass it as a command-line argument; read it from the environment or the secret store.
  Why: logs and process lists are readable by others.
  Check: search for `set -x` and for secret variables inside `echo` or arguments.

## Portability (SHP)

- **SHP-1** Write for the shell where the script runs. For Bash 3.2 (Apple's `/bin/bash`), avoid associative arrays, `mapfile`, `${var,,}` and `declare -n`.
  Why: they fail only on the machine that matters.
  Check: the shebang matches the target; run `bash -n` with that Bash. Under `set -u`, Bash before 4.4 treats an empty array as unbound: expand it as `${arr[@]+"${arr[@]}"}`.

- **SHP-2** Resolve paths from the script's own location (`"$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"` in Bash; `$0` is wrong when the script is sourced), not from the caller's folder.
  Why: hooks and pipelines run from other working directories.
  Check: no relative paths that assume the current directory.

- **SHP-3** Create temporary files with `mktemp` and remove them with `trap '…' EXIT`.
  Why: fixed paths collide between parallel runs and leave data behind.
  Check: `scripts/check-shell.py` finds no fixed `/tmp/<name>` path.

## Interface (SHI)

- **SHI-1** Diagnostics go to stderr, data to stdout; exit with distinct, documented codes for distinct failures.
  Why: callers parse stdout and branch on the exit code.
  Check: the header lists the exit codes; error messages use `>&2`.

- **SHI-2** Keep inline pipeline scripts to a few lines; anything with logic goes into a versioned script file.
  Why: inline YAML scripts cannot be linted, tested or reviewed properly.
  Check: no inline step longer than about ten lines.
