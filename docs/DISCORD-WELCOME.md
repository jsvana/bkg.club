# Discord Welcome Message (Carl-bot)

Carl-bot greets each new Discord member and auto-assigns them the
**lil' homies** role. They stay a lil' homie until an officer verifies two
things: (1) their nickname is set correctly, and (2) they've been jumped in
(the 2-meter CW initiation QSO). This doc holds the paste-ready welcome
message so the copy doesn't live only inside the Carl-bot dashboard.

## The message

Paste everything inside the fence verbatim — the `**bold**` markers are
Discord formatting, and `{user}` / `{server}` are Carl-bot variables that get
filled in automatically ( `{user}` @-mentions the new member, `{server}` is
the server name).

```text
★彡 NEW HOMIE ON THE NET!!! 彡★

🤜 WELCOME 2 {server}, {user}!!! 🤜

U just got rolled in2 the **lil' homies** role — every new homie starts here while the officers process ur intake!! (We're a law-abiding, FCC-respectin' gang, but rules is rules!! 🚨)

**HOW 2 GET PATCHED IN2 THE FULL GANG:**

1️⃣ **SET UR NAME STRAIGHT!!** Server nickname = `First Name | Callsign | #BKG` (like `Justin | N9HO | #32`) — first name ONLY, save the full govt name 4 the FCC!! State OG? Tack on ur state — `Justin | N9HO | #32 | AL OG`!! Not a state OG? NOTHIN goes after ur number!! 🚨

2️⃣ **GET JUMPED IN!!** Initiation = one **2-meter CW QSO** with a BKG member!! Already took ur licks & got ur BKG #? Tell an officer!! Not yet? Holler in the chat & we'll line up ur jump-in — bring ur key, leave ur fists at home!! 🤜📻

Once an officer verifies both, u get patched up from lil' homie 2 FULL BRASS POUNDER!! ✨

Til then: lurk, ask questions, & ALWAYS send a proper Roger!!

QRL? QRL? ...freq's all urs, homie!!
73 de BKG 🤜 ~*~2 METER CW OR BUST~*~
-... -.- --.
```

## Setting it up in Carl-bot

- Dashboard: <https://carl.gg> → ur server → **Welcome** → pick the welcome
  channel and paste the message above. (Or `!welcome message <text>` in chat.)
- Useful variables besides the two used here: `{user.name}` (name without the
  ping), `{membercount}`.
- The message is ~1.3k characters — comfortably under Discord's 2000-char
  limit, so there's room to tweak.
- The nickname format is exact: `First Name | Callsign | #BKG`
  (e.g. `Justin | N9HO | #32`) — first name only, no last name. State OGs —
  and only state OGs — append `| <state abbreviation> OG`
  (e.g. `Justin | N9HO | #32 | AL OG`). Anyone who isn't a state OG has
  **nothing** after the number.
- The role assignment itself is separate from the welcome message: Carl-bot
  dashboard → **Autoroles** → add *lil' homies* as the role granted on join.
