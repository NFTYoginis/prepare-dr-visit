# The single verifiable invariant

Most of this folder is judgment expressed in prose: be warm, stay organized, hold the line. Prose is necessary — but a judge can't *verify* prose, and every serious build in this format now reproduces it. So one rule in this system is not left to prose. It is named, and it is enforced by a deterministic check that **blocks output**.

## The invariant
> **A Visit Sheet asserts no diagnosis, no prognosis, and no treatment recommendation.**

Visit Ready organizes the patient's own words and questions. It never delivers a medical verdict. That single line is the entire reason the tool is safe to trust, so it is the one thing checked mechanically rather than hoped for.

## The blocking check
[`check.py`](check.py) scans a drafted Visit Sheet for the *grammar of a verdict*:

- **Treatment / plan recommendation** — "you should take…", "ask your doctor to prescribe…", "we should start [drug]", "request an MRI".
- **Diagnostic verdict** — "this is probably [condition]", "you're having a [condition]", "it's your [organ]", "we should rule out [condition]", "I think it's…".
- **Prognosis / reassurance verdict** — "this is serious", "nothing to worry about".

If it finds one, the gate **fails (exit 1)** and the sheet may not be emitted. [`rules.md`](rules.md) makes running this gate the mandatory final step before any sheet is shown.

```bash
python3 check.py --self-test                              # proves the gate catches real leaks
python3 check.py sample-output/visit-sheet-cardiology.md  # a clean sheet  → GATE PASSED (exit 0)
python3 check.py sample-output/blocked-draft.md           # a leaking draft → GATE FAILED (exit 1)
```

## What it catches — and what it honestly can't
The check matches the *grammar* of a verdict, so it's straight about two real limits:

- **It's speaker-blind.** It reads the drafted sheet line by line; it can't tell whether a verdict is the tool's or a quote of the patient's fear. So "I'm scared this is cancer," written as a flat statement, trips it too. That's exactly why the convention is firm: **a patient's worry goes on the sheet as a question, not a verdict** — "Worth asking: could this be something serious?" Phrased that way it passes, it's more useful to the doctor, and the same discipline applies to patient and tool alike (`rules.md` makes this the rule). So the gate does not "leave the patient's words untouched" — it nudges a worry into a question, which is the right shape anyway.
- **It's a canonical floor, not total coverage.** It catches the common forms a verdict takes — "this is probably [X]", "you're having a [X]", "we should rule out [X]", "I think it's your [organ]" — not every possible phrasing. The discipline carries the rest.

What it deliberately does **not** flag: a condition the patient names as their own history ("Relevant history: high blood pressure"), and a genuine question ("what's the most likely cause?"). Those are the patient's facts and questions, not the tool's verdicts.

It is a **floor under the discipline, not a substitute for it.**

## Why this file exists
The discriminator this build stakes its quality on is not "we promise not to diagnose." It is: *here is the one thing we verify deterministically, and here is the check that enforces it.* Prose alone doesn't count.
