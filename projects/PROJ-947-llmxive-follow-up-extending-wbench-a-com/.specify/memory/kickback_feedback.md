# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence was provided showing that the `code/`, `tests/`, `data/`, and `results/` directories actually exist in the repository root; without visible directory listings or files, the requirement cannot be confirmed as satisfied. The implementer must add these directories (even if empty) to the project structure.
- `T001c` (rejected 1x): No directory listings or file system evidence were provided showing that `tests/unit/`, `tests/integration/`, and `tests/contract/` exist in the repository. Without concrete proof of these folders being created, the task requirement is not satisfied. The implementer must add the three test directories (and optionally placeholder test files) and present evidence (e.g., a directory tree or file list).
- `T013` (rejected 1x): The repository contains a partially‑written `code/entropy/generator.py` that stops mid‑function and never implements the token‑reweighting, convergence loop, or file‑writing steps required. Moreover, the expected output files `data/processed/variants.csv` and `data/processed/generation_logs.json` are absent. Consequently the task’s core requirements are not satisfied.
- `T014` (rejected 1x): The repository contains `code/entropy/validator.py`, but the file is truncated and we cannot verify that it reads `data/processed/variants.csv`, writes `data/processed/validity_flags.csv` with the required columns, or implements the unit‑test behavior. Moreover, both `data/processed/variants.csv` and the expected output `data/processed/validity_flags.csv` are absent, and no unit‑test file is present. These missing artifacts prevent confirming that the task’s functional requirements are met.
- `T015` (rejected 1x): The required output file `data/processed/complexity_scores.csv` does not exist, and the provided `code/entropy/scorer.py` is incomplete (truncated) with no evidence that it actually computes scores and writes the CSV. The task’s core deliverable is therefore missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

