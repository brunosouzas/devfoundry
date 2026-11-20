---
name: python
description: "Rules for Python code: the interpreter and locked dependencies the project declares, virtual environments, import side effects, safe paths, type annotations, file encodings and pytest or unittest tests. Use when writing, changing, reviewing or fixing a Python application, CLI or script with logic, and its tests; recognise it by a pyproject.toml, requirements*.txt, uv.lock, poetry.lock or *.py files that are the product. Triggers: Python, Python 3, pytest, unittest, pip, uv, Poetry, virtualenv, venv. Not for a few lines of shell glue (shell skill), a pipeline's YAML (azure-devops, github-actions or jenkins skill), or Java code (java skill)."
license: MIT
metadata:
  version: "1.0.0"
  aliases: "python 3, python3, pytest"
---

# Python

What is particular to Python code: an application, a CLI or a script with logic, and its tests.

## When

- Use for Python applications, CLIs and scripts with logic, and their tests.
- Not for a few lines of shell glue: those follow `shell`, if installed.

## How to work

1. Find the interpreter version and the dependency tool the project uses (`pyproject.toml`, `requirements*.txt`, `uv.lock`, `poetry.lock`, `.python-version`). Use the project's virtual environment, or create `.venv` inside the working copy; never install into the system Python (PENV-1).
2. A copied virtual environment is not portable (its scripts keep absolute paths): recreate it instead of trusting it.
3. Use the test runner the project already has (`pytest` or `unittest`).
4. Verify: the project's test command, plus its linter or type checker if it has one (`ruff`, `mypy`), and the encoding check (PY-4):
   ```bash
   python3 <this skill's folder>/scripts/check-encoding.py <changed files or folders>
   ```

## Rules

Read [rules.md](rules.md) and follow every rule. Cite a rule by its ID and this skill's version when you apply or break it, for example "breaks PY-2 (python 1.0.0)".
