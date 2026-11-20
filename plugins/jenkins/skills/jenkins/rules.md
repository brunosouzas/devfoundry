# Jenkins: rules

Rules for Jenkins pipelines, from common practice. In an existing project, follow the conventions it already uses and report a difference instead of rewriting; these rules decide new pipelines and steps.

How to change this file (see CONTRIBUTING.md of this repository):
- **Add a rule:** copy an item, give it the next number in its group, write the rule, why it exists and how to check it. A new rule is a MINOR version.
- **Change a rule:** edit it in place and keep its ID, so old reviews still point at the right rule. A rule that now says the opposite is a MAJOR version; clearer wording is a PATCH.
- **Retire a rule:** keep its ID and heading, replace the text with `(retired in <version>: <reason>)`, and never reuse the number. A retired rule is a MAJOR version.

## Pipelines (JNK)

- **JNK-1** Prefer declarative pipelines; keep logic in shared-library steps, not in the `Jenkinsfile`.
  Why: a short `Jenkinsfile` is readable and the logic in the library can be tested and reused.
  Check: no long `script {}` blocks in the `Jenkinsfile`.

- **JNK-2** Keep shared-library step signatures backward compatible; add optional parameters with defaults instead of changing existing ones.
  Why: every job using the library breaks at once otherwise.
  Check: changed steps in `vars/` accept the old call.

- **JNK-3** Fail on purpose: let errors propagate, and use `catchError` or `try` only to clean up or report, then rethrow.
  Why: a swallowed failure turns a red build green.
  Check: every `catch` rethrows or sets the build result.

- **JNK-4** Check what a retry or a parallel branch does to artifacts and the workspace before adding one.
  Why: a retried deploy can deploy twice; parallel branches can delete each other's files.
  Check: retried steps are idempotent; parallel branches use separate folders.

## Secrets (JNKS)

- **JNKS-1** Use `withCredentials` with the narrowest credential scope, and reference the variable inside single-quoted `sh '…$TOKEN…'`.
  Why: double-quoted Groovy strings interpolate the secret into the command text, where it can leak; Jenkins warns about it.
  Check: no secret variables inside `sh "…"` with double quotes.

- **JNKS-2** Never interpolate user-controlled parameters into shell commands; pass them as environment variables.
  Why: a parameter like `; rm -rf /` becomes part of the command.
  Check: parameters reach `sh` through `withEnv` or `environment {}`.
