---
name: jenkins
description: "Rules for Jenkins pipelines: declarative Jenkinsfiles, Groovy shared libraries and their step signatures, failure handling, retries and parallel branches, credentials and parameters in sh steps. Use when writing, changing, reviewing or debugging a Jenkinsfile or a shared library (vars/*.groovy, src/), and the shell steps they run; recognise it by a Jenkinsfile, a vars/ folder of a shared library or @Library in a pipeline. Triggers: Jenkins, Jenkinsfile, Jenkins pipeline, shared library, Groovy pipeline, withCredentials. Not for GitHub Actions workflows (github-actions skill), Azure Pipelines (azure-devops skill), Groovy outside Jenkins, or the shell script a step calls on its own (shell skill)."
license: MIT
metadata:
  version: "1.0.0"
  aliases: "jenkinsfile, groovy, jenkins pipeline"
---

# Jenkins

What is particular to Jenkins pipelines. The branch strategy and deploy process a pipeline implements come from the repository's delivery process. Shell steps also follow `shell`, if installed.

## When

- Use for declarative or scripted `Jenkinsfile`s and Groovy shared libraries.
- Not for deciding the delivery process. Not for GitHub Actions or Azure Pipelines: `github-actions` or `azure-devops`, if installed.

## How to work

1. Find every job that calls a shared-library step you change (`vars/<step>.groovy`) and keep its signature working (JNK-2).
2. Remember where code runs: pipeline Groovy runs on the controller under CPS and the sandbox; `sh` steps run on the agent. A plain Groovy test does not prove CPS or sandbox behaviour.
3. Verify: the library's unit tests (JenkinsPipelineUnit or Spock) when it has them, a replay or a run on a branch job for anything else. Report a local test and a Jenkins run separately.

## Rules

Read [rules.md](rules.md) and follow every rule. Cite a rule by its ID and this skill's version when you apply or break it, for example "breaks JNKS-1 (jenkins 1.0.0)".
