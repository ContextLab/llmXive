# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory tree or file listings were provided, so there is no evidence that the required folders (`code/`, `data/raw/`, `data/processed/`, `results/`, `specs/`, `tests/`, `tests/unit/`, `tests/integration/`) and their `__init__.py` files actually exist. The implementer must supply a concrete file‑system snapshot (e.g., a `tree` output or a zip archive) showing these directories and the initialization files.
- `T004` (rejected 1x): No `utils/memory.py` file is present, and there is no implementation of `check_and_terminate_if_exceeds(limit_gb: float)` or any of the requested features (gradient checkpointing, batch‑size auto‑scaling, RAM watchdog). The required artifact is missing, so the task is not satisfied.
- `T005b` (rejected 1x): No `pipeline/loader.py` file or code snippet showing an exponential backoff wrapper with the specified initial delay of 30 seconds and a maximum of 5 retries is provided. Without the actual implementation artifact, we cannot confirm that the required functionality exists or meets the task specifications.
- `T005a` (rejected 1x): No `pipeline/loader.py` file or any code implementing dataset loaders for OpenWebText, GSM8K, ARC‑Challenge, or Wikitext‑2 is present. Consequently the required fail‑fast logic and absence of synthetic fallbacks cannot be verified. The artifact is missing, so the task is not satisfied.
- `T006` (rejected 1x): No `pipeline/model.py` file or any code implementing GPT‑2 124M checkpoint loading and CPU‑compatible weight manipulation was provided. The required artifact is missing, so the task is not satisfied.
- `T013` (rejected 1x): No `schemas/modification_proposal.py` file or Pydantic `ModificationProposal` model with the required fields was provided; the evidence lacks the requested code artifact entirely.
- `T034` (rejected 1x): declared artifact(s) missing/empty/invalid: results/logs/cycle_N.log, results/trajectory.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

