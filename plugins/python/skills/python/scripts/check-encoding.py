#!/usr/bin/env python3
"""Check Python sources for text files opened without an explicit encoding (PY-4).

What it does
    Parses every *.py file under the paths given and reports, with file and
    line, each call that reads or writes text with the platform's default
    encoding:
    - open(...) or io.open(...) in a text mode (no "b" in the mode) without an
      encoding= argument;
    - <path>.read_text(...) or <path>.write_text(...) without encoding=;
    - <path>.open(...) in a text mode without encoding= (pathlib), when its
      first argument is a mode literal or absent;
    - gzip.open, bz2.open or lzma.open with a "t" mode, and codecs.open,
      without an encoding.
    An encoding passed by position counts as given.
    os.open, tarfile.open, zipfile.open and similar are not text and are
    never reported.

Why it exists
    PY-4 has one right answer, so a script checks it instead of an agent
    reading code by eye (the skill's step "Verify" runs it). The rule and its
    reason are in ../rules.md.

How to run
    python3 check-encoding.py [PATH ...]
    PATH is a file or a folder (searched for *.py, skipping .venv, venv,
    .tox, .git, node_modules and __pycache__); the default is the current folder.
    Python 3.9 or newer, standard library only.
    Exit code: 0 nothing found, 1 findings printed, 2 a path does not exist
    or a file could not be read or parsed (printed on stderr; the other files
    are still checked).

What can go wrong
    - The check reads the syntax, not the types: any call named read_text,
      write_text or open on an object counts, so a method of your own with the
      same name and no encoding parameter is reported. Add encoding to it or
      ignore that line; there is no inline suppression on purpose.
    - A mode passed through a variable cannot be read: it is treated as text,
      so the call needs an encoding (or a literal "rb"/"wb" mode).
    - A call that passes **kwargs is skipped: the encoding may be inside it.
"""

import argparse
import ast
import re
import sys
from pathlib import Path

# Folders that hold someone else's code or generated files, never the product.
SKIPPED_DIRS = {".venv", "venv", ".git", "node_modules", "__pycache__", ".tox"}

# Standard modules whose open() is not a text file open (a descriptor, an
# archive, a browser tab): never reported.
NOT_TEXT_OPEN = {"os", "tarfile", "zipfile", "webbrowser", "shelve", "dbm", "wave"}

# Compressed-file modules: open() is binary by default and text only with "t".
COMPRESSED = {"gzip", "bz2", "lzma"}


def mode_of(call, position):
    """Return the literal mode string of a call, '' when absent, None when not literal."""
    # The mode is the keyword mode= or the positional argument at `position`.
    for keyword in call.keywords:
        if keyword.arg == "mode":
            node = keyword.value
            break
    else:
        if len(call.args) > position:
            node = call.args[position]
        else:
            return ""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def looks_like_mode(node):
    # A literal made only of mode letters ("r", "wb", "a+"): a file name is not.
    return isinstance(node, ast.Constant) and isinstance(node.value, str) and bool(re.fullmatch(r"[rwaxbt+]{1,3}", node.value))


def needs_encoding(call):
    """Return the name of the call when it handles text without an encoding, else None."""
    keywords = {k.arg for k in call.keywords}
    # **kwargs may carry the encoding; encoding given by keyword: nothing to report.
    if None in keywords or "encoding" in keywords:
        return None
    func = call.func
    receiver = func.value.id if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) else None
    # Each kind of call: its name, where its mode is, and where a positional
    # encoding sits (open(file, mode, buffering, encoding), Path.open(mode,
    # buffering, encoding), read_text(encoding), write_text(data, encoding)).
    if isinstance(func, ast.Name) and func.id == "open" or receiver == "io" and func.attr == "open":
        name, mode_position, encoding_position = ("open()" if receiver is None else "io.open()"), 1, 3
    elif receiver == "codecs" and func.attr == "open":
        # codecs.open(file, mode, encoding): binary unless an encoding is given.
        name, mode_position, encoding_position = "codecs.open()", 1, 2
    elif receiver in COMPRESSED and func.attr == "open":
        # gzip.open(file, mode, compresslevel, encoding) is binary unless "t".
        mode = mode_of(call, 1)
        if len(call.args) > 3 or mode is None or "t" not in mode:
            return None
        return f"{receiver}.open()"
    elif receiver in NOT_TEXT_OPEN and func.attr == "open":
        return None
    elif isinstance(func, ast.Attribute) and func.attr == "read_text":
        # pathlib's text helpers have no binary mode: always text.
        return None if call.args else ".read_text()"
    elif isinstance(func, ast.Attribute) and func.attr == "write_text":
        return None if len(call.args) > 1 else ".write_text()"
    elif isinstance(func, ast.Attribute) and func.attr == "open":
        # Path.open(mode, buffering, encoding). Another object's open(name)
        # takes a file name first: only a mode literal (or nothing) is Path's.
        if call.args and not looks_like_mode(call.args[0]):
            return None
        name, mode_position, encoding_position = ".open()", 0, 2
    else:
        return None
    if len(call.args) > encoding_position:
        return None
    mode = mode_of(call, mode_position)
    # A literal binary mode needs no encoding; a non-literal mode might be text.
    if mode is not None and "b" in mode:
        return None
    return name


def check_source(text, filename="<source>"):
    """Return [(line, message)] for one file's source; raises SyntaxError."""
    tree = ast.parse(text, filename=filename)
    findings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = needs_encoding(node)
            if name:
                findings.append((node.lineno, f"PY-4 {name} without encoding="))
    return sorted(findings)


def python_files(paths):
    # A folder means every *.py below it, skipping environments and caches.
    for path in paths:
        if path.is_dir():
            for file in sorted(path.rglob("*.py")):
                if not SKIPPED_DIRS.intersection(file.relative_to(path).parts):
                    yield file
        else:
            yield path


def main(argv=None):
    parser = argparse.ArgumentParser(description="Report text-mode file calls without encoding= (PY-4).")
    parser.add_argument("paths", nargs="*", type=Path, default=[Path(".")], help="files or folders (default: .)")
    args = parser.parse_args(argv)

    found = broken = 0
    # A path that does not exist is an error, not "nothing found".
    for path in args.paths:
        if not path.exists():
            print(f"{path}: no such file or folder", file=sys.stderr)
            broken += 1
    for path in python_files(p for p in args.paths if p.exists()):
        # A file that cannot be read or parsed is reported; the others still run.
        try:
            findings = check_source(path.read_text(encoding="utf-8"), str(path))
        except (OSError, UnicodeDecodeError, SyntaxError, ValueError) as error:
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
