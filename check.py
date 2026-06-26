#!/usr/bin/env python3
"""
Visit Ready — the blocking gate.

THE SINGLE VERIFIABLE INVARIANT:
    A Visit Sheet asserts no diagnosis, no prognosis, and no treatment
    recommendation. It organizes the patient's own words and questions;
    it never delivers a medical verdict.

This is enforced here, deterministically, as a BLOCKING check — not
narrated in prose. If the gate fails, the sheet may not be emitted.

    python3 check.py path/to/visit-sheet.md   # gate a sheet (exit 0 pass / 1 fail)
    cat sheet.md | python3 check.py -          # gate from stdin
    python3 check.py --self-test               # prove the gate works

Stdlib only. No dependencies.
"""

import argparse
import re
import sys

# Condition / organ / descriptor shapes — matched ONLY inside verdict grammar
# below, so a bare condition word in the patient's own history never trips the
# gate on its own. This is a deliberately CANONICAL set: it catches the common
# forms a verdict takes, not every phrasing. The discipline carries the rest;
# see INVARIANT.md ("a floor under the discipline, not a substitute").
_CONDITION = (
    r"(?:\w+itis|\w+osis|\w+emia|\w+opathy|cancer|tumou?r|infection|angina|"
    r"migraine|fracture|clot|embolism|stroke|heart attack|heart failure|disease|"
    r"syndrome|disorder|deficiency|infarction|aneurysm|ulcer|pneumonia|lupus|"
    r"diabetes|asthma|copd|gout|sepsis|gallstones?|kidney stones?|blockage|"
    r"shingles|vertigo|covid|the flu|flu)"
)
# Organs/descriptors/states only ever match as the OBJECT of a verdict ("it's your
# <organ>", "this looks <descriptor>", "your thyroid is <state>") — never alone.
_ORGAN = (r"(?:heart|gallbladder|liver|kidneys?|lungs?|thyroid|appendix|"
          r"pancreas|spleen|bowel|colon|prostate|sinuses?)")
_DESCRIPTOR = (r"(?:cardiac|neurological|respiratory|gastrointestinal|vascular|"
               r"hormonal|musculoskeletal|psychiatric)")
_STATE = (r"(?:failing|underactive|overactive|enlarged|inflamed|blocked|damaged|"
          r"infected|the problem|the cause|the culprit|the issue)")

# Each rule fires on the GRAMMAR of a verdict (the tool asserting a conclusion
# about the patient), not on questions the patient asks or facts they report.
RULES = [
    # --- treatment / plan recommendations ---
    ("treatment recommendation",
     re.compile(r"\byou\s+(?:should|need to|ought to|must|have to)\s+"
                r"(?:take|start|stop|switch|try|request|ask for|get|begin)\b", re.I)),
    ("treatment recommendation",
     re.compile(r"\b(?:ask|request|tell)\b[^.?!\n]{0,40}\b"
                r"(?:to\s+(?:prescribe|order|run)|for\s+(?:a|an|some)\s+"
                r"(?:prescription|medication|antibiotic|steroid|statin|scan|"
                r"mri|ct|biopsy|x-?ray))\b", re.I)),
    ("treatment recommendation",
     re.compile(r"\bI\s+(?:recommend|suggest|advise)\b[^.?!\n]{0,40}"
                r"\b(?:take|try|start|stop|request|ask|get)\b", re.I)),
    # clinician-style plan: "we should rule out / start ...", "we'll order ...", "let's start ..."
    ("treatment / plan recommendation",
     re.compile(r"\b(?:we|let'?s|let us)(?:'ll|\s+(?:should|need to|ought to|will|can))?\s+"
                r"(?:rule out|start|stop|switch|order|run|test for|prescribe|"
                r"put (?:you|them) on|begin|trial)\b", re.I)),
    ("diagnostic verdict",  # differential-diagnosis phrasing
     re.compile(r"\brule\s+out\b", re.I)),
    # --- diagnostic verdicts ---
    # copular assertion — broadened subject ("the lump is cancer", "your thyroid is underactive")
    ("diagnostic verdict",
     re.compile(r"\b(?:this|it|that|the\s+cause|(?:the|that|your)\s+\w+)"
                r"(?:\s+(?:is|are|could be|might be|may be|looks like|sounds like|"
                r"looks|sounds|seems(?:\sto\sbe)?|appears(?:\sto\sbe)?)|'s)"
                r"(?:\s+(?:probably|likely|most likely|definitely))?"
                r"[^.?!\n]{0,40}\b(?:" + _CONDITION + r"|your\s+" + _ORGAN
                + r"|" + _DESCRIPTOR + r"|" + _STATE + r")\b", re.I)),
    # "you have / you've got <condition>" (contraction-safe)
    ("diagnostic verdict",
     re.compile(r"\byou(?:\s+(?:probably|likely|most likely|may|might|could))?"
                r"(?:'ve\s+got|\s+have(?:\s+got)?)\b[^.?!\n]{0,40}\b" + _CONDITION + r"\b", re.I)),
    ("diagnostic verdict",
     re.compile(r"\byou(?:'re| are)\s+(?:probably\s+|likely\s+)?having\b"
                r"[^.?!\n]{0,30}\b" + _CONDITION + r"\b", re.I)),
    # "you're / you may be developing <condition>"
    ("diagnostic verdict",
     re.compile(r"\byou(?:'re| are|\s+may be|\s+might be|\s+could be)\s+(?:probably\s+)?"
                r"(?:developing|getting|coming down with)\b[^.?!\n]{0,20}\b" + _CONDITION + r"\b", re.I)),
    # stated clinical opinion: "I think it's ...", "my guess is ..."
    ("diagnostic verdict",
     re.compile(r"\bI\s+(?:think|believe|suspect|bet|reckon|figure)\b"
                r"[^.?!\n]{0,25}\b(?:it'?s|this is|that'?s|you have|you'?ve got)\b", re.I)),
    ("diagnostic verdict",
     re.compile(r"\bmy\s+(?:guess|bet|hunch|money)\s+(?:is|would be|'?s on)\b", re.I)),
    # inferential: "points to / suggests / consistent with / caused by ... <condition>"
    ("diagnostic verdict",
     re.compile(r"\b(?:points?\s+to|suggests?|indicates?|consistent with|caused by|"
                r"due to|screams?|(?:likely\s+)?culprit is)\b[^.?!\n]{0,30}\b(?:"
                + _CONDITION + r"|your\s+" + _ORGAN + r"|" + _ORGAN + r"|" + _DESCRIPTOR + r")\b", re.I)),
    # bare hedged opinion: "sounds like / looks like <condition>"
    ("diagnostic verdict",
     re.compile(r"\b(?:sounds|looks)\s+like\b[^.?!\n]{0,20}\b(?:"
                + _CONDITION + r"|" + _DESCRIPTOR + r")\b", re.I)),
    # --- prognosis verdicts (present + future) ---
    ("prognosis / reassurance verdict",
     re.compile(r"\b(?:this is|it'?s|that'?s)\s+"
                r"(?:serious|dangerous|life-threatening|benign|harmless|"
                r"nothing to worry about|nothing serious|just stress|not serious|"
                r"probably fine|nothing)\b", re.I)),
    ("prognosis verdict",  # future-tense outcome
     re.compile(r"\byou(?:'ll|'d| will|'re going to| are going to)"
                r"[^.?!\n]{0,30}\b(?:need|require|have to|develop|lose|worsen|"
                r"recover|die|end up|be left)\b", re.I)),
    ("prognosis verdict",
     re.compile(r"\byou\s+(?:won'?t|will not)\s+"
                r"(?:recover|make it|get better|improve|be the same)\b", re.I)),
    ("prognosis verdict",
     re.compile(r"\b(?:this|it|that|(?:the|that|your)\s+\w+)\s+"
                r"(?:will|'ll|is going to|may|might|could)\s+"
                r"(?:get worse|worsen|spread|progress|deteriorate|improve|"
                r"kill|need|require)\b", re.I)),
]


def scan(text):
    """Return a list of (line_no, label, snippet) violations."""
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        for label, rx in RULES:
            m = rx.search(line)
            if m:
                out.append((i, label, m.group(0).strip()))
    return out


def gate(text):
    """(passed, violations). passed=True => safe to emit."""
    v = scan(text)
    return (len(v) == 0, v)


def _report(violations):
    for line_no, label, snippet in violations:
        print(f'  line {line_no}: [{label}] -> "{snippet}"')


# --- self-test: prove the gate blocks real leaks and clears clean sheets ---

SAMPLES_FAIL = [
    "Reason I'm here: this is probably angina brought on by exertion.",
    "You likely have an infection; ask your doctor to prescribe an antibiotic.",
    "Worth mentioning: it could be a clot, and this is serious.",
    "You should start a statin and request an MRI.",
    "Don't worry — this is nothing to worry about.",
    "I suggest you ask for a biopsy.",
    # widened coverage (F2) — natural verdict forms that used to leak:
    "Reason: you're having a heart attack.",
    "It's probably your heart.",
    "This looks cardiac.",
    "Plan: we should rule out lupus and start prednisone.",
    "I think it's your gallbladder.",
    # 2nd independent re-gate — verdict families + dead-branch fixes:
    "Reason: your thyroid is underactive.",
    "Reason: your heart is the problem.",
    "Reason: that rash is shingles.",
    "Reason: the lump is cancer.",
    "Reason: your labs suggest diabetes.",
    "Reason: symptoms point to pneumonia.",
    "Reason: your symptoms scream appendicitis.",
    "Impression: sounds like vertigo.",
    "My guess is shingles.",
    "Reason: you may be developing COPD.",
    "Worth mentioning: you've got pneumonia.",
    "Plan: we'll order an MRI and start prednisone.",
    "Prognosis: you'll need surgery.",
    "Prognosis: this will get worse over the next few months.",
    "Prognosis: you won't recover fully.",
    "It's nothing — just stress.",
]

SAMPLES_PASS = [
    "Reason I'm here: chest tightness on exertion for ~3 weeks.",
    "My top question: what's the most likely cause, and what test will tell us?",
    "Medications: lisinopril (daily); ibuprofen (knee, as needed).",
    "Worse when I climb stairs, better when I rest.",
    "What symptoms should send me to the ER instead of waiting?",
    "I have had this tightness for about three weeks.",
    "Relevant history: high blood pressure (on lisinopril); age 54.",
    # a patient's worry belongs on the sheet — phrased as a question, it passes (F1):
    "Worth asking: could this be something serious, like cancer?",
    "Worth asking: could this be my heart, or something else?",
    # legitimate patient content / questions must still pass (FP guards):
    "I want to ask whether I should start any new medication.",
    "Worth asking: will this get worse, or settle on its own?",
    "Relevant history: I had pneumonia last year.",
    "My heart rate has been a bit higher than usual lately.",
]


def self_test():
    ok = True
    print("FAIL samples — the gate must BLOCK each:")
    for s in SAMPLES_FAIL:
        passed, _ = gate(s)
        print(f"  [{'BLOCKED ok' if not passed else 'LEAKED  !!'}] {s}")
        ok = ok and (not passed)
    print("\nPASS samples — the gate must ALLOW each:")
    for s in SAMPLES_PASS:
        passed, v = gate(s)
        print(f"  [{'allowed ok' if passed else 'FALSE-POSITIVE !!'}] {s}")
        if not passed:
            ok = False
            _report(v)
    print()
    if ok:
        print("SELF-TEST PASSED — gate blocks every leak, clears every clean line.")
        return 0
    print("SELF-TEST FAILED — gate is miscalibrated (see above).")
    return 1


def main():
    ap = argparse.ArgumentParser(
        description="Visit Ready blocking gate: no diagnosis, prognosis, or treatment recommendation.")
    ap.add_argument("path", nargs="?", help="Visit Sheet file to gate ('-' for stdin)")
    ap.add_argument("--self-test", action="store_true", help="prove the gate works")
    args = ap.parse_args()

    if args.self_test:
        sys.exit(self_test())
    if not args.path:
        ap.error("give a file to gate, or --self-test")

    if args.path == "-":
        text = sys.stdin.read()
    else:
        with open(args.path, encoding="utf-8") as f:
            text = f.read()

    passed, violations = gate(text)
    if passed:
        print("GATE PASSED — no diagnosis, prognosis, or treatment recommendation found. Safe to emit.")
        sys.exit(0)
    print("GATE FAILED — this Visit Sheet asserts a medical verdict and MUST NOT be emitted:")
    _report(violations)
    print("\nFix: remove the verdict. Turn it into a question the patient asks the doctor.")
    sys.exit(1)


if __name__ == "__main__":
    main()
