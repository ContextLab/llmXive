# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T014` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data_acquisition.py
- `T015` (rejected 1x): The provided `src/preprocessing.py` contains only data loading and stratified splitting logic; it does not implement Ensembl/Entrez‑to‑HGNC harmonization, coverage calculation, conditional logging, or writing `data/feasibility_gate.json`. Moreover, the required `data/feasibility_gate.json` file is absent. These missing pieces mean the task’s core requirements are not satisfied.
- `T023b` (rejected 1x): declared artifact(s) missing/empty/invalid: src/differential_expression.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

