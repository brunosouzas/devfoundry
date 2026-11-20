# Java: rules

Rules for standalone Java code, from common practice. In an existing project, follow the conventions it already uses and report a difference instead of rewriting; these rules decide new code.

How to change this file (see CONTRIBUTING.md of this repository):
- **Add a rule:** copy an item, give it the next number in its group, write the rule, why it exists and how to check it. A new rule is a MINOR version.
- **Change a rule:** edit it in place and keep its ID, so old reviews still point at the right rule. A rule that now says the opposite is a MAJOR version; clearer wording is a PATCH.
- **Retire a rule:** keep its ID and heading, replace the text with `(retired in <version>: <reason>)`, and never reuse the number. A retired rule is a MAJOR version.

## Build (JBLD)

- **JBLD-1** Build with the JDK and wrapper the project declares; never rely on whatever `java` is on the PATH.
  Why: code that compiles on a newer JDK can fail on the runtime that deploys it.
  Check: the build uses `./mvnw` or `./gradlew` and the declared release level.

- **JBLD-2** Declare dependency versions where the project manages them (parent, BOM, catalog), not inline in a module.
  Why: two versions of one library on the classpath fail at runtime, not at build.
  Check: no new hard-coded version in a module that inherits its versions.

- **JBLD-3** A Maven release (`release:prepare release:perform`) runs only in the release pipeline; never run `mvn release:*` by hand, and run `versions:set` by hand only where the project's documented release process names that step (for example setting the snapshot version on the first commit of a maintenance branch).
  Why: the release pipeline is what tags, publishes and records the version; a release from a workstation has no record and can publish code that is not on the default branch.
  Check: no release commits pushed from a workstation (`[maven-release-plugin]` commits come from the pipeline identity).

## Code (JAVA)

- **JAVA-1** Close every resource with try-with-resources.
  Why: a leaked stream, connection or thread survives the happy path and kills the service later.
  Check: every `Closeable` opened in new code is in a try-with-resources.

- **JAVA-2** Do not return `null` for "nothing": return an empty collection or `Optional`.
  Why: every caller has to remember a null check, and one will not.
  Check: new public methods never return `null` collections.

- **JAVA-3** Catch the specific exception you can handle; never catch `Exception` or `Throwable` just to log and continue.
  Why: a broad catch hides the bug and leaves the state half-done.
  Check: search the diff for `catch (Exception` and `catch (Throwable`.

- **JAVA-4** Keep public method signatures, serialised fields and exception types stable unless the change says otherwise.
  Why: callers and stored data depend on them.
  Check: the diff of public types matches the change's scope.

- **JAVA-5** Prefer immutable objects (final fields, records) for data that crosses a boundary.
  Why: shared mutable state is the commonest source of concurrency bugs.
  Check: new data classes are records or have final fields.

## Tests (JTST)

- **JTST-1** Test names say the behaviour (`rejectsOrderWithoutCustomerId`), one behaviour per test.
  Why: the failing test's name should tell you what broke.
  Check: read the test names in the diff.

- **JTST-2** Mock only what crosses a boundary (HTTP, database, clock); test your own classes for real.
  Why: mocking your own code tests the mock.
  Check: no mocks of classes from the same module without a reason.
