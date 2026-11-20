#!/usr/bin/env python3
"""Check Azure Pipelines YAML for unpinned templates, latest images and SourceBranchName conditions.

What it does
    Reads every *.yml and *.yaml file under the paths given and reports, with
    file and line:
    - ADO-5: an entry of resources.repositories without `ref: refs/tags/<tag>`,
      or whose ref is a branch or an expression (`${{ }}`, `$( )`, `$[ ]`);
    - ADOD-2: a `vmImage:` that ends in `-latest`;
    - ADOD-3: `SourceBranchName` in a condition (`condition:`, including its
      folded or literal block, or a `${{ if }}` / `${{ elseif }}` line).
    Files with none of `trigger`, `pr`, `stages`, `jobs`, `steps`,
    `resources`, `pool`, `extends` or `schedules` at the top level are skipped (not a
    pipeline or template).

Why it exists
    These three rules have one right answer, so a script checks them instead
    of an agent reading YAML by eye (the skill's step 4 runs it). The rules
    and their reasons are in ../rules.md.

How to run
    python3 check-pipelines.py [PATH ...]
    PATH is a file or a folder (searched recursively for *.yml and *.yaml,
    skipping .git and node_modules); the default is the current folder.
    Python 3.9 or newer, standard library only (no YAML library: see below).
    Exit code: 0 nothing found, 1 findings printed, 2 a path does not exist
    or a file could not be read (printed on stderr; the other files are still
    checked).

What can go wrong
    - The reader is line based and understands block-style YAML as Azure
      Pipelines files are written. Flow style (`{ repository: x, ref: y }` on
      one line) is read for `ref:` only; anchors and aliases are not
      followed.
    - ADO-5 reads every repository resource. One checked out only for its
      content (not for templates) may legitimately follow a branch: say so in
      the report instead of pinning it.
    - A `vmImage` built from a parameter or a variable (`${{ parameters.image }}`,
      `$(imageName)` with a matrix value) cannot be read; the parameter's
      default and the matrix are not checked.
"""

import argparse
import re
import sys
from pathlib import Path

SKIPPED_DIRS = {".git", "node_modules"}
PIPELINE_KEYS = {"trigger", "pr", "stages", "jobs", "steps", "resources", "pool", "extends", "schedules"}

KEY_RE = re.compile(r"^(?P<indent> *)(?P<dash>- +)?[\"']?(?P<key>[\w.-]+)[\"']?:(?:\s+(?P<value>.*))?$")
TAG_REF_RE = re.compile(r"^refs/tags/[\w.+-]+$")
EXPRESSION_RE = re.compile(r"\$\{\{|\$\(|\$\[")


def unquote(value):
    # The scalar without its trailing comment and quotes.
    value = value.split(" #", 1)[0].strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def stripped_flow(line):
    # A list item written as a flow map: `- { repository: x, ref: y }`.
    return re.match(r"^\s*-\s*\{", line) is not None


def is_pipeline(lines):
    # A pipeline or template has one of the known keys at column 0.
    for line in lines:
        match = KEY_RE.match(line)
        if match and not match.group("indent") and not match.group("dash") and match.group("key") in PIPELINE_KEYS:
            return True
    return False


def check_repositories(lines):
    """ADO-5: findings for resources.repositories entries."""
    findings = []
    resources_indent = repos_indent = item_indent = None
    item = None  # (line number, name, ref value or None)

    def close(entry):
        # An entry is complete: report a missing or unpinned ref.
        if entry is None:
            return
        number, name, ref = entry
        if ref is None:
            findings.append((number, f"ADO-5 repository '{name}' has no ref; pin it with ref: refs/tags/<tag>"))
        elif EXPRESSION_RE.search(ref):
            findings.append((number, f"ADO-5 repository '{name}' takes its ref from an expression ({ref}); use a literal tag"))
        elif not TAG_REF_RE.match(ref):
            findings.append((number, f"ADO-5 repository '{name}' follows {ref}; pin it with ref: refs/tags/<tag>"))

    for number, line in enumerate(lines, 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        match = KEY_RE.match(line)
        is_item = bool(match and match.group("dash")) or stripped_flow(line)
        # Leaving a block closes everything inside it.
        if resources_indent is not None and indent <= resources_indent:
            close(item)
            item = None
            resources_indent = repos_indent = item_indent = None
        if match and match.group("key") == "resources" and not match.group("dash"):
            resources_indent = indent
            continue
        if resources_indent is None:
            continue
        # A list item may sit at the same indent as `repositories:`.
        if repos_indent is not None and indent <= repos_indent and not (is_item and indent == repos_indent):
            close(item)
            item, repos_indent, item_indent = None, None, None
        if match and match.group("key") == "repositories" and not match.group("dash"):
            repos_indent = indent
            continue
        if repos_indent is None:
            continue
        # A flow-style item ({ repository: x, ref: y }) is complete on its line.
        if stripped_flow(line) and (item_indent is None or indent <= item_indent):
            close(item)
            fields = dict(re.findall(r"([\w-]+)\s*:\s*([^,}]+)", line.split("{", 1)[1]))
            ref = fields.get("ref")
            item = [number, unquote(fields.get("repository", "?")), unquote(ref) if ref else None]
            item_indent = indent
            continue
        # A new list item starts a new repository entry; a deeper list (an
        # entry's own trigger branches) belongs to the entry.
        if match and match.group("dash") and (item_indent is None or indent <= item_indent):
            close(item)
            item_indent = indent
            item = [number, "?", None]
        if item is None or not match:
            continue
        key, value = match.group("key"), unquote(match.group("value") or "")
        if key == "repository":
            item[1] = value
        elif key == "ref":
            item[2] = value
    close(item)
    return findings


def check_images_and_conditions(lines):
    """ADOD-2 and ADOD-3 findings."""
    findings = []
    condition_indent = None  # inside a `condition: |` or `>` block
    for number, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        if condition_indent is not None and indent <= condition_indent:
            condition_indent = None
        match = KEY_RE.match(line)
        key = match.group("key") if match else None
        value = unquote(match.group("value") or "") if match else ""
        # ADOD-2: a hosted image that moves under the pipeline.
        if key == "vmImage" and value.endswith("-latest"):
            findings.append((number, f"ADOD-2 vmImage {value}; pin the image (ubuntu-24.04)"))
        # ADOD-3: the branch name loses its folders, so conditions use SourceBranch.
        in_condition = condition_indent is not None or key == "condition" or re.search(r"\$\{\{\s*(else)?if\b", stripped)
        if in_condition and "SourceBranchName" in stripped:
            findings.append((number, "ADOD-3 SourceBranchName in a condition; compare Build.SourceBranch (refs/heads/...)"))
        if key == "condition" and value in ("|", ">", "|-", ">-", "|+", ">+"):
            condition_indent = indent
    return findings


def check_text(text):
    """Return [(line, message)] for one file, [] when it is not a pipeline."""
    lines = text.splitlines()
    if not is_pipeline(lines):
        return []
    return sorted(check_repositories(lines) + check_images_and_conditions(lines))


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
    parser = argparse.ArgumentParser(description="Report unpinned template repositories (ADO-5), -latest images (ADOD-2) and SourceBranchName conditions (ADOD-3).")
    parser.add_argument("paths", nargs="*", type=Path, default=[Path(".")], help="files or folders (default: .)")
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
