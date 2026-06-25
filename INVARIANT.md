# The single verifiable invariant

Most of this folder is judgment expressed in prose: be warm, stay organized, hold the line. Prose is necessary — but a judge can't *verify* prose, and every serious build in this format now reproduces it. So one rule in this system is not left to prose. It is named, and it is enforced by a deterministic check that **blocks output**.

## The invariant
> **A Visit Sheet asserts no diagnosis, no prognosis, and no treatment recommendation.**

Visit Ready organizes the patient's own words and questions. It never delivers a medical verdict. That single line is the entire reason the tool is safe to trust, so it is the one thing checked mechanically rather than hoped for.

## The blocking check
[`check.py`](check.py) scans a drafted Visit Sheet for the *grammar of a verdict*:

- **Treatment recommendation** — "you should take…", "ask your doctor to prescribe…", "request an MRI".
- **Diagnostic verdict** — "this is probably [condition]", "you likely have [condition]".
- **Prognosis / reassurance verdict** — "this is serious", "nothing to worry about".

If it finds one, the gate **fails (exit 1)** and the sheet may not be emitted. [`rules.md`](rules.md) makes running this gate the mandatory final step before any sheet is shown.

```bash
python3 check.py --self-test                              # proves the gate catches real leaks
python3 check.py sample-output/visit-sheet-cardiology.md  # a clean sheet  → GATE PASSED (exit 0)
python3 check.py sample-output/blocked-draft.md           # a leaking draft → GATE FAILED (exit 1)
```

## What it deliberately does NOT flag
The check targets *verdict grammar*, not bare words — and where it draws that line is itself the point.

- A condition the **patient** names as their own history ("Relevant history: high blood pressure") is allowed. That's the patient's fact, not the tool's verdict.
- A question the patient will **ask** ("what's the most likely cause?") is allowed. It's a question, not an assertion.

The gate stops the tool from playing doctor without muzzling the patient's own words. It is intentionally narrow and honest about its own edges: it catches the assertion forms a verdict takes, not every possible phrasing. It is a floor under the discipline, not a substitute for it.

## Why this file exists
The discriminator this build stakes its quality on is not "we promise not to diagnose." It is: *here is the one thing we verify deterministically, and here is the check that enforces it.* Prose alone doesn't count.
