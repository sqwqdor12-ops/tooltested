#!/usr/bin/env python3
"""
ToolTested static blog generator.

Zero dependencies. Reads posts/*.md (frontmatter + markdown subset),
emits a fully SEO-optimized static site into site/ :
  - index.html (article list)
  - article pages with meta/OG/Twitter tags + JSON-LD
  - sitemap.xml, rss.xml, robots.txt, 404.html
Inline critical CSS, no JS, no external requests => ~100 Lighthouse.
Usage: python3 build.py
"""
import os, re, html, glob, datetime

SITE_URL = os.environ.get("SITE_URL", "https://tooltested.github.io")
SITE_NAME = "ToolTested"
SITE_TAGLINE = "Hands-on AI tool guides that actually work"
OUTPUT = "site"
POSTS_DIR = "posts"


def md_to_html(text):
    """Tiny markdown subset: headings, bold, italic, code, links, lists, paras, quotes."""
    lines = text.split("\n")
    out, in_list, in_code, code_buf = [], False, False, []

    def inline(s):
        s = html.escape(s)
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", s)
        s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
        return s

    for line in lines:
        if line.strip().startswith("```"):
            if in_code:
                out.append("<pre><code>" + html.escape("\n".join(code_buf)) + "</code></pre>")
                code_buf, in_code = [], False
            else:
                if in_list: out.append("</ul>"); in_list = False
                in_code = True
            continue
        if in_code:
            code_buf.append(line); continue
        m = re.match(r"^(#{1,3})\s+(.*)", line)
        if m:
            if in_list: out.append("</ul>"); in_list = False
            lvl = len(m.group(1))
            # shift so page h1 stays unique; post title is the only h1
            lvl = lvl if lvl > 1 else 2
            out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>")
            continue
        m = re.match(r"^\s*[-*]\s+(.*)", line)
        if m:
            if not in_list: out.append("<ul>"); in_list = True
            out.append(f"<li>{inline(m.group(1))}</li>")
            continue
        if in_list: out.append("</ul>"); in_list = False
        m = re.match(r"^>\s?(.*)", line)
        if m:
            out.append(f"<blockquote><p>{inline(m.group(1))}</p></blockquote>")
            continue
        if line.strip() == "":
            continue
        out.append(f"<p>{inline(line)}</p>")
    if in_list: out.append("</ul>")
    if in_code: out.append("<pre><code>" + html.escape("\n".join(code_buf)) + "</code></pre>")
    return "\n".join(out)


def parse_post(path):
    raw = open(path, encoding="utf-8").read()
    fm, body = raw, ""
    if raw.startswith("---"):
        _, fm, body = raw.split("---", 2)
    meta = {}
    for line in fm.strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip().lower()] = v.strip()
    return meta, body.strip()


def slugify(title):
    s = re.sub(r"[^a-z0-9\s-]", "", title.lower())
    return re.sub(r"[\s-]+", "-", s).strip("-")


CSS = """
:root{--bg:#faf9f7;--fg:#1a1a1a;--muted:#666;--accent:#0b57d0;--card:#fff;--border:#e5e2dd;--code:#f2f0ec}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{font:400 17px/1.7 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;background:var(--bg);color:var(--fg)}
.wrap{max-width:720px;margin:0 auto;padding:0 20px}
header.site{border-bottom:1px solid var(--border);padding:20px 0;margin-bottom:40px}
header.site .wrap{display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px}
.logo{font-weight:800;font-size:1.35rem;color:var(--fg);text-decoration:none;letter-spacing:-.02em}
.logo span{color:var(--accent)}
.tagline{color:var(--muted);font-size:.9rem}
h1{font-size:1.9rem;line-height:1.25;letter-spacing:-.02em;margin-bottom:12px}
h2{font-size:1.45rem;margin:2em 0 .6em;letter-spacing:-.01em}
h3{font-size:1.15rem;margin:1.6em 0 .5em}
p{margin-bottom:1em}
a{color:var(--accent)}
ul{margin:0 0 1em 1.2em}
li{margin-bottom:.4em}
blockquote{border-left:4px solid var(--accent);padding:.4em 1em;margin:1.2em 0;color:var(--muted);background:var(--card);border-radius:0 8px 8px 0}
code{background:var(--code);padding:.15em .4em;border-radius:4px;font-size:.9em}
pre{background:var(--code);padding:16px;border-radius:8px;overflow-x:auto;margin:1.2em 0}
pre code{padding:0;background:none}
article.post{margin-bottom:44px;padding-bottom:44px;border-bottom:1px solid var(--border)}
article.post time{color:var(--muted);font-size:.85rem;text-transform:uppercase;letter-spacing:.05em}
article.post .excerpt{color:var(--muted);margin-top:.4em}
.readmore{font-weight:600}
.meta{color:var(--muted);font-size:.9rem;margin-bottom:28px}
.toc{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:18px 22px;margin:28px 0}
.toc strong{display:block;margin-bottom:6px}
.toc ul{margin-left:1.2em}
footer.site{border-top:1px solid var(--border);padding:32px 0 48px;margin-top:40px;color:var(--muted);font-size:.9rem}
.kicker{color:var(--accent);font-weight:700;font-size:.8rem;text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px}
@media (prefers-color-scheme:dark){:root{--bg:#141414;--fg:#eaeaea;--muted:#999;--card:#1e1e1e;--border:#2c2c2c;--code:#242424}}
"""

HTML_SHELL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{url}">
<meta property="og:site_name" content="__NAME__">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{description}">
<script type="application/ld+json">{jsonld}</script>
<style>{css}</style>
</head>
<body>
<header class="site"><div class="wrap"><a class="logo" href="/">Tool<span>Tested</span></a><span class="tagline">{tagline}</span></div></header>
<main class="wrap">
{body}
</main>
<footer class="site"><div class="wrap"><p>__NAME__ &mdash; __TAGLINE__. Independent, hands-on, no affiliate fluff.</p><p><a href="/rss.xml">RSS</a> &middot; <a href="/sitemap.xml">Sitemap</a></p></div></footer>
</body>
</html>"""


def page(title, description, url, body_html, jsonld, og_type="article"):
    shell = (HTML_SHELL.replace("__NAME__", SITE_NAME)
             .replace("__TAGLINE__", SITE_TAGLINE))
    return shell.format(
        title=html.escape(title), description=html.escape(description),
        url=url, body=body_html, jsonld=jsonld, css=CSS, tagline=SITE_TAGLINE,
    )


def main():
    posts = []
    for path in sorted(glob.glob(os.path.join(POSTS_DIR, "*.md"))):
        meta, body = parse_post(path)
        slug = meta.get("slug") or slugify(meta.get("title", os.path.basename(path)))
        posts.append({
            "title": meta.get("title", "Untitled"),
            "description": meta.get("description", ""),
            "date": meta.get("date", "2026-01-01"),
            "body": body,
            "slug": slug,
            "html": md_to_html(body),
        })

    posts.sort(key=lambda p: p["date"], reverse=True)
    os.makedirs(OUTPUT, exist_ok=True)
    iso_now = datetime.date.today().isoformat()

    # index
    items = []
    for p in posts:
        d = datetime.date.fromisoformat(p["date"]).strftime("%b %-d, %Y") if re.match(r"^\d{4}-\d{2}-\d{2}$", p["date"]) else p["date"]
        items.append(f'<article class="post"><time datetime="{p["date"]}">{d}</time><h2><a href="/{p["slug"]}/">{html.escape(p["title"])}</a></h2><p class="excerpt">{html.escape(p["description"])}</p><p><a class="readmore" href="/{p["slug"]}/">Read the guide &rarr;</a></p></article>')
    idx_jsonld = ('{"@context":"https://schema.org","@type":"Blog","name":"%s",'
                  '"description":"%s","url":"%s/"}' % (SITE_NAME, SITE_TAGLINE, SITE_URL))
    idx_body = ('<h1>Hands-on AI tool guides, tested by a human</h1>'
                '<p class="meta">Every guide on %s is written after actually running the tool. '
                'Real steps, real screenshots-in-words, zero fluff.</p>' % SITE_NAME
                ) + "\n".join(items)
    open(os.path.join(OUTPUT, "index.html"), "w", encoding="utf-8").write(
        page(f"{SITE_NAME} — {SITE_TAGLINE}", SITE_TAGLINE, f"{SITE_URL}/", idx_body, idx_jsonld))

    # posts
    urls = []
    for p in posts:
        body = (f'<h1>{html.escape(p["title"])}</h1>'
                f'<p class="meta"><time datetime="{p["date"]}">{p["date"]}</time> &middot; {SITE_NAME}</p>'
                + p["html"])
        jsonld = ('{"@context":"https://schema.org","@type":"TechArticle",'
                  '"headline":"%s","description":"%s","datePublished":"%s",'
                  '"dateModified":"%s","author":{"@type":"Organization","name":"%s"},'
                  '"publisher":{"@type":"Organization","name":"%s"},'
                  '"mainEntityOfPage":"%s/%s/"}'
                  % (p["title"].replace('"', "'"), p["description"].replace('"', "'"),
                     p["date"], p["date"], SITE_NAME, SITE_NAME, SITE_URL, p["slug"]))
        d = os.path.join(OUTPUT, p["slug"])
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(
            page(p["title"], p["description"], f"{SITE_URL}/{p['slug']}/", body, jsonld))
        urls.append((f"{SITE_URL}/{p['slug']}/", p["date"]))

    # sitemap
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm.append(f"<url><loc>{SITE_URL}/</loc><lastmod>{iso_now}</lastmod><priority>1.0</priority></url>")
    for u, d in urls:
        sm.append(f"<url><loc>{u}</loc><lastmod>{d}</lastmod></url>")
    sm.append("</urlset>")
    open(os.path.join(OUTPUT, "sitemap.xml"), "w").write("\n".join(sm))

    # rss
    rss = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<rss version="2.0"><channel>',
           f"<title>{SITE_NAME}</title>",
           f"<link>{SITE_URL}/</link>",
           f"<description>{SITE_TAGLINE}</description>"]
    for p in posts[:20]:
        rss.append(f"<item><title>{html.escape(p['title'])}</title>"
                   f"<link>{SITE_URL}/{p['slug']}/</link>"
                   f"<description>{html.escape(p['description'])}</description>"
                   f"<pubDate>{p['date']}</pubDate></item>")
    rss.append("</channel></rss>")
    open(os.path.join(OUTPUT, "rss.xml"), "w").write("\n".join(rss))

    # robots + 404
    open(os.path.join(OUTPUT, "robots.txt"), "w").write(
        f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
    open(os.path.join(OUTPUT, "404.html"), "w", encoding="utf-8").write(
        page("404 — not found", "Page not found", f"{SITE_URL}/404.html",
             "<h1>404</h1><p>That page wandered off. <a href='/'>Back to the guides &rarr;</a></p>",
             '{}'))
    print(f"Built {len(posts)} posts into {OUTPUT}/")


if __name__ == "__main__":
    main()
