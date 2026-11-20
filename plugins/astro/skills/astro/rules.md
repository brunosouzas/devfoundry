# Astro: rules

Rules for Astro static sites, from what real sites needed so far. A site's own editorial rules (what its pages may say) belong to that site's repository, not here.

How to change this file (see CONTRIBUTING.md of this repository):
- **Add a rule:** copy an item, give it the next number in its group, write the rule, why it exists and how to check it. A new rule is a MINOR version.
- **Change a rule:** edit it in place and keep its ID, so old reviews still point at the right rule. A rule that now says the opposite is a MAJOR version; clearer wording is a PATCH.
- **Retire a rule:** keep its ID and heading, replace the text with `(retired in <version>: <reason>)`, and never reuse the number. A retired rule is a MAJOR version.

## Content (AST)

- **AST-4** Never ship placeholder text (a `TODO` note) to a public page.
  Why: a merge that deploys publishes it.
  Check: search the built HTML for `TODO` and judge each hit (an article may talk about TODOs).

## Build (ASB)

- **ASB-1** Build and check from a clean install with the Node in `.nvmrc`; never install a missing peer dependency by hand or keep `legacy-peer-deps=true`.
  Why: a stale `node_modules` hides missing peers; on one site the flag made `astro check` fail on a clean `npm ci`.
  Check: `npm ci && npm run build && npx astro check` passes.

- **ASB-2** Escape a literal brace in `.astro` markup, SVG `<text>` included: write `{"{ }"}`, then search the built HTML for it.
  Why: a bare brace is parsed as an expression and renders empty.
  Check: the built HTML shows the brace.

- **ASB-3** A theme's helpers follow the site's content schema (a field that is a single value, such as `category`, is not treated as an array), and share links use the entry's public URL, not its collection id (`post.id`).
  Why: themes assume arrays and internal ids.
  Check: share links in the built HTML are public URLs.

- **ASB-4** Escape user input before building a RegExp for search or highlight.
  Why: input with `[` or `(` throws.
  Check: search code escapes input.

- **ASB-5** When the site is served by a Cloudflare Worker, test redirects with `wrangler dev`: Workers' default trailing-slash handling redirects `/about` to `/about/`.
  Why: a link that works in `astro dev` can redirect in production.
  Check: internal links in the built HTML end the way the Worker serves them.

## After deploy (ASD)

- **ASD-1** When the share image or favicon changed, say in the pull request that the image must be refreshed in each network's cache tool (LinkedIn's Post Inspector, for example) after the deploy.
  Why: social networks cache the old image.
  Check: the pull request mentions it when those files change.
