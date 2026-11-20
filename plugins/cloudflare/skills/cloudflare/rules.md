# Cloudflare: rules

Rules for Cloudflare Workers and Pages deploys, from what real Workers and sites needed so far. In an existing Worker, follow the layout it already has and report a difference instead of moving files; these rules decide new routes and deploys.

How to change this file (see CONTRIBUTING.md of this repository):
- **Add a rule:** copy an item, give it the next number in its group, write the rule, why it exists and how to check it. A new rule is a MINOR version.
- **Change a rule:** edit it in place and keep its ID, so old reviews still point at the right rule. A rule that now says the opposite is a MAJOR version; clearer wording is a PATCH.
- **Retire a rule:** keep its ID and heading, replace the text with `(retired in <version>: <reason>)`, and never reuse the number. A retired rule is a MAJOR version.

## Layout (CFL)

- **CFL-1** The wrangler config keeps the existing Worker `name`, its `main` entry and its custom-domain route, and holds no secrets.
  Why: a different name creates a second Worker instead of replacing the live one.
  Check: the diff does not change `name`; no secret value in the config.

- **CFL-2** One route table (method + path → handler) in the entry module, with JSON 404 and 405 answers; each service in its own module (`src/routes/`), shared verifiers in one place (`src/lib/`).
  Why: one Worker can serve many hooks, with one place to see every route.
  Check: new routes are registered in the table and live in their own module.

- **CFL-3** Tests use vitest, and `npm test` gates the build.
  Why: Workers Builds runs the tests before it deploys.
  Check: the build command runs `npm test`.

## Inbound webhooks (CFW)

- **CFW-1** Verify every signature with HMAC-SHA256 through `crypto.subtle.verify`, in each provider's format (`sha256=` for GitHub, Slack's `v0:{ts}:{body}`).
  Why: `verify` runs in constant time; comparing strings leaks timing.
  Check: no `===` comparison of signatures.

- **CFW-2** Reject requests with a stale timestamp.
  Why: a valid signed request can otherwise be replayed.
  Check: the verifier checks the timestamp window.

- **CFW-3** Add an allowlist when a route acts on behalf of a person (for example a Slack button).
  Why: a valid signature proves the platform, not the person.
  Check: such routes check the user id.

- **CFW-4** Secrets are set by the Worker's owner with `wrangler secret put` or the dashboard; the README lists their names.
  Why: secrets never enter the repository or a log.
  Check: new secrets are named in the README and absent from the code.

## Changes that delete things (CFD)

- **CFD-1** Before removing a route, find what called it (the README, the sender's settings) and list the webhooks to delete at the sender.
  Why: a removed route returns 404 and the sender keeps retrying.
  Check: the pull request lists the senders.

- **CFD-2** To remove a Durable Object class, drop the binding and append a new `[[migrations]]` entry with `deleted_classes`; never edit earlier migrations. Say in the pull request that the deploy deletes its data for good.
  Why: Cloudflare requires an append-only migration history, and the deletion is irreversible on merge.
  Check: migrations only grow; the pull request has the warning.

## Workers Builds (CFB)

For a Worker deployed by Workers Builds.

- **CFB-1** Build `npm ci && npm test`; deploy `npx wrangler deploy`; non-production branches `npx wrangler versions upload` or disabled.
  Why: a build still configured with the old `wrangler preview` command (removed from Wrangler) failed every pull-request build.
  Check: the Workers Builds settings use these commands.

- **CFB-2** A red "Workers Builds" check on a pull request is usually the preview build: compare with the check runs of merge commits on the default branch before debugging.
  Why: production deploys only run on the default branch.
  Check: `gh api repos/<owner>/<repo>/commits/<sha>/check-runs` on the last merge.

- **CFB-3** Forwarding from a Worker to a service on a local machine needs a Cloudflare Tunnel and works only while that machine is on; say so before proposing it.
  Why: the Worker cannot reach a sleeping machine.
  Check: a design that calls a local machine states the tunnel and the availability limit.

## Delivery from a pipeline (CFR)

For a Worker or a Pages site deployed by a pipeline, with staging and production.

- **CFR-1** A pull request of a Worker or a site builds and tests only: no deploy and no Cloudflare token in the run; a site's pull request carries screenshots of a local build. A reviewer sees a real URL on staging (CFR-2) before a release; nothing outside the production stage deploys production, unless the repository's delivery documentation names another job that may.
  Why: a Workers token cannot be limited to one script and a Pages token reaches every branch, so a token in pull request runs could deploy production.
  Check: the pull request run compiles no deploy stage and uses no secret that holds a Cloudflare token; `wrangler deploy` (or `wrangler pages deploy` to the production branch) appears only in the production stage and in the jobs the documentation names.

- **CFR-2** Staging is its own Worker environment (`env.staging` in the wrangler config, with its own route), deployed from the default branch; production deploys from the release tag.
  Why: staging must not share a name or a route with production, or a staging deploy replaces the live site.
  Check: `npx wrangler deploy --env staging --dry-run` names the staging Worker and route.
  For a Pages site, staging is the branch deployment `staging` (`wrangler pages deploy --branch staging`, at `staging.<project>.pages.dev`, behind the same Access application) and production the project's production branch; check that the staging deploy names `--branch staging`.

- **CFR-3** Roll production back with `npx wrangler rollback <previous version id>` when the check after a deploy fails, and tell the owner at once.
  Why: going back to a version already released is safer than waiting for a fix.
  Check: the report names the version rolled back to and the check that passed after it.
