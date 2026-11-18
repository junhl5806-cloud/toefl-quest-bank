#!/usr/bin/env python3
"""Validate a TOEFL Quest bank set (bank/YYYY-MM-DD.json).

Usage: python3 tools/validate.py bank/2026-11-18.json [--print-blind OUT.json]

Exit code 0 = valid. Errors are printed one per line.
--print-blind writes a copy with every answer key removed (for the blind-solve check).
"""
import json, re, sys

LEVELS = ["3.5", "4.5", "5.5"]
TEMPLATE = [  # key, step, allowed kinds
    ("R0", "R", {"ctw"}), ("R1", "R", {"daily"}), ("R2", "R", {"academic"}),
    ("L0", "L", {"choose"}), ("L1", "L", {"conversation"}), ("L2", "L", {"talk", "announcement"}),
    ("W0", "W", {"build"}), ("W1", "W", {"email", "discussion"}),
    ("S0", "S", {"repeat"}), ("S1", "S", {"interview"}),
]
MCQ_COUNT = {"daily": 3, "academic": 5, "conversation": 3, "announcement": 3, "talk": 4}
VOCAB_RE = re.compile(r"(?:word|phrase)\s+[\"“'‘]([^\"”'’]+)[\"”'’]\s+in\s+(?:the\s+)?(?:passage|paragraph|text)", re.I)

errors = []
def err(where, msg): errors.append(f"{where}: {msg}")

def check_mcq(where, qs, n, text=None):
    if not isinstance(qs, list) or len(qs) != n:
        err(where, f"needs exactly {n} questions"); return
    for i, q in enumerate(qs):
        w = f"{where}.q{i}"
        if not isinstance(q, dict) or not str(q.get("q", "")).strip(): err(w, "missing q"); continue
        o = q.get("options")
        if not isinstance(o, list) or len(o) != 4 or any(not str(x).strip() for x in o): err(w, "needs 4 non-empty options"); continue
        if len({str(x).strip().lower() for x in o}) != 4: err(w, "duplicate options")
        a = q.get("answer")
        if not isinstance(a, int) or not 0 <= a <= 3: err(w, "answer must be 0-3")
        m = VOCAB_RE.search(q["q"])
        if m and text is not None and not re.search(r"\b" + re.escape(m.group(1)) + r"\b", text, re.I):
            err(w, f'vocab word "{m.group(1)}" not found in passage')

def validate(s):
    for k in ("id", "date", "levels", "tasks"):
        if k not in s: err("set", f"missing {k}")
    if s.get("levels") != LEVELS: err("set", f"levels must be {LEVELS}")
    tasks = s.get("tasks") or []
    if [t.get("key") for t in tasks] != [k for k, _, _ in TEMPLATE]:
        err("set", "tasks must be in order " + ",".join(k for k, _, _ in TEMPLATE)); return
    for t, (key, step, kinds) in zip(tasks, TEMPLATE):
        kind = t.get("kind"); sh = t.get("shared") or {}; bl = t.get("byLevel") or {}
        if t.get("step") != step: err(key, f"step must be {step}")
        if kind not in kinds: err(key, f"kind must be one of {sorted(kinds)}"); continue
        for lv in LEVELS:
            if lv not in bl: err(key, f"byLevel missing {lv}")
        for lv in LEVELS:
            d = {**sh, **(bl.get(lv) or {})}; w = f"{key}[{lv}]"
            if kind == "ctw":
                p = d.get("paragraph", "")
                blanks = re.findall(r"\{([^|}]+)\|([^}]+)\}", p)
                if len(blanks) != 10: err(w, f"ctw needs 10 blanks, has {len(blanks)}")
                for a, b in blanks:
                    if not re.fullmatch(r"[A-Za-z]+", a + b): err(w, f"blank {{{a}|{b}}} must be letters only")
                if re.search(r"\{[^}]*\{", p): err(w, "nested braces")
            elif kind in MCQ_COUNT:
                text = d.get("text") if kind != "conversation" else " ".join(l.get("text", "") for l in d.get("lines", []))
                if not str(text or "").strip(): err(w, "missing text/lines")
                if kind == "conversation" and len(d.get("lines", [])) < 6: err(w, "conversation needs 6+ lines")
                check_mcq(w, d.get("questions"), MCQ_COUNT[kind], text)
            elif kind == "choose":
                its = d.get("items")
                if not isinstance(its, list) or len(its) != 5: err(w, "choose needs 5 items"); continue
                check_mcq(w, [{"q": i.get("prompt"), "options": i.get("options"), "answer": i.get("answer")} for i in its], 5)
            elif kind == "build":
                its = d.get("items")
                if not isinstance(its, list) or len(its) != 4: err(w, "build needs 4 items"); continue
                for i, it in enumerate(its):
                    a = str(it.get("answer", ""))
                    if not it.get("context") or not a: err(f"{w}.i{i}", "missing context/answer")
                    if re.search(r"[.,!?;:]", a): err(f"{w}.i{i}", "answer must have no punctuation")
                    if not 6 <= len(a.split()) <= 13: err(f"{w}.i{i}", "answer should be 7-12 words")
                    dis = str(it.get("distractor", "")).strip()
                    if not dis or dis.lower() in [x.lower() for x in a.split()]: err(f"{w}.i{i}", "distractor missing or inside answer")
            elif kind == "email":
                if not d.get("scenario") or not d.get("recipient") or len(d.get("points") or []) != 3: err(w, "email needs scenario, recipient, 3 points")
            elif kind == "discussion":
                if not d.get("question") or not d.get("professor") or len(d.get("posts") or []) != 2: err(w, "discussion needs professor, question, 2 posts")
            elif kind == "repeat":
                if len(d.get("sentences") or []) < 5: err(w, "repeat needs 5+ sentences")
            elif kind == "interview":
                if len(d.get("questions") or []) != 3: err(w, "interview needs 3 questions")

def blind_copy(s):
    """Same set with every answer hidden: MCQ keys removed, ctw blanks shown as underscores,
    build sentences given as shuffled word lists (incl. the distractor)."""
    import random
    rnd = random.Random(7)
    b = json.loads(json.dumps(s))
    for t in b["tasks"]:
        for lv in b["levels"]:
            d = t["byLevel"].get(lv) or {}
            for q in d.get("questions") or []:
                if isinstance(q, dict): q.pop("answer", None)
            if t["kind"] == "ctw" and "paragraph" in d:
                d["paragraph"] = re.sub(r"\{([^|}]+)\|([^}]+)\}", lambda m: m.group(1) + "_" * len(m.group(2)), d["paragraph"])
            if t["kind"] == "build":
                new = []
                for it in d.get("items") or []:
                    words = str(it.get("answer", "")).split() + [it.get("distractor", "")]
                    rnd.shuffle(words)
                    new.append({"context": it.get("context"), "words": words})
                d["items"] = new
            elif t["kind"] == "choose":
                for it in d.get("items") or []: it.pop("answer", None)
    return b

if __name__ == "__main__":
    path = sys.argv[1]
    s = json.load(open(path, encoding="utf-8"))
    validate(s)
    if "--print-blind" in sys.argv:
        out = sys.argv[sys.argv.index("--print-blind") + 1]
        json.dump(blind_copy(s), open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if errors:
        print("\n".join(errors)); sys.exit(1)
    print(f"OK {s.get('id')}: {len(s['tasks'])} tasks x {len(LEVELS)} levels, {len(json.dumps(s))//1024} KB")
