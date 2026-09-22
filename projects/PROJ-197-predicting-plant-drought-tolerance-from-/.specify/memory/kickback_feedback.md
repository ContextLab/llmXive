# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directory tree (code/, data/raw/, data/processed/, tests/, docs/, docs/reports/) is presented; the implementer did not provide any file‑system listing, screenshots, or other proof that these folders exist and are non‑empty. The task therefore remains unverified.
- `T016` (rejected 1x): The repository contains `code/data/generate.py` with a correct matrix‑generation function, but the script never writes the resulting array to `data/processed/synthetic_phylo_matrix.npy`, and that file is absent from the project. The required output file is missing, so the task is not fully satisfied.
- `T012` (rejected 1x): The repository contains a partially‑implemented `code/data/generate.py` (the shown portion stops after creating the DataFrame and does not show label computation or CSV writing). Moreover, the required output file `data/processed/synthetic_genomics.csv` is absent. The task’s core deliverables—generating labels per the specified rule and persisting them to the exact CSV path—are therefore not fulfilled.
- `T019` (rejected 1x): declared artifact(s) missing/empty/invalid: tests/unit/test_stats.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

