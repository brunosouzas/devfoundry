# Python: rules

Rules for Python code, from common practice. In an existing project, follow the conventions it already uses and report a difference instead of rewriting; these rules decide new code.

How to change this file (see CONTRIBUTING.md of this repository):
- **Add a rule:** copy an item, give it the next number in its group, write the rule, why it exists and how to check it. A new rule is a MINOR version.
- **Change a rule:** edit it in place and keep its ID, so old reviews still point at the right rule. A rule that now says the opposite is a MAJOR version; clearer wording is a PATCH.
- **Retire a rule:** keep its ID and heading, replace the text with `(retired in <version>: <reason>)`, and never reuse the number. A retired rule is a MAJOR version.

## Environment (PENV)

- **PENV-1** Run and test with the project's interpreter and locked dependencies, in a virtual environment inside the working copy.
  Why: a package installed globally hides a dependency the project forgot to declare.
  Check: commands in the report use `.venv/bin/python` or the project's runner (`uv run`, `poetry run`).

- **PENV-2** Declare every new dependency in the project's dependency file, pinned the way the others are.
  Why: an undeclared import works on your machine only.
  Check: each new import of a third-party package has a matching entry.

## Code (PY)

- **PY-1** Importing a module never starts work: entry points live under `if __name__ == "__main__":` or a declared console script.
  Why: a test or another module importing it would trigger side effects.
  Check: no top-level calls that read files, open connections or start loops.

- **PY-2** Build paths with `pathlib` and resolve them before checking that they stay inside the folder they must stay in.
  Why: `..` and symlinks escape string-based checks.
  Check: path checks call `.resolve()` and compare with `is_relative_to` or parents.

- **PY-3** Type-annotate public functions.
  Why: the signature is the cheapest documentation and lets a type checker catch misuse.
  Check: new public functions have parameter and return annotations.

- **PY-4** Open text files with an explicit encoding (`encoding="utf-8"`).
  Why: the default encoding differs between machines.
  Check: `scripts/check-encoding.py` reports no `open()`, `read_text()` or `write_text()` in text mode without `encoding`.

## Tests (PTST)

- **PTST-1** Tests use temporary folders (`tmp_path`, `tempfile`) and fake services; never a real user data folder, a real home folder or a live API.
  Why: a test that touches real data can destroy it.
  Check: no hard-coded home paths or production URLs in tests.

- **PTST-2** Test the error paths too: invalid input, missing file, a dependency that fails.
  Why: the happy path is the one already exercised by hand.
  Check: each new function with a failure mode has a test for it.
