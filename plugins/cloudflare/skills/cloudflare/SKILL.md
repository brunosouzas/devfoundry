---
name: cloudflare
description: "Rules for Cloudflare Workers and Pages: the wrangler config and Worker name, one route table, vitest gating the build, inbound webhook signatures, replay windows and allowlists, secrets, removing routes and Durable Objects, Workers Builds commands, tunnels to a local service, staging and production environments, deploy tokens kept out of pull requests, and rollbacks. Use when writing, changing, reviewing or deploying a Cloudflare Worker, or the deploy of a site to Cloudflare Pages; recognise it by a wrangler.toml, wrangler.json or wrangler.jsonc, or wrangler deploy or wrangler pages deploy in a pipeline. Triggers: Cloudflare, Cloudflare Workers, Cloudflare Pages, Wrangler, Durable Objects, Workers Builds, webhook worker. Not for the site's own pages and build (astro skill), the pipeline YAML around a deploy (azure-devops or github-actions skill), or DNS and zone settings."
license: MIT
metadata:
  version: "1.0.0"
  aliases: "cloudflare workers, cloudflare pages, wrangler"
---

# Cloudflare

What is particular to Cloudflare Workers and to deploying a site on Cloudflare Pages. A site built with Astro follows `astro` for its pages and build, if installed; the pipeline that deploys follows its own skill.

## When

- Use for Worker code, the wrangler config, routes, Durable Objects, Workers Builds settings, and Pages staging and production deploys.
- Not for the site's content and build, and not for DNS or zone settings.

## How to work

1. Read the wrangler config, the route table and the README's list of routes and secrets (CFL-2, CFW-4).
2. Run `npm test` (vitest) and `npx wrangler dev` for anything that depends on routing or redirects.
3. Find what a merge deploys (Workers Builds settings, or the repository's pipeline): production straight from the default branch, or staging from it and production from a release tag (CFR-2). Say in the pull request what the merge changes in production.

## Rules

Read [rules.md](rules.md) and follow every rule. Cite a rule by its ID and this skill's version when you apply or break it, for example "breaks CFW-1 (cloudflare 1.0.0)".
