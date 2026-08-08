# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001c` (rejected 1x): No evidence of the required `.gitkeep` files in `data/raw/`, `data/processed/`, `data/results/`, `artifacts/synthesized_adapters/`, or `specs/001-lattentskill-retrieval-geometry/contracts/` was provided; the artifact list is empty, so the task’s requirement is not satisfied.
- `T003b` (rejected 1x): declared artifact(s) missing/empty/invalid: ruff.toml
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T014` (rejected 1x): The repository contains `src/retrieval/vector_db.py`, but the required output file `data/processed/skill_index.npz` is absent, and the provided module does not demonstrate that it actually constructs and writes the index (no top‑level execution or invoked logic shown). Without the generated `.npz` file, the task’s core requirement is unmet.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

