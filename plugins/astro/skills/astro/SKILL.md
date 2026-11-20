---
name: astro
description: "Rules for Astro static sites: clean installs and astro check, braces in .astro markup, theme helpers against the content schema, public URLs in links, escaping search input, redirects when served by Cloudflare Workers, and social-image caches after a deploy. Use when writing, changing, reviewing or fixing an Astro site: pages, layouts, components, styles, content collections and loaders, astro.config.*; recognise it by an astro.config.mjs, astro.config.ts or *.astro files. Triggers: Astro, Astro site, .astro, astro check, content collections, Astro theme. Not for the texts the site publishes, the Worker or Pages project that serves it (cloudflare skill), or a React, Next.js or other front-end framework app."
license: MIT
metadata:
  version: "1.0.0"
  aliases: "astro site, astro.build"
---

# Astro

What is particular to an Astro static site. When the site is served by a Cloudflare Worker or Pages project, that part follows `cloudflare`, if installed.

## When

- Use for the site's code: pages, layouts, components, styles, content collections and loaders, `astro.config.*`.
- Not for the texts themselves, and not for the Worker or Pages project that serves the site.

## How to work

1. Find where the content comes from: the content config, a loader that reads another folder or repository at build time, and the variable that names it. Build with the same content the pipeline uses.
2. Use the Node version in `.nvmrc` and a clean install (`npm ci`) (ASB-1).
3. Build and check: `npm run build` and `npx astro check`. Then open the built HTML for what you changed (ASB-2, ASB-3).
4. Find what a merge deploys (the repository's pipeline or its delivery documentation) and settle every visible text before it.

## Rules

Read [rules.md](rules.md) and follow every rule. Cite a rule by its ID and this skill's version when you apply or break it, for example "breaks ASB-2 (astro 1.0.0)".
