# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory tree or file listings were provided showing the required folders (`src/data/`, `src/analysis/`, `src/utils/`, `src/cli/`, `tests/unit/`, `tests/integration/`, `data/raw/`, `data/processed/`, `data/results/`, `results/`, `state/`). Without concrete evidence that these paths exist, the task is not satisfied. The implementer must create and show the full project structure.
- `T010a` (rejected 1x): No file such as `data-model.md` containing the required GUE‑derived extreme‑value CDF definition, Tracy‑Widom approximation, and normalization derivation was provided. Without the actual written formula the task’s deliverable is absent.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

