# ToolTested

A free, zero-dependency, SEO-maxed static blog. Hands-on AI tool guides.

**The whole stack:** Python 3 (built in) + GitHub Pages (free hosting) + GitHub Actions (free CI/CD). No Node, no framework, no npm, nothing to break.

## Why this is "crazy optimized"

- **Zero JavaScript.** Pure HTML + inline CSS. Pages are ~15 KB, load in under 200 ms.
- **Critical CSS inlined** — no render-blocking requests at all, not even a stylesheet fetch.
- **Full SEO suite generated automatically**: meta description, Open Graph, Twitter cards, canonical URLs, `TechArticle` JSON-LD schema, `sitemap.xml`, `rss.xml`, `robots.txt`.
- **Clean URLs** (`/slug/`), unique H1 per page, semantic HTML, accessible contrast, dark mode via `prefers-color-scheme`.
- **Ages like fine wine:** every page is static, so there's nothing to hack and nothing to update.

## Write a new post

1. Create `posts/your-post-slug.md`
2. Add frontmatter:

```
---
title: Your Long-Tail Keywordy Title
description: One-sentence description used for meta tags and the homepage.
date: 2026-09-20
slug: your-post-slug
---
Your markdown here...
```

3. `python3 build.py` to preview in `site/`
4. Push to `main` — GitHub Actions builds and deploys automatically.

Supported markdown: `# ## ###` headings, `**bold**`, `*italic*`, `[links](url)`, `- lists`, `> quotes`, `` `code` `` and ``` ```code blocks``` ```.

## Setup (5 minutes)

1. Create a new **public** GitHub repo named `tooltested` (or anything).
2. Upload this folder's contents to it and push.
3. In the repo: **Settings → Pages → Source: GitHub Actions**.
4. Done. Your blog is live at `https://<username>.github.io/tooltested/`.

If you use a custom domain or repo name, set the base URL before building:
`SITE_URL=https://yourdomain.com python3 build.py`

## Local preview

```bash
python3 build.py
python3 -m http.server -d site 8000
```

## Content strategy baked in

The niche is long-tail "AI tool + specific task" guides ("How to use X to do Y") — high-intent searches, high ad RPM, and low competition because big sites only write listicles. Keep every post: one tool, one job, honest verdict.
