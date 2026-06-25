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

# Condition shapes — common diagnostic-noun suffixes plus a keyword list.
# Used ONLY inside verdict grammar below, so a bare condition word in the
# patient's own history never trips the gate on its own.
_CONDITION = (
    r"(?:\w+itis|\w+osis|\w+emia|\w+opathy|cancer|tumou?r|infection|angina|"
    r"migraine|fracture|clot|embolism|stroke|heart attack|disease|syndrome|"
    r"disorder|deficiency|infarction|aneurysm|ulcer|pneumonia)"
)

# Each rule fires on the GRAMMAR of a verdict (the tool asserting a conclusion
# about the patient), not on questions the patient asks or facts they report.
RULES = [
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
    ("diagnostic verdict",
     re.compile(r"\b(?:this|it|that|the\s+cause)\s+"
                r"(?:is|'s|appears to be|looks like|sounds like|is probably|"
                r"is likely|is most likely|could be|might be|may be)\b"
                r"[^.?!\n]{0,40}\b" + _CONDITION + r"\b", re.I)),
    ("diagnostic verdict",
     re.compile(r"\byou\s+(?:probably\s+|likely\s+|most likely\s+|may\s+|"
                r"might\s+|could\s+)?have\b[^.?!\n]{0,40}\b" + _CONDITION + r"\b", re.I)),
    ("prognosis / reassurance verdict",
     re.compile(r"\b(?:this is|it'?s|that'?s)\s+"
                r"(?:serious|dangerous|life-threatening|benign|harmless|"
                r"nothing to worry about|not serious|probably fine)\b", re.I)),
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
]

SAMPLES_PASS = [
    "Reason I'm here: chest tightness on exertion for ~3 weeks.",
    "My top question: what's the most likely cause, and what test will tell us?",
    "Medications: lisinopril (daily); ibuprofen (knee, as needed).",
    "Worse when I climb stairs, better when I rest.",
    "What symptoms should send me to the ER instead of waiting?",
    "I have had this tightness for about three weeks.",
    "Relevant history: high blood pressure (on lisinopril); age 54.",
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
