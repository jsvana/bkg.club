# Downline Tree + Recruit Form — Setup

This adds two pages to bkg.club:

- **`tree.html`** — an interactive "downline" family tree showing who recruited
  who into the gang (MLM-pyramid style), with a top-recruiters leaderboard.
- **`recruit.html`** — a form where a sponsoring member submits a new recruit's
  info. Submissions land in a Google Sheet for officers to review.

Both reuse the existing build pipeline: `scripts/build-roster.py` reads the
roster Google Sheet and regenerates the site on every push + every 6 hours.

---

## 1. The tree data: add a `Sponsor` column to the roster sheet

The tree is built from **one new column** in the existing roster Google Sheet
(the same sheet that already has `Callsign, Name, Join Date, #, QTH`).

1. Open the roster sheet.
2. Add a column named exactly **`Sponsor`** (`Sponsored By` also works).
3. For each member, put **who recruited them** — either that sponsor's
   **callsign** (e.g. `KI7QCF`) or their **BKG number** (e.g. `1`, `BKG1`,
   or `BKG #1`). Both are accepted.
4. Leave it blank for anyone with no known sponsor — they become a **root** of
   the tree (the founder, #1, is naturally a root).

**Backfilling existing members:** this column *is* the backfill mechanism. Fill
in the `Sponsor` for current members as you learn who brought them in. On the
next build the tree updates automatically — nothing else to edit.

> The build resolves a sponsor to a callsign by matching the cell against
> known members (callsign first, then BKG number). Unrecognized sponsors are
> logged and treated as a root. Self-sponsors are ignored.

That's all the tree needs. `scripts/build-roster.py` injects the data into
`tree.html` between the `DOWNLINE_DATA` markers each build.

---

## 2. The recruit form: connect a Google Form

The site is static (GitHub Pages), so the form POSTs to a **Google Form** whose
responses collect in a Sheet you review (admin-review flow — submissions do
**not** auto-publish to the tree).

### a. Create the Google Form

Create a Form with one question (Short answer / Paragraph) per field, in this
order. Question titles can be anything; the mapping is by entry ID, not title:

| Form question                | maps to JS key |
|------------------------------|----------------|
| Sponsor Callsign             | `sponsorCall`  |
| Sponsor BKG #                | `sponsorNum`   |
| New Op Callsign              | `recruitCall`  |
| New Op Name                  | `recruitName`  |
| New Op QTH (State)           | `recruitQth`   |
| QSO Date (UTC)               | `qsoDate`      |
| QSO Time (UTC)               | `qsoTime`      |
| Band / Mode                  | `qsoBand`      |
| Notes                        | `notes`        |
| Submitter Email              | `email`        |

### b. Find the action URL + entry IDs

1. Open the live Form, right-click → **View Page Source** (or use the
   "Get pre-filled link" feature, which is easier).
2. The **action URL** ends in `/formResponse` — e.g.
   `https://docs.google.com/forms/d/e/1FAIpQLSxxxx/formResponse`.
3. Each field has an `entry.<NUMBER>` name. The pre-filled-link trick: fill the
   form, "Get pre-filled link", and read the `entry.NNNN=value` pairs from the
   generated URL.

### c. Wire it into `recruit.html`

Near the bottom of `recruit.html`, edit the `GOOGLE_FORM` object:

```js
const GOOGLE_FORM = {
    action: "https://docs.google.com/forms/d/e/1FAIpQLSxxxx/formResponse",
    fields: {
        sponsorCall: "entry.1111111111",
        sponsorNum:  "entry.2222222222",
        recruitCall: "entry.3333333333",
        // ...the rest
    }
};
```

Once `action` is set, the on-page "SETUP PENDING" warning disappears and the
form goes live. Leaving `action` empty keeps the form disabled.

### d. Approving a submission

1. Review the Form-response Sheet.
2. To accept: add the new op to the **roster sheet** as usual (assign the next
   BKG #) and set their **`Sponsor`** to the submitting member's callsign/number.
3. Next build → they appear in the roster, map, and the downline tree.

---

## Files

| File                          | What it is |
|-------------------------------|------------|
| `tree.html`                   | Downline tree page (data injected at build) |
| `recruit.html`                | Recruit submission form (POSTs to Google Form) |
| `assets/bkg.css`              | Shared theme for the two new pages |
| `scripts/build-roster.py`     | Now also resolves sponsors + builds the tree |

No new secrets or services beyond the Google Form. The form needs no API keys —
it POSTs straight to Google.
