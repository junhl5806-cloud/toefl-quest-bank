# TOEFL Quest Bank

Daily TOEFL iBT (2026 format) practice sets shared by the TOEFL Daily Quest apps.
AI-generated original practice items. Not affiliated with or endorsed by ETS. TOEFL® is a registered trademark of ETS.

## Files
- `bank/YYYY-MM-DD.json` — one set per day (date in America/Denver)
- `bank/index.json` — `{latest, sets:[{id,date,verified}]}` newest last
- `tools/validate.py` — format checks; `--print-blind out.json` writes a copy with all answers hidden

## Set format
`{id, date, version, createdAt, levels:["3.5","4.5","5.5"], verified:{method,at,mismatches,fixed}, tasks:[...]}`

Each task: `{key, step, kind, shared, byLevel:{"3.5":{...},"4.5":{...},"5.5":{...}}}`.
An app builds the item for a learner as `{...shared, ...byLevel[level]}` — the same shape the app already uses.

| key | step | kind | shared | byLevel |
|---|---|---|---|---|
| R0 | R | ctw | topic | paragraph (10 blanks as `{shown\|missing}`) |
| R1 | R | daily | genre, text | 3 questions |
| R2 | R | academic | title, text | 5 questions |
| L0 | L | choose | – | 5 items {prompt, options[4], answer} |
| L1 | L | conversation | title, lines[{speaker,text}] | 3 questions |
| L2 | L | talk / announcement | title, text (+speaker) | 4 / 3 questions |
| W0 | W | build | – | 4 items {context, answer, distractor} |
| W1 | W | email / discussion | prompt fields | {} |
| S0 | S | repeat | context, sentences[6] | {} |
| S1 | S | interview | topic, questions[3] | {} |

Questions: `{q, options[4], answer}` (0-based). Options are already shuffled.
Reading `https://raw.githubusercontent.com/junhl5806-cloud/toefl-quest-bank/main/bank/<date>.json` needs no key.

## Problem reports
Open an issue with the label `report` and a body containing a JSON block:
`{"set":"2026-11-18","key":"R2","level":"4.5","ref":"2","reason":"wrong_key|ambiguous|typo|other","note":"..."}`
The daily job re-checks reported items, fixes or replaces them, and closes the issue.
