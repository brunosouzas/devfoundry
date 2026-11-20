# Azure DevOps: rules

Rules for Azure Pipelines, from common practice and the platform's documented behaviour. A team adds its own scopes, numbers and triggers on top; a rule marked `(locked)` protects secrets and no local convention may change or disable it.

How to change this file (see CONTRIBUTING.md of this repository):
- **Add a rule:** copy an item, give it the next number in its group, write the rule, why it exists and how to check it. A new rule is a MINOR version.
- **Change a rule:** edit it in place and keep its ID, so old reviews still point at the right rule. A rule that now says the opposite is a MAJOR version; clearer wording is a PATCH.
- **Retire a rule:** keep its ID and heading, replace the text with `(retired in <version>: <reason>)`, and never reuse the number. A retired rule is a MAJOR version.

## Naming (ADON)

- **ADON-1** Variable groups follow one naming standard that puts the layer, the scope and the purpose in the name, `vg-<NN>-<scope>-<purpose>[-<environment>]`, where `NN` orders the groups by layer (identity and credentials first, runtime values later). The team fixes the scopes and numbers.
  Why: the number sorts groups by layer, the scope says who may use the group, and the name says what is inside without opening it; two patterns side by side make every reader guess.
  Check: every new or renamed group matches the standard, and the README of every template or pipeline that names it changes in the same change.

- **ADON-2** Variables are `UPPER_SNAKE_CASE`: they start with a letter and hold only `A-Z`, `0-9` and `_`, prefixed with the environment's name in capitals when the value differs per environment (`TEST_`, `UAT_`, `PROD_`, `STAGING_`: `TEST_APP_ENV`, `PROD_API_HOST`). No dot notation (`test.app.env`), hyphens (`test-sys.auth`) or camelCase (`testAppEnv`).
  Why: scripts read them as environment variables, and one style needs no escaping and lets templates build names predictably.
  Check: new variables match the pattern; an existing variable that does not match is renamed in the next change that touches its group.

## Pipelines (ADO)

- **ADO-1** Shared steps live in versioned templates; a pipeline calls templates with parameters instead of copying steps.
  Why: copied steps drift; a template fix reaches every pipeline.
  Check: no step block duplicated across pipelines in the diff.

- **ADO-2** A changed template parameter keeps working for every existing caller, or every caller changes in the same change.
  Why: a template can parse fine while breaking a pipeline in another repository.
  Check: the pull request lists the callers and how each was checked.

- **ADO-3** Deploy steps run as deployment jobs bound to an environment, so approvals and history apply.
  Why: a plain job deploys with no gate and no record.
  Check: each deploy step is a `deployment:` job with `environment:`.

- **ADO-4** Build once, publish the artifact, and deploy that artifact in later stages.
  Why: a rebuild per stage deploys something that was never tested.
  Check: deploy stages download the pipeline artifact, or the published version from the registry the delivery documentation names; they do not build, except as the exception below.
  Exception: a rebuild from the same release tag that the delivery documentation declares, with its provenance recorded: a scheduled rebuild whose output depends on the build date, or a build per target organisation (an artifact derived from the tag, built again when the target's registry lacks it).

- **ADO-5** A template repository resource is pinned to a literal tag, `ref: refs/tags/vX.Y.Z`; never a branch, a missing `ref` or a `${{ variables.x }}` expression.
  Why: a `ref` built from a variable falls silently to the default branch, and a branch moves under every consumer; a tag that does not exist stops the pipeline at compile time, which is the safe failure.
  Check: `scripts/check-pipelines.py` finds every `resources.repositories` entry with `ref: refs/tags/` and a literal version.

- **ADO-6** A change to a template is proven by compiling every pipeline that consumes it (the Pipelines preview API, `POST _apis/pipelines/{id}/preview` with the repository resource pointed at the change's branch), not only by tests that read the YAML.
  Why: a template expression Azure refuses at compile time (`${{ add(...) }}` in a job's timeout) passed every text test and broke the one pipeline that used it.
  Check: the pull request of a template lists each consumer and its preview result.

- **ADO-7** A review, a label or an edit of a pull request's description starts no pull request run. When the pipeline reads such an input (an approval, a label), comment `/azp run <pipeline>` after changing it, and read the bot's answer: a run refused because the target branch moved leaves the old result in place.
  Why: a check that read the input too early stays green or red on stale data.
  Check: after a label, an approval or a description changes on a pull request whose checks read it, a newer run exists.

## Secrets (ADOS)

- **ADOS-1** (locked) Secrets come from secret variables, variable groups linked to Azure Key Vault, or service connections; never from YAML or the repository.
  Why: YAML is in git and readable by everyone with repository access.
  Check: no secret values in the diff.

- **ADOS-2** (locked) Pass secrets to scripts as environment variables (`env:`), never interpolated into the script text or arguments.
  Why: interpolated values appear in logs and process lists.
  Check: secrets are mapped under `env:` and referenced as `$VAR` inside the script.

- **ADOS-3** (locked) A job that holds a secret checks out no code of the tree it judges, and runs its tools from an empty folder; a pull request run gets no secret with write access.
  Why: a tool started in a checkout reads files that the pull request controls (Maven reads `.mvn/jvm.config`), which hands the secret to code nobody reviewed.
  Check: jobs that map a secret have `checkout: none` or check out only a tag; tool steps set `workingDirectory` to an empty folder; pull request runs link only read-only groups.

- **ADOS-4** (locked) Every variable group that holds a secret has a Branch control check allowing only the protected refs that need it (the default branch, release tags, maintenance branches when they release), proven by a negative run from another branch.
  Why: without it, any branch with edited YAML receives the secret; the check reads every repository of the run, so a template repository at its pinned ref must fit too.
  Check: the group's checks list Branch control with explicit refs; a run from a scratch branch stops at the check.

- **ADOS-5** (locked) A token minted inside a step is masked with `##vso[task.setsecret]` before any other use and reaches a tool through standard input or a file of mode 600, never an argument, an `env NAME=value` prefix or a URL.
  Why: arguments are visible in the process list and in error messages; an unmasked token in a log stays readable for as long as the run is kept.
  Check: no token in a command line of the step (`ps` sampled while it runs); every minted value is masked first.

## Delivery (ADOD)

- **ADOD-1** Production deploys run only from a release tag (`refs/tags/v*`), or from the merge of a reviewed change to a desired-state file on the default branch (the file names the released versions); a pull request or a branch run builds and deploys at most a preview or a test environment. Any other trigger that reaches production is named in the repository's delivery documentation.
  Why: a deploy step with no branch condition publishes production from any manual run on any branch.
  Check: every production stage has a `condition:` on `Build.SourceBranch` for the tag or the default branch, and `ne(variables['Build.Reason'], 'PullRequest')`; a desired-state pipeline has `pr: none` and a `trigger.paths.include` of its file.

- **ADOD-2** Pin the agent image (`vmImage: ubuntu-24.04`) and the tools (lockfile, plugin versions); never `ubuntu-latest`.
  Why: `ubuntu-latest` moved to Ubuntu 26 on 2026-10-19 and pipelines started failing the same week.
  Check: `scripts/check-pipelines.py` finds no `-latest` image.

- **ADOD-3** Compare branches with `Build.SourceBranch` (`refs/heads/hotfix/1.2.1`), never `Build.SourceBranchName`.
  Why: `SourceBranchName` keeps only the last segment, so `hotfix/1.2.1` never matches `hotfix/*`.
  Check: `scripts/check-pipelines.py` finds no `SourceBranchName` in a condition.

- **ADOD-4** A trigger that releases (a release branch, `v*` tags) has no path filter.
  Why: a release whose only change was the changelog never ran, because the path filter also applies to the merge commit.
  Check: no `paths:` under the releasing trigger.

- **ADOD-5** A production deploy happens only after a human approval that the platform records: an Approval check on the production environment, the code owner's required review of the desired-state file, or a manual validation in the run; an agent never gives it, delegated or not.
  Why: production is the owner's decision, and the platform's record says who approved what.
  Check: the production path has one of the three, and the agent's identity cannot satisfy it.

- **ADOD-6** The pull request pipeline's check name is the one the branch ruleset requires, pinned to the Azure Pipelines app.
  Why: a required check that never reports blocks every merge; one that is not required lets a red build merge; a check not pinned to the app can be satisfied by a status anyone with write access posts.
  Check: the name on a pull request's checks equals the required one, and the ruleset names the app as its source.

- **ADOD-7** An environment that pipelines deploy to has an Exclusive lock check, and its stages use `lockBehavior: sequential`.
  Why: without the check, `sequential` waits for nothing, and two runs deploy the same environment at once; with it, a second run waits and is not cancelled.
  Check: the environment's checks list one Exclusive lock.

- **ADOD-8** A deploy or restore run that stopped is resumed by a new run queued on the same commit, never by "Rerun failed jobs".
  Why: a rerun reuses the tokens and outputs of the first attempt and may skip a validation that already passed; a new run starts from what exists and is idempotent when its steps are.
  Check: the runbook says "queue a new run on the same commit".
