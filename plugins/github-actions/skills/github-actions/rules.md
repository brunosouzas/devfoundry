# GitHub Actions: rules

Rules for GitHub Actions, from GitHub's documentation (security hardening for GitHub Actions, the `GITHUB_TOKEN`, events that trigger workflows, reusable workflows, environments) and practice in maintained workflows. A rule marked `(locked)` protects secrets or the repository and no local convention may change or disable it.

How to change this file (see CONTRIBUTING.md of this repository):
- **Add a rule:** copy an item, give it the next number in its group, write the rule, why it exists and how to check it. A new rule is a MINOR version.
- **Change a rule:** edit it in place and keep its ID, so old reviews still point at the right rule. A rule that now says the opposite is a MAJOR version; clearer wording is a PATCH.
- **Retire a rule:** keep its ID and heading, replace the text with `(retired in <version>: <reason>)`, and never reuse the number. A retired rule is a MAJOR version.

## Security (GHAS)

- **GHAS-1** (locked) Pin every action and reusable workflow from another repository by its full commit SHA, with the tag in a comment: `uses: actions/checkout@<40-hex sha> # v7.0.1`. A local `./` path and a `docker://` image pinned by `@sha256:` digest are fine.
  Why: a tag or branch can be moved to other code after review; a full SHA is the only immutable reference, and Dependabot still updates it, comment included.
  Check: `scripts/check-workflows.py` finds no `uses:` with a tag, a branch or a short SHA.

- **GHAS-2** (locked) The workflow's `permissions:` is `{}` or `contents: read`, and each job that needs more declares exactly that in its own `permissions:`; never `write-all`. Without a workflow-level block, every job has one.
  Why: the `GITHUB_TOKEN` gets the repository's default permissions otherwise, which may be write to everything, in every job and every step's code.
  Check: `scripts/check-workflows.py` finds no write at the workflow level, no `write-all`, and no job without permissions when the workflow sets none.

- **GHAS-3** (locked) Never interpolate an expression a user can influence into `run:` or a `script:` (actions/github-script): `github.event.*` titles, bodies, messages, refs, branch names (`head_branch`), labels and display titles, author and committer names and emails, a fork's `head.repo.full_name`, `github.head_ref`, and `inputs.*`. Map it to `env:` and use the quoted variable (`"$TITLE"`).
  Why: `${{ }}` is replaced in the script text before the shell runs, so a pull request titled `"; curl … | sh #` runs as code with the job's token and secrets.
  Check: `scripts/check-workflows.py` finds none of those expressions inside `run:` or `script:`.

- **GHAS-4** (locked) Never use `pull_request_target`, in any workflow: checks run on `pull_request`, and a write a pull request needs (a label, a comment) runs in a `workflow_run` job that checks out none of the pull request's code. A `workflow_run` job treats the artifacts of the run it follows as data and never executes them.
  Why: `pull_request_target` runs with the base repository's secrets and a write token, so checking out or building the pull request's code hands both to whoever opened it, and one later edit is enough to do that.
  Check: `scripts/check-workflows.py` finds no `pull_request_target`; review that a `workflow_run` job runs nothing from a downloaded artifact.

- **GHAS-5** (locked) Check out with `persist-credentials: false`, unless a later step of the same job pushes with that token, and then say so in a comment.
  Why: by default the token stays on the runner for the rest of the job (in the repository's git config, or a credentials file it points to), where every later step and tool can read it.
  Check: `scripts/check-workflows.py` finds every `actions/checkout` step with `persist-credentials: false`.

- **GHAS-6** (locked) Pass secrets by name, to the job or reusable workflow that needs them, never `secrets: inherit`; a step reads a secret from `env:`, never from an argument or the script text; a value derived from a secret (a minted token) is masked with `::add-mask::` before any other use.
  Why: `inherit` hands every secret of the repository to a workflow that needs one; arguments appear in process lists and error messages.
  Check: `scripts/check-workflows.py` finds no `secrets: inherit` and no `${{ secrets.* }}` inside `run:` or `script:`; review that a minted value is masked.

- **GHAS-7** (locked) A secret that only a protected ref needs (a release key, a production credential) lives in an environment whose deployment branches and tags admit only that ref, and the job declares `environment:`. Where the plan has no environments for the repository (a private repository on GitHub Free), the secret's job runs only on a protected ref (a tag ruleset, the default branch) and says so in a comment.
  Why: a repository secret reaches any workflow on any branch that someone with write access pushes.
  Check: the environment's deployment branch policy names the refs; a run from a scratch branch cannot read the secret.

- **GHAS-8** Prefer short-lived identities: OIDC (`id-token: write`, in that job only) for clouds and registries that support it, and a GitHub App token limited to the repository and the permissions the job needs (`actions/create-github-app-token` with `repositories:` and `permission-*`) over a personal access token. Events made with `GITHUB_TOKEN` start no new workflow run (except `workflow_dispatch` and `repository_dispatch`), so a bot whose pull request needs its checks uses an App token.
  Why: a long-lived token outlives the job and usually reaches more repositories than the job needs.
  Check: no personal access token in a workflow that an App or OIDC could replace; `id-token: write` appears only in the job that exchanges it.

- **GHAS-9** A tool downloaded in a step is pinned to a version and verified against its published checksum before it runs.
  Why: a release asset can be replaced, and a download without a check runs whatever comes back.
  Check: each `curl` or `wget` of a binary is followed by `sha256sum -c` (or `sha512sum -c`) of a checksum written in the workflow.

## Workflows (GHA)

- **GHA-1** Pin the runner image (`runs-on: ubuntu-24.04`); never `*-latest`. Move to a new image in its own change.
  Why: `ubuntu-latest` changes under every workflow on GitHub's schedule, and the failures arrive the same week in unrelated changes.
  Check: `scripts/check-workflows.py` finds no `-latest` runner.

- **GHA-2** Every job sets `timeout-minutes:` (a job that calls a reusable workflow cannot: the called job sets it).
  Why: the default is 360 minutes; a hung step holds a runner, and a concurrency group, for six hours.
  Check: `scripts/check-workflows.py` finds every job with `timeout-minutes`.

- **GHA-3** A workflow that releases or deploys sets `concurrency:` with `cancel-in-progress: false` for that target; a pull request check may cancel its older runs.
  Why: two releases at once race on tags and versions, and a cancelled deploy leaves the target half-done.
  Check: release and deploy jobs have a `concurrency.group` and `cancel-in-progress: false`.

- **GHA-4** Shared jobs live in reusable workflows (`on: workflow_call`) called at a tag pinned by SHA (GHAS-1). A change to a reusable workflow's inputs, secrets or outputs keeps every caller working, or changes every caller in the same release; read the called workflow at the ref the caller pins, never from a local checkout.
  Why: a caller fails at start-up (`startup_failure`) when it passes a secret or input the pinned version does not declare, and a local branch may not be what the tag holds.
  Check: the pull request lists each caller and the ref it pins; the inputs and secrets a caller passes exist in `git show <ref>:<workflow>`.

- **GHA-5** Lint every workflow with `actionlint` (pinned and checksum-checked, GHAS-9) in CI.
  Why: a typo in an expression or a key is found only when the workflow runs, often on `main`.
  Check: a CI job runs `actionlint` on `.github/workflows/`.

- **GHA-6** A required check's name is the name the check reports: the job's `name:` (or id), `<caller job> / <called job>` for a reusable workflow, and `<name> (<matrix values>)` for each job of a matrix. Renaming either changes the required check in the same change.
  Why: a required check that never reports blocks every merge, and one that is no longer required lets a red build merge.
  Check: the ruleset's required checks equal the names on a pull request's checks.

## Delivery (GHAD)

- **GHAD-1** A job that deploys or publishes declares `environment:`; the production environment requires a reviewer (with self-review prevented) and an agent never approves it. Where the plan offers no required reviewers for the repository (private repositories outside GitHub Enterprise), the human approval is the required review of the release pull request or the protected tag that starts the job, and the workflow's comment says which.
  Why: the environment is where GitHub records who approved what and holds the secrets back until then.
  Check: each deploy or publish job has `environment:`; the production environment lists required reviewers, or the comment names the approval that replaces them.

- **GHAD-2** Production deploys and publishes run only from a pushed release tag or a push to the default branch that merges a release; never from `pull_request`, and any manual trigger is limited by `if:` on `github.ref`.
  Why: a deploy that a branch run can reach publishes unreviewed code.
  Check: each production job's trigger and `if:` admit only the release tag or the default branch.

- **GHAD-3** Build once, in a job without publishing rights, and hand the result on as an artifact; the publishing job installs and builds nothing and executes nothing from the artifact.
  Why: the publishing identity must never exist while dependencies install or their scripts run.
  Check: the job with the token or `id-token: write` has no install or build step.

- **GHAD-4** Release and publish jobs restore no cache (`actions/cache`, the `cache:` input of a `setup-*` action), and turn off caching a setup action does on its own (`package-manager-cache: false` for `actions/setup-node`).
  Why: a cache written by an earlier run can carry poisoned files into the build that is published.
  Check: no cache in a job that has `environment:`, `id-token: write` or a release token; its `setup-node` step sets `package-manager-cache: false`.
