#!/usr/bin/env python3
"""Check shell scripts for strict mode (SH-1) and fixed temporary paths (SHP-3).

What it does
    Reads every shell script under the paths given (a *.sh, *.bash or *.ksh
    file, or any file whose first line is a sh, bash, ksh or zsh shebang) and
    reports, with file and line:
    - SH-1: no `set -euo pipefail` (or, in a #!/bin/sh script, `set -eu`)
      before the first command. `set -e -u -o pipefail`, `set -o errexit
      -o nounset -o pipefail` and zsh's `setopt err_exit no_unset pipe_fail`
      count too; several lines add up.
    - SHP-3: a fixed path under /tmp or /var/tmp (`/tmp/build.log`), outside
      a comment. `mktemp` lines and `$TMPDIR` paths are fine.

Why it exists
    These two rules have one right answer, so a script checks them instead of
    an agent reading by eye (the skill's step "Verify" runs it); shellcheck
    covers quoting (SH-2). The rules and their reasons are in ../rules.md.

How to run
    python3 check-shell.py [PATH ...]
    PATH is a file or a folder (searched recursively, skipping .git,
    node_modules, .venv and venv); the default is the current folder.
    Python 3.9 or newer, standard library only.
    Exit code: 0 nothing found, 1 findings printed, 2 a path does not exist
    or a file could not be read (printed on stderr; the other files are still
    checked).

What can go wrong
    - SH-1 allows "unless the project documents another convention": a
      project that does so gets findings here; say so in the report instead of
      changing every script.
    - A script meant to be sourced (a library of functions) should not set
      options for its caller; it is reported, and the report says why it is
      fine.
    - The reader is line based: a /tmp path inside a heredoc of data is
      reported too.
"""

import argparse
import re
import sys
from pathlib import Path

SKIPPED_DIRS = {".git", "node_modules", ".venv", "venv"}
SUFFIXES = {".sh", ".bash", ".ksh"}
SHEBANG_RE = re.compile(r"^#!\s*(?:/usr/bin/env\s+)?(?:\S*/)?(sh|bash|ksh|zsh|dash)\b")

# The option letters and long names that make up strict mode.
LETTERS = {"e": "errexit", "u": "nounset"}
SET_RE = re.compile(r"^\s*set\s+(.*)$")
# zsh spells the same options with setopt (case and underscores ignored).
SETOPT_RE = re.compile(r"^\s*setopt\s+(.*)$")
SETOPT_NAMES = {"errexit": "errexit", "nounset": "nounset", "pipefail": "pipefail"}
# A comment starts at # at the line start or after a space; ${#arr[@]} is not one.
COMMENT_RE = re.compile(r"(^|\s)#.*$")
# A fixed path under a temporary folder: /tmp/name, not /tmp alone or $TMPDIR.
FIXED_TMP_RE = re.compile(r"(?<![\w$}/.-])/(?:var/)?tmp/[\w.-]+")


def shell_of(path, first_line):
    """Return the shell name ('sh', 'bash'...) or None when the file is not a script."""
    match = SHEBANG_RE.match(first_line)
    if match:
        return match.group(1)
    if path.suffix in SUFFIXES:
        return "bash" if path.suffix == ".bash" else "sh" if path.suffix == ".sh" else path.suffix[1:]
    return None


def options_of(arguments):
    """Return the set of long option names a `set` line turns on."""
    found = set()
    words = COMMENT_RE.sub("", arguments).split()
    i = 0
    while i < len(words):
        word = words[i]
        if word == "-o" and i + 1 < len(words):
            found.add(words[i + 1])
            i += 2
            continue
        if word.startswith("-") and not word.startswith("--"):
            letters = word[1:]
            # -euo pipefail: the o takes the next word as its option name.
            if letters.endswith("o") and i + 1 < len(words):
                found.add(words[i + 1])
                letters = letters[:-1]
                i += 1
            found.update(LETTERS[c] for c in letters if c in LETTERS)
        i += 1
    return found


def check_text(text, shell):
    """Return [(line, message)] for one script."""
    lines = text.splitlines()
    findings = []
    # SH-1: options seen before the first command that is not `set` itself.
    wanted = {"errexit", "nounset"} | ({"pipefail"} if shell != "sh" and shell != "dash" else set())
    seen, strict_line = set(), None
    for number, line in enumerate(lines, 1):
        stripped = line.strip()
        if number == 1 and stripped.startswith("#!") or not stripped or stripped.startswith("#"):
            continue
        match = SET_RE.match(line)
        setopt = SETOPT_RE.match(line)
        if match or setopt:
            if match:
                seen |= options_of(match.group(1))
            else:
                names = {w.lower().replace("_", "") for w in COMMENT_RE.sub("", setopt.group(1)).split()}
                seen |= {SETOPT_NAMES[n] for n in names if n in SETOPT_NAMES}
            if wanted <= seen:
                strict_line = number
                break
            continue
        break
    if strict_line is None:
        hint = "set -eu" if "pipefail" not in wanted else "set -euo pipefail"
        findings.append((1, f"SH-1 no `{hint}` before the first command"))
    # SHP-3: fixed temporary paths, outside comments and mktemp templates.
    for number, line in enumerate(lines, 1):
        code = COMMENT_RE.sub("", line)
        if "mktemp" in code:
            continue
        for match in FIXED_TMP_RE.finditer(code):
            findings.append((number, f"SHP-3 fixed temporary path {match.group(0)}; use mktemp"))
    return findings


def candidate_files(paths):
    # A folder means every file below it that could be a script.
    for path in paths:
        if path.is_dir():
            for file in sorted(path.rglob("*")):
                if file.is_file() and not SKIPPED_DIRS.intersection(file.relative_to(path).parts):
                    yield file, False
        else:
            yield path, True


def main(argv=None):
    parser = argparse.ArgumentParser(description="Report shell scripts without strict mode (SH-1) or with fixed /tmp paths (SHP-3).")
    parser.add_argument("paths", nargs="*", type=Path, default=[Path(".")], help="files or folders (default: .)")
    args = parser.parse_args(argv)

    found = broken = 0
    # A path that does not exist is an error, not "nothing found".
    for path in args.paths:
        if not path.exists():
            print(f"{path}: no such file or folder", file=sys.stderr)
            broken += 1
    for path, named in candidate_files(p for p in args.paths if p.exists()):
        # Read as text; a binary file found in a folder is simply not a script.
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            if named:
                print(f"{path}: cannot check: not UTF-8 text", file=sys.stderr)
                broken += 1
            continue
        except OSError as error:
            print(f"{path}: cannot check: {error}", file=sys.stderr)
            broken += 1
            continue
        shell = shell_of(path, text.split("\n", 1)[0])
        # A file named on the command line is checked as sh even without a shebang.
        if shell is None:
            if not named:
                continue
            shell = "sh"
        for line, message in check_text(text, shell):
            print(f"{path}:{line}: {message}")
            found += 1

    # Exit 2 wins over 1: an unchecked file means the result is incomplete.
    if broken:
        return 2
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
