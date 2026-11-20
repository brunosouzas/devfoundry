---
name: java
description: "Rules for standalone Java code: the JDK and build the project declares (Maven or Gradle wrapper), dependency management, releases, resources, nulls, exceptions, stable public types and JUnit tests. Use when writing, changing, reviewing or fixing a Java application, library or CLI and its tests; recognise it by a pom.xml whose packaging is jar, war or pom (not a Mule one), a build.gradle or build.gradle.kts, or *.java sources. Triggers: Java, JDK, JUnit, JUnit 5, Maven, Gradle, Spring Boot, Mockito, AssertJ. Not for a Mule application, plugin or connector even when it has Java inside (the mule-engineering plugin of mulesmith), Groovy in a Jenkins shared library (jenkins skill), or Python code (python skill)."
license: MIT
metadata:
  version: "1.0.0"
  aliases: "jdk, junit, gradle, maven, spring boot"
---

# Java

What is particular to standalone Java code: an application, a library or a CLI, and its JUnit tests.

## When

- Use for a standalone Java application, library or CLI, its build (Maven or Gradle) and its JUnit tests.
- Not for a Mule application, plugin or connector, even when it has Java inside: those follow the `mule-engineering` skills of the public `mulesmith` marketplace, if installed.

## How to work

1. Find the JDK and build tool the project really uses: `.java-version`, `.sdkmanrc`, `maven.compiler.release` or the Gradle toolchain, the wrapper (`./mvnw`, `./gradlew`). Use the wrapper when there is one (JBLD-1).
2. Find where dependency versions are managed (parent POM, BOM, `dependencyManagement`, version catalog) before adding one (JBLD-2).
3. Write the JUnit test first for a fix; use the test style already in the project (JUnit 5, AssertJ, Mockito).
4. Verify: `./mvnw -q verify` or `./gradlew check`, plus the project's own checks.

## Rules

Read [rules.md](rules.md) and follow every rule. Cite a rule by its ID and this skill's version when you apply or break it, for example "breaks JAVA-3 (java 1.0.0)".
