# AGENTS.md — devfoundry

Claude Code plugins with rules for other languages and tools. This file is for agents working **on** this repository; users of the plugins read `README.md`.

## Layout

- `plugins/<plugin>/`: one plugin each (`.claude-plugin/plugin.json`, `skills/<skill>/SKILL.md`, `rules.md`, and `scripts/` for a checker). `.claude-plugin/marketplace.json` lists them.
- `tooling/ci/`: the script CI runs (`.github/workflows/ci.yml`), runnable locally.

## Rules for changing a skill

- The promise is rules only: no profile, no measurement, no claim of verified examples. Say nothing in a skill that implies more.
- Rule IDs are stable: retire a rule, never delete or renumber it.
- Plugin and skill names carry no brand and never change once published.
- The description is the trigger and must be strict YAML (quote a value that contains `: `).
- The CI and pipeline plugins hold rules for writing pipeline files; do not put a delivery process (gates, approvals, release models) in them.
- Check: `claude plugin validate .`, `claude plugin validate plugins/<plugin>`, `python3 tooling/ci/check-skill-frontmatter.py`.
