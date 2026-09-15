"""Static marketing/policy pages for crawlability and AdSense site structure."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import HTMLResponse

SITE_NAV = """
<nav class="site-nav" aria-label="Site">
  <a href="/">Home</a><span class="nav-sep" aria-hidden="true">·</span>
  <a href="/about">About</a><span class="nav-sep" aria-hidden="true">·</span>
  <a href="/how-it-works">How it works</a><span class="nav-sep" aria-hidden="true">·</span>
  <a href="/guides">Guides</a><span class="nav-sep" aria-hidden="true">·</span>
  <a href="/privacy">Privacy</a>
</nav>
"""

PAGE_CSS = """
:root {
  --felt: #0d2a24;
  --felt-deep: #071914;
  --ink: #e8efe9;
  --muted: #9bb5ab;
  --amber: #e4a03a;
  --line: rgba(232, 239, 233, 0.12);
  --font-ui: "Outfit", sans-serif;
  --font-brand: "Syne", sans-serif;
}
* { box-sizing: border-box; }
html, body {
  margin: 0;
  min-height: 100%;
  font-family: var(--font-ui);
  color: var(--ink);
  background:
    radial-gradient(ellipse 90% 60% at 50% -10%, #1a4a3e 0%, transparent 55%),
    linear-gradient(165deg, var(--felt) 0%, var(--felt-deep) 100%);
  background-attachment: fixed;
}
.wrap {
  width: min(640px, 100%);
  margin: 0 auto;
  padding: 1rem 1.1rem 2.5rem;
}
.site-nav {
  font-size: 0.68rem;
  font-weight: 400;
  letter-spacing: 0.04em;
  color: rgba(155, 181, 171, 0.38);
  margin: 0 0 1.25rem;
  line-height: 1.5;
}
.site-nav a {
  color: inherit;
  text-decoration: none;
}
.site-nav a:hover,
.site-nav a:focus-visible {
  color: rgba(155, 181, 171, 0.7);
}
.nav-sep { margin: 0 0.4rem; opacity: 0.8; }
.brand-link {
  font-family: var(--font-brand);
  font-weight: 800;
  font-size: 1.35rem;
  color: var(--ink);
  text-decoration: none;
  letter-spacing: -0.02em;
}
.brand-link:hover { color: var(--amber); }
h1 {
  font-family: var(--font-brand);
  font-size: clamp(1.6rem, 5vw, 2rem);
  font-weight: 800;
  letter-spacing: -0.02em;
  margin: 0.6rem 0 0.75rem;
}
h2 {
  font-size: 1.05rem;
  font-weight: 600;
  margin: 1.4rem 0 0.45rem;
}
p, li {
  color: var(--muted);
  font-size: 0.95rem;
  line-height: 1.55;
}
p { margin: 0 0 0.85rem; }
ul { margin: 0 0 1rem; padding-left: 1.2rem; }
li { margin: 0 0 0.35rem; }
a.inline { color: var(--amber); }
.cta {
  display: inline-block;
  margin-top: 0.5rem;
  padding: 0.7rem 1rem;
  border-radius: 12px;
  background: linear-gradient(180deg, var(--amber) 0%, #c47e18 100%);
  color: #1a1208;
  font-weight: 600;
  text-decoration: none;
  font-size: 0.92rem;
}
.guide-list { list-style: none; padding: 0; }
.guide-list li {
  margin: 0 0 0.75rem;
  padding: 0.85rem 0.9rem;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: rgba(7, 25, 20, 0.35);
}
.guide-list a {
  color: var(--ink);
  font-weight: 600;
  text-decoration: none;
}
.guide-list a:hover { color: var(--amber); }
.guide-list p { margin: 0.35rem 0 0; font-size: 0.88rem; }
"""


def render_site_page(
    request: Request,
    *,
    origin: str,
    title: str,
    description: str,
    path: str,
    body_html: str,
    json_ld: str | None = None,
) -> HTMLResponse:
    canonical = f"{origin}{path}"
    ld_block = f'\n  <script type="application/ld+json">\n{json_ld}\n  </script>' if json_ld else ""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <title>{title}</title>
  <meta name="description" content="{description}" />
  <meta name="robots" content="index,follow" />
  <meta name="theme-color" content="#0d2a24" />
  <link rel="canonical" href="{canonical}" />
  <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="TableScore" />
  <meta property="og:title" content="{title}" />
  <meta property="og:description" content="{description}" />
  <meta property="og:url" content="{canonical}" />
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-7115873505287711"
     crossorigin="anonymous"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&family=Syne:wght@700;800&display=swap" rel="stylesheet" />
  <style>{PAGE_CSS}</style>{ld_block}
</head>
<body>
  <div class="wrap">
    {SITE_NAV}
    <a class="brand-link" href="/">TableScore</a>
    {body_html}
  </div>
</body>
</html>"""
    return HTMLResponse(html)


ABOUT_BODY = """
<h1>About TableScore</h1>
<p>
  TableScore is a free live scoreboard for board game night. It runs in the browser on phones
  and laptops so everyone at the table can follow the same scores without passing a paper pad
  or installing an app.
</p>
<p>
  One person creates a room, names the game, and adds players. TableScore generates a short
  four-letter password. Everyone else opens the site, enters that password, and joins the same
  room. When someone updates a score, the rest of the table sees it update live.
</p>
<p>
  The product is built for custom and house-ruled games—not a locked list of titles. You choose
  how winning works (high or low score), how the game ends, and whether you score round-by-round
  or as a running total.
</p>
<p>
  TableScore is made for people who already play board games together and want less friction
  keeping track: families, game groups, cafés, and casual nights where phones are already on the table.
</p>
<p><a class="cta" href="/">Open the scoreboard</a></p>
"""

HOW_IT_WORKS_BODY = """
<h1>How TableScore works</h1>
<p>
  TableScore keeps a shared live room for your table. Here is the usual flow from empty lobby
  to finished game.
</p>
<h2>1. Create a room</h2>
<p>
  On the home page, enter a game name and the players at your table. TableScore assigns a
  four-letter room password. Share that word out loud or in your group chat—anyone with the
  password can join the same scoreboard.
</p>
<h2>2. Set the rules (custom games)</h2>
<p>
  For custom games you pick how to win (highest or lowest score), how the match ends (manually
  or at a target score), and how you keep score (in rounds or incrementally). Optional notes
  and a description field are there for house rules or a link to the rulebook.
</p>
<h2>3. Score together</h2>
<p>
  On the live scorecard, update points as play happens. Other devices in the room refresh
  automatically, so the person across the table sees the same totals. You can add a player mid-game,
  complete rounds when you play that way, or end the game when you are done.
</p>
<h2>4. Play again</h2>
<p>
  After a match you can reset scores for another game with the same players and rules, or leave
  the room and start fresh from the lobby.
</p>
<p>
  No accounts are required to create or join a room. Rooms are temporary scoring sessions for
  people already sitting together—not a social network or public leaderboard site.
</p>
<p><a class="cta" href="/">Create a room</a></p>
"""

PRIVACY_BODY = """
<h1>Privacy</h1>
<p>
  This Privacy page explains what TableScore collects when you use boardgameallstars.com
  (the “Service”).
</p>
<h2>What the Service is for</h2>
<p>
  TableScore provides temporary live scoring rooms for board game nights. You create a room,
  share a password, and enter player names and scores so devices at the table stay in sync.
</p>
<h2>Information we process</h2>
<ul>
  <li><strong>Room data you enter:</strong> game name, player names, scores, and optional notes or rule settings for that session.</li>
  <li><strong>Technical data:</strong> standard server logs such as IP address, browser type, and timestamps, used to operate and secure the Service.</li>
  <li><strong>Advertising:</strong> if Google AdSense (or similar) is enabled, Google may use cookies or similar technologies to serve ads. See Google’s policies for details on how they process data.</li>
</ul>
<h2>How we use information</h2>
<p>
  Room data exists so your table can score together. We use technical logs to keep the Service
  running, debug issues, and prevent abuse. We do not sell personal information.
</p>
<h2>Retention</h2>
<p>
  Scoring rooms are temporary. Inactive or ended rooms are cleaned up automatically after a
  short period so passwords can be reused. Logs are kept only as long as needed for operations
  and security.
</p>
<h2>Cookies and ads</h2>
<p>
  The core scoreboard does not require an account login cookie. Third-party ad partners may set
  their own cookies subject to your browser settings and their policies.
</p>
<h2>Children</h2>
<p>
  The Service is a general-purpose scoring tool. If you use it with a family game night, an adult
  should create and manage the room.
</p>
<h2>Contact</h2>
<p>
  Questions about this policy can be sent via the contact method listed on your AdSense / site
  owner account for boardgameallstars.com.
</p>
<p><a class="inline" href="/">Back to TableScore</a></p>
"""

GUIDES_INDEX_BODY = """
<h1>Guides</h1>
<p>
  Short, practical notes on using a live scoreboard at game night. These pages are written for
  TableScore on boardgameallstars.com.
</p>
<ul class="guide-list">
  <li>
    <a href="/guides/live-board-game-scoreboard">Live board game scoreboard at the table</a>
    <p>Why a shared phone scoreboard beats a paper pad when everyone already has a device out.</p>
  </li>
  <li>
    <a href="/guides/board-game-scorekeeper">Free board game scorekeeper for custom games</a>
    <p>How to set win conditions, targets, and round scoring for house rules—not just one published title.</p>
  </li>
</ul>
<p><a class="cta" href="/">Open TableScore</a></p>
"""

GUIDE_LIVE_BODY = """
<h1>Live board game scoreboard at the table</h1>
<p>
  Most game nights already have phones on the table. A live scoreboard uses that fact: one shared
  room, one password, scores that update for everyone without rewriting a paper pad after every round.
</p>
<h2>What “live” means here</h2>
<p>
  In TableScore, live means devices in the same room stay synchronized while you play. When someone
  changes a score, other phones refresh on their own. You are not uploading a public profile or
  competing with strangers online—you are keeping the same sheet of numbers visible to your table.
</p>
<h2>A simple setup that works</h2>
<ul>
  <li>One person opens TableScore and creates the room with player names.</li>
  <li>They read the four-letter password out loud.</li>
  <li>Everyone else joins on their own phone.</li>
  <li>Update scores as turns finish; glance at the board instead of asking “what’s the total?”</li>
</ul>
<h2>When it helps most</h2>
<p>
  Live scoring shines in longer games, multi-round games, and nights with four or more players—
  anywhere a paper scoresheet gets crowded or someone forgets to carry a total forward. It also
  helps when players sit around a large table and cannot easily see one central sheet.
</p>
<p>
  If you want to try it, create a room on the home page and keep the first game simple: enter
  names, share the password, and update points as you go.
</p>
<p><a class="cta" href="/">Start a live scoreboard</a></p>
<p><a class="inline" href="/guides">All guides</a></p>
"""

GUIDE_SCOREKEEPER_BODY = """
<h1>Free board game scorekeeper for custom games</h1>
<p>
  Many score apps assume a fixed catalog of titles. TableScore is built as a free scorekeeper for
  the games you already play—including custom maps, expansions, and house rules that do not match
  a preset template.
</p>
<h2>Rules you can set</h2>
<ul>
  <li><strong>How to win:</strong> highest score or lowest score (useful for games that count down).</li>
  <li><strong>How to end:</strong> stop manually when the group is done, or use a target score.</li>
  <li><strong>How to keep score:</strong> running totals, or round-by-round with a round history.</li>
  <li><strong>Sorting:</strong> by score or in a manual seat order that matches the table.</li>
</ul>
<h2>Why custom matters</h2>
<p>
  House rules change scoring all the time: alternate win conditions, team scores tracked as
  separate players, or “start at 501 and go down.” A flexible scorekeeper lets you encode those
  choices once at setup, then focus on the game instead of reinventing a spreadsheet.
</p>
<h2>Getting started</h2>
<p>
  Create a room, name the game whatever you call it at your table, add players, then complete the
  short setup form. Share the room password so every phone shows the same scorekeeper. When the
  night is over, leave the room—sessions are temporary and meant for people playing together in person.
</p>
<p><a class="cta" href="/">Use the free scorekeeper</a></p>
<p><a class="inline" href="/guides">All guides</a></p>
"""

SITEMAP_PATHS = [
    "/",
    "/about",
    "/how-it-works",
    "/privacy",
    "/guides",
    "/guides/live-board-game-scoreboard",
    "/guides/board-game-scorekeeper",
]
