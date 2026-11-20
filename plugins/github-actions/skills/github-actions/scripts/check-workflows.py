#!/usr/bin/env python3
"""Check GitHub Actions workflows and composite actions for the rules with one right answer.

What it does
    Reads every *.yml and *.yaml file under the paths given and reports, with
    file and line:
    - GHAS-1: a `uses:` of another repository not pinned by a 40-character
      commit SHA (a `docker://` image needs an `@sha256:` digest);
    - GHAS-2: `write-all`; a write permission at the workflow level; a job
      without `permissions:` when the workflow sets none;
    - GHAS-3: `github.event.*` text fields, `github.head_ref` or `inputs.*`
      inside `${{ }}` in a `run:` or `script:` value;
    - GHAS-4: a `pull_request_target` trigger;
    - GHAS-5: an `actions/checkout` step without `persist-credentials: false`;
    - GHAS-6: `secrets: inherit`, or `${{ secrets.* }}` inside a `run:` or
      `script:` value;
    - GHA-1: a `runs-on:` that names a `-latest` image (scalar or list);
    - GHA-2: a job without `timeout-minutes:` (jobs that call a reusable
      workflow are exempt: GitHub does not allow it there).
    A file with top-level `jobs:` is a workflow; one with top-level `runs:` is
    an action (GHAS-1 and GHAS-3 only). Other YAML files are skipped.

Why it exists
    These rules have one right answer, so a script checks them instead of an
    agent reading YAML by eye (the skill's step 5 runs it, next to
    actionlint, which checks syntax and expressions but not these). The rules
    and their reasons are in ../rules.md.

How to run
    python3 check-workflows.py [PATH ...]
    PATH is a file or a folder (searched recursively for *.yml and *.yaml,
    skipping .git and node_modules); the default is .github/workflows.
    Python 3.9 or newer, standard library only (no YAML library: see below).
    Exit code: 0 nothing found, 1 findings printed, 2 a path does not exist
    or a file could not be read (printed on stderr; the other files are still
    checked).

What can go wrong
    - The reader is line based and understands block-style YAML as workflows
      are written (two-space or any consistent indentation). Flow-style maps
      (`permissions: { contents: write }`) are read on their line; anchors
      and aliases are not followed. Quoted keys ("on":) are read.
    - GHA-1 reads the runs-on value only: `runs-on: ${{ matrix.os }}` with
      `os: [ubuntu-latest]` in the matrix is not reported; read the matrix.
    - GHAS-3 is strict on purpose: `inputs.*` of a workflow_dispatch boolean is
      harmless, and is reported anyway; moving it to `env:` costs one line.
    - GHAS-5 has an exception (a job that pushes with the checkout's token);
      the finding stays, and the comment the rule asks for explains it.
"""

import argparse
import re
import sys
from pathlib import Path

SKIPPED_DIRS = {".git", "node_modules"}

# A key may be quoted ("on": is common, to keep YAML 1.1 from reading it as true).
KEY_RE = re.compile(r"^(?P<indent> *)(?P<dash>- +)?[\"']?(?P<key>[\w.-]+)[\"']?:(?:\s+(?P<value>.*))?$")
SHA_RE = re.compile(r"@[0-9a-f]{40}$")
BLOCK_MARKERS = ("|", ">", "|-", ">-", "|+", ">+")

# GHAS-3: expressions whose value someone outside the maintainers can choose.
UNTRUSTED_RE = re.compile(
    r"\$\{\{[^}]*?\b("
    r"github\.head_ref"
    r"|inputs\.[\w-]+"
    r"|github\.event\.[\w.*\[\]'-]*?\b(title|body|message|ref|label|default_branch|page_name|head_branch|display_title)\b"
    r"|github\.event\.[\w.*\[\]'-]*?\b(author|committer|pusher)\.(name|email|username)\b"
    r"|github\.event\.[\w.*\[\]'-]*?\bhead\.repo\.(full_name|name)\b"
    r")"
)

# GHAS-6: a secret written into the script text.
SECRET_IN_SCRIPT_RE = re.compile(r"\$\{\{[^}]*?\bsecrets\.[\w-]+")


def unquote(value):
    # The scalar without its trailing comment and quotes.
    value = (value or "").split(" #", 1)[0].strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def indent_of(line):
    # Spaces before the first character: YAML's nesting.
    return len(line) - len(line.lstrip(" "))


def significant(lines):
    # Blank lines and comments say nothing about structure.
    """Yield (number, line, match) for lines that are not blank or comments."""
    for number, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            yield number, line, KEY_RE.match(line)


def block_of(lines, start):
    """Return the (number, line) pairs indented under line `start` (1-based)."""
    base = indent_of(lines[start - 1])
    # A list item's keys sit at the dash's indent + 2.
    match = KEY_RE.match(lines[start - 1])
    if match and match.group("dash"):
        base += len(match.group("dash")) - 1
    block = []
    for number in range(start + 1, len(lines) + 1):
        line = lines[number - 1]
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if indent_of(line) <= base:
            break
        block.append((number, line))
    return block


def top_level(lines):
    """Return {key: line number} of the keys at column 0."""
    keys = {}
    for number, line, match in significant(lines):
        if match and not match.group("indent") and not match.group("dash"):
            keys.setdefault(match.group("key"), number)
    return keys


def check_uses(lines):
    """GHAS-1: every remote uses: pinned by full SHA."""
    findings = []
    for number, line, match in significant(lines):
        if not match or match.group("key") != "uses":
            continue
        value = unquote(match.group("value"))
        if value.startswith("./") or not value:
            continue
        if value.startswith("docker://"):
            if "@sha256:" not in value:
                findings.append((number, f"GHAS-1 {value} is not pinned by digest (@sha256:...)"))
        elif not SHA_RE.search(value):
            findings.append((number, f"GHAS-1 {value} is not pinned by a full commit SHA"))
    return findings


def check_scripts(lines):
    """GHAS-3: untrusted expressions inside run: or script: values."""
    findings = []
    for number, line, match in significant(lines):
        if not match or match.group("key") not in ("run", "script"):
            continue
        value = match.group("value") or ""
        body = [(number, value)]
        if value.strip() in BLOCK_MARKERS:
            body = block_of(lines, number)
        for line_number, text in body:
            for found in UNTRUSTED_RE.finditer(text):
                findings.append((line_number, f"GHAS-3 {found.group(1)} is interpolated into a script; pass it through env:"))
            for found in SECRET_IN_SCRIPT_RE.finditer(text):
                findings.append((line_number, f"GHAS-6 {found.group(0)[3:].strip()} is written into a script; pass it through env:"))
    return findings


def jobs_of(lines, jobs_line):
    """Return [(job id, line number, [(number, line)])] for the jobs: block."""
    block = block_of(lines, jobs_line)
    if not block:
        return []
    job_indent = indent_of(block[0][1])
    jobs = []
    for number, line in block:
        match = KEY_RE.match(line)
        if indent_of(line) == job_indent and match:
            jobs.append((match.group("key"), number, []))
        elif jobs:
            jobs[-1][2].append((number, line))
    return jobs


def job_keys(job_lines):
    """Return {key: (number, value)} of a job's own keys (its first indent level)."""
    if not job_lines:
        return {}
    level = indent_of(job_lines[0][1])
    keys = {}
    for number, line in job_lines:
        match = KEY_RE.match(line)
        if match and indent_of(line) == level and not match.group("dash"):
            keys[match.group("key")] = (number, unquote(match.group("value")))
    return keys


def check_workflow(lines):
    findings = []
    keys = top_level(lines)
    # GHAS-4: the trigger, in any form (on: x, on: [x], on: {x:}), read in
    # the on: block only, so an if: that names the event is not a trigger.
    if "on" in keys:
        number = keys["on"]
        for line_number, text in [(number, lines[number - 1])] + block_of(lines, number):
            if re.search(r"\bpull_request_target\b", text.split(" #", 1)[0]):
                findings.append((line_number, "GHAS-4 pull_request_target runs with secrets and a write token; use pull_request"))
    # GHAS-2 and GHAS-6 anywhere in the file.
    for number, line, match in significant(lines):
        if match and match.group("key") == "permissions" and unquote(match.group("value")) == "write-all":
            findings.append((number, "GHAS-2 write-all; grant each job only the permissions it needs"))
        if match and match.group("key") == "secrets" and unquote(match.group("value")) == "inherit":
            findings.append((number, "GHAS-6 secrets: inherit; pass each secret by name"))
    workflow_permissions = "permissions" in keys
    if workflow_permissions:
        number = keys["permissions"]
        value = unquote(KEY_RE.match(lines[number - 1]).group("value"))
        inline = [(number, value)] if value else block_of(lines, number)
        for line_number, text in inline:
            if re.search(r":\s*write\b", text) or text.strip() == "write":
                findings.append((line_number, "GHAS-2 write permission at the workflow level; move it to the job that needs it"))
    if "jobs" not in keys:
        return findings
    for job, number, job_lines in jobs_of(lines, keys["jobs"]):
        own = job_keys(job_lines)
        calls_workflow = "uses" in own
        # GHAS-2: without a workflow default, every job sets its own.
        if not workflow_permissions and "permissions" not in own:
            findings.append((number, f"GHAS-2 job '{job}' has no permissions and the workflow sets none"))
        # GHA-1: a moving runner image.
        # GHA-1: a moving runner image, as a scalar or in a list.
        latest = re.search(r"[\w.-]+-latest\b", own.get("runs-on", (0, ""))[1])
        if latest:
            findings.append((own["runs-on"][0], f"GHA-1 runs-on {latest.group(0)}; pin a versioned image (ubuntu-24.04, macos-15)"))
        # GHA-2: a timeout, except on a reusable workflow call.
        if not calls_workflow and "timeout-minutes" not in own:
            findings.append((number, f"GHA-2 job '{job}' has no timeout-minutes"))
        findings.extend(check_checkouts(lines, job_lines))
    return findings


def check_checkouts(lines, job_lines):
    """GHAS-5: each actions/checkout step sets persist-credentials: false."""
    findings = []
    for number, line in job_lines:
        match = KEY_RE.match(line)
        if not match or match.group("key") != "uses" or not unquote(match.group("value")).startswith("actions/checkout@"):
            continue
        # The step is the list item that holds this uses: line.
        step_start = number
        if not match.group("dash"):
            for back in range(number - 1, 0, -1):
                candidate = KEY_RE.match(lines[back - 1])
                if candidate and candidate.group("dash") and indent_of(lines[back - 1]) < indent_of(line):
                    step_start = back
                    break
        step = [lines[step_start - 1]] + [text for _, text in block_of(lines, step_start)]
        # Block or flow style ({ persist-credentials: false }) both count.
        if not any(re.search(r"\bpersist-credentials\s*:\s*['\"]?false\b", text.split(" #", 1)[0]) for text in step):
            findings.append((number, "GHAS-5 actions/checkout without persist-credentials: false"))
    return findings


def check_text(text):
    """Return [(line, message)] for one file; [] when it is neither a workflow nor an action."""
    lines = text.splitlines()
    keys = top_level(lines)
    if "jobs" in keys:
        return sorted(set(check_uses(lines) + check_scripts(lines) + check_workflow(lines)))
    if "runs" in keys:
        return sorted(set(check_uses(lines) + check_scripts(lines)))
    return []


def yaml_files(paths):
    # A folder means every YAML file below it, in a stable order.
    for path in paths:
        if path.is_dir():
            for file in sorted([*path.rglob("*.yml"), *path.rglob("*.yaml")]):
                if not SKIPPED_DIRS.intersection(file.relative_to(path).parts):
                    yield file
        else:
            yield path


def main(argv=None):
    parser = argparse.ArgumentParser(description="Report GitHub Actions workflows that break GHAS-1 to GHAS-6, GHA-1 or GHA-2.")
    parser.add_argument("paths", nargs="*", type=Path, default=[Path(".github/workflows")], help="files or folders (default: .github/workflows)")
    args = parser.parse_args(argv)

    found = broken = 0
    # A path that does not exist is an error, not "nothing found".
    for path in args.paths:
        if not path.exists():
            print(f"{path}: no such file or folder", file=sys.stderr)
            broken += 1
    for path in yaml_files(p for p in args.paths if p.exists()):
        # A file that cannot be read is reported, and the others still run.
        try:
            findings = check_text(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError) as error:
            print(f"{path}: cannot check: {error}", file=sys.stderr)
            broken += 1
            continue
        for line, message in findings:
            print(f"{path}:{line}: {message}")
        found += len(findings)

    # Exit 2 wins over 1: an unchecked file means the result is incomplete.
    if broken:
        return 2
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
