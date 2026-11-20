# Devfoundry

Claude Code plugins with **rules** for the languages and tools around everyday software work. Each plugin is one skill: a short `SKILL.md` that routes the request, and a `rules.md` of numbered rules with stable IDs, each with its reason and how to check it. Some skills ship a small script that checks what has a right answer.

| Plugin | Rules for | Rule IDs |
| --- | --- | --- |
| `java` | Standalone Java: the JDK and build a project declares, dependencies, nulls, exceptions, JUnit tests | JBLD, JAVA, JTST |
| `python` | Python applications, CLIs and scripts: locked dependencies, environments, safe paths, encodings, pytest | PENV, PY, PTST |
| `shell` | Bash and POSIX sh scripts, git hooks and pipeline steps: strict mode, quoting, guarded destructive commands | SH, SHP, SHI |
| `astro` | Astro static sites: clean builds, `.astro` markup pitfalls, content schema, public URLs and redirects | AST, ASB, ASD |
| `cloudflare` | Cloudflare Workers and Pages: wrangler config, routes, webhook signatures, secrets, deploys and rollbacks | CFL, CFW, CFD, CFB, CFR |
| `azure-devops` | Writing Azure Pipelines YAML: templates and pinned refs, variable groups, environments, secrets | ADON, ADO, ADOS, ADOD |
| `github-actions` | Writing GitHub Actions workflows: pinned actions, least-privilege permissions, untrusted input, secrets | GHAS, GHA, GHAD |
| `jenkins` | Writing Jenkinsfiles and Groovy shared libraries: declarative pipelines, failure handling, credentials | JNK, JNKS |

## What this repository promises, and what it does not

**The promise is the rules, and only the rules.** Each rule is written down, numbered and stable: a rule is retired, never deleted, so you can cite it.

There is **no project profile** and **no measurement**. Nothing here has been run against fixed cases to show that an agent follows the rules better with them than without them. **Code snippets inside the skills are illustrative**: they are not built or tested projects, and they are not a promise that they compile or run in your environment.

The three CI and pipeline plugins (`azure-devops`, `github-actions`, `jenkins`) hold rules for **writing the pipeline files** only. Your delivery process (who approves, which branch ships, how a release is made) is yours, and they leave it to your repository.

**MuleSoft** (Mule 4, DataWeave, APIkit, MUnit, API contracts, integration and resilience patterns) is not here. It lives in [mulesmith](https://github.com/brunosouzas/mulesmith), which does promise a profile, verified examples and measured cases.

Devfoundry is not affiliated with Anthropic, Microsoft, GitHub, Cloudflare, Jenkins or any other vendor named in a plugin; the names identify the tools the rules are about.

## Requirements

Claude Code, in the terminal, the Code tab of the Claude desktop app or the VS Code extension. Some skills ship a checker script that needs Python 3 (standard library only).

## Install

Add the marketplace once, then install the plugins you want (each `/plugin install` opens a panel where you pick the scope):

```
/plugin marketplace add brunosouzas/devfoundry
/plugin install java@devfoundry
/plugin install python@devfoundry
/plugin install shell@devfoundry
/plugin install astro@devfoundry
/plugin install cloudflare@devfoundry
/plugin install azure-devops@devfoundry
/plugin install github-actions@devfoundry
/plugin install jenkins@devfoundry
```

Or from a shell:

```bash
claude plugin marketplace add brunosouzas/devfoundry
claude plugin install java@devfoundry   # and so on, with --scope user for every project
```

## How a skill works

The skill loads when a request matches its `description`. It tells the agent how to work and to follow `rules.md`, citing a rule by its ID and the skill's version when it applies or breaks it, for example "breaks JAVA-3 (java 1.0.0)". Where a skill has a checker, the rule says which script runs it.

## Contributing

- Plugin and skill names are fixed technical slugs; a plugin `name` never changes once published.
- The `description` is the trigger: write the when-to-use cases there, with a "Not for" clause for near misses. Frontmatter must be strict YAML: quote a description that contains `: ` or ` #`. `tooling/ci/check-skill-frontmatter.py` checks it.
- A rule keeps its ID. Retire it, never delete it.
- Check a change with `claude plugin validate .`, `claude plugin validate plugins/<plugin>` and the frontmatter check.

## License

[MIT](LICENSE).
