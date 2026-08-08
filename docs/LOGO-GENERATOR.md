# The Badge Forge (`logo.html`)

A members-only page where anyone in the gang can pound out a personalized BKG
badge — their callsign, their BKG number, their choice of metal — and download
it as a PNG or SVG for QSL cards, stickers, and profile pics.

---

## Why it doesn't call an AI image API

The obvious way to build "an image generator" is to POST a prompt to an image
API and show what comes back. That does not work on this site, and it's worth
being clear about why before someone tries it again.

**bkg.club is a static site.** GitHub Pages serves files; there is no server of
ours running anywhere. Every byte of `logo.html` is downloaded by the visitor's
browser and can be read with View Source. On top of that, `jsvana/bkg.club` is a
**public repository**, so the source is readable even without visiting the site.

That rules out putting an API key in the page. An API key in a static page isn't
"a bit risky" — it is published. Scrapers watch GitHub and CDN traffic for exactly
this, and a leaked image-generation key gets drained fast, on our card. No amount
of obfuscation, base64, or "hiding it in a JS file" changes this: whatever the
browser can read, so can everyone else.

So there were two honest options:

1. **Put a real server in front of the key.** A Cloudflare Worker or Netlify/Vercel
   function holds the API key as a server secret, checks the password server-side,
   and proxies the request. This is the correct design *if we want AI generation*.
   It costs money per image, needs an account and a deploy pipeline separate from
   Pages, and needs abuse controls (rate limiting, a spend cap) or one leaked
   password drains the budget.

2. **Don't need a key at all.** Generate the badge locally, in the browser, with
   nothing to protect.

We built #2, because it turned out to be a better fit for what the badge actually
is. Take a look at what we're producing: it's the same badge every time, with
different words on it. That's not a job for a diffusion model — it's a job for a
drawing. Doing it as a drawing is instant, free, works offline, and gives the
*exact same* badge every time instead of a new hallucination of the logo on each
click. `logo.jpg` stays the official mark; the forge redraws it as vector art so
the text can be swapped.

**If we ever do want real AI generation**, see "Adding AI generation later" at the
bottom. The key point: the password check must move to the server at the same
time, because at that point the password would be guarding something that costs
money, and a client-side check guards nothing.

---

## What the password gate actually does

Be precise about this, because "password protected" oversells it.

The passphrase is not stored in this repo. What's in `logo.html` is a random
16-byte salt and the PBKDF2-SHA256 hash (250,000 iterations) of the passphrase.
The browser derives the same hash from what you type and compares. A correct
entry sets a flag in `sessionStorage`, so it lasts for that browser tab.

| | |
|---|---|
| ✅ Keeps out | Drive-by visitors, people who find the URL, search engines (the page is `noindex`) |
| ✅ Avoids | Storing the passphrase in plaintext anywhere in the repo or the page |
| ❌ Does not stop | Anyone willing to run a wordlist against the hash offline |
| ❌ Not suitable for | Anything that costs money per use, or any member data |

The gate is a front door, not a vault. It's the right amount of security here for
one specific reason: **there is nothing valuable behind it.** No API key, no
member PII, no per-click cost. The worst case if someone guesses the passphrase
is that a stranger makes themselves a BKG badge — mildly annoying, not expensive.

That trade-off stops being acceptable the moment something behind the door has a
cost or a secret attached to it. If that day comes, the check moves server-side.

Because the hash ships to every visitor, an offline guessing attack is free and
unlimited. Use a passphrase that isn't in a wordlist. The rotation script
enforces a 10-character minimum for this reason.

---

## Changing the passphrase

```bash
python3 scripts/set-logo-password.py       # prompts twice, input hidden
```

Or non-interactively:

```bash
BKG_LOGO_PASSWORD='...' python3 scripts/set-logo-password.py
```

It rewrites the `/* GATE:START */ … /* GATE:END */` block in `logo.html` with a
fresh random salt and the new hash. Commit `logo.html` and push; it's live on the
next deploy.

Rotate it whenever someone leaves the gang, or if it gets posted somewhere public.

---

## How the badge is drawn

Everything lives in the second `<script>` block of `logo.html`. The badge is
assembled as an SVG string in a 1024×1024 coordinate space, then handed to an
`<img>` for preview and rasterized through a `<canvas>` for PNG export.

Things that are load-bearing and easy to break:

- **Arc text direction.** The top arc runs 9 o'clock → 12 → 3 (`sweep-flag=1`)
  and the bottom arc runs 9 → 6 → 3 (`sweep-flag=0`). Glyphs sit upright to the
  *left* of the direction of travel, so the top text hangs outside its baseline
  radius and the bottom text hangs inside it. That's why `R_ARC_BOT` (424) is
  larger than `R_ARC_TOP` (378) — it makes both bands occupy the same ring.
  Flip either sweep flag and that text renders upside down.

- **Text has to be measured, not guessed.** Glyphs that run past the end of a
  `<textPath>` are silently dropped, so long text would get chopped with no
  warning. Sizes are fitted using a real off-screen SVG `<text>` node and
  `getComputedTextLength()`, not a `<canvas>` `measureText()` estimate — the
  canvas number drifts from SVG layout enough to clip. `textLength` is then
  pinned on the result so a font substitution on someone else's machine can't
  push it back over.

- **The knuckle duster is a mask, not a path.** Each finger is a filled disc with
  a smaller disc knocked out; a lens-shaped grip bar unions them together. The
  hole spacing is deliberate: adjacent *holes* must not touch (or two holes merge
  into one slot) while the *rims* around them must overlap (that overlap is what
  scallops the top edge). If you resize the holes, check both.

- **Gradients are bounding-box relative.** A horizontal `<line>` has a zero-height
  bounding box, which collapses a vertical gradient to nothing — the divider
  dashes were invisible until they became `<rect>`s. Anything flat that needs the
  metal fill has to have real height.

- **Fonts are system fonts on purpose.** The badge uses Arial Black / Impact, not
  the site's Google Fonts. An SVG rendered inside an `<img>` is an isolated
  document — it cannot reach the page's webfonts or the network — so a webfont
  would preview fine and then silently fall back in the exported PNG.

- **The PNG export must not taint the canvas.** The SVG goes in as a `data:` URL,
  which is same-origin. Pull in a remote image and `canvas.toBlob()` starts
  throwing a security error instead of downloading.

The member dropdown reads `members.txt` — the same file `scripts/build-roster.py`
generates for Ham2K PoLo — so new members show up in the forge automatically on
the next roster build. If that fetch fails the dropdown disables itself and the
text fields still work.

---

## Adding AI generation later

If the gang does want "describe a badge and get a weird one back", the shape is:

1. Deploy a Cloudflare Worker (free tier is plenty) holding the image API key as
   a **secret**, never in this repo.
2. Move the password check into the Worker. Give it its own shared secret and
   have it verify server-side, so the browser never holds anything that grants
   access. The client-side gate in `logo.html` becomes UI politeness, not security.
3. Rate-limit per IP and set a hard monthly spend cap on the API account. Assume
   the password will leak eventually and make sure the blast radius is a bill you
   can live with.
4. Point the page at the Worker URL and keep the current client-side forge as the
   default — it's free, instant, and produces a consistent mark, which is what
   you want most of the time anyway.

Don't do step 4 without steps 1–3.
