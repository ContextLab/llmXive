# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): The provided evidence contains only a feature specification and user stories; there is no indication that the required directories (`src/`, `tests/`, `data/`) have been created or contain any files. The implementer must add the project skeleton with those three top‑level folders (and optionally placeholder files) to satisfy task T001.
- `T003` (rejected 1x): declared artifact(s) missing/empty/invalid: pre-commit-config.yaml
- `T005` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/download_meg.py, data/raw/meg_streamed.parquet
- `T006` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/download_clutrr.py, data/raw/clutrr.parquet, tests/contract/test_clutrr_schema.py
- `T007` (rejected 1x): The required output file `data/processed/meg_filtered.npy` is absent, and the provided `src/data/preprocess_meg.py` contains code for Welch PSD computation (Part 2) rather than a band‑pass filter implementation for 30‑50 Hz. Consequently the deliverable and core functionality are missing.
- `T047` (rejected 1x): The required output file `data/processed/meg_psd_normalized.npy` does not exist, and the provided `src/data/preprocess_meg.py` is truncated and does not contain a complete implementation (e.g., missing zero‑padding, PSD computation, and normalization logic). Additionally, the referenced `contracts/dataset.schema.yaml` is missing, so verification cannot be performed.
- `T009` (rejected 1x): declared artifact(s) missing/empty/invalid: src/models/base_model.py
- `T012` (rejected 1x): declared artifact(s) missing/empty/invalid: src/analysis/spectral.py, tests/unit/test_spectral.py
- `T013` (rejected 1x): The `src/analysis/sdc.py` file is incomplete and contains a syntax error (unterminated string in the `compute_sdc_batch` function) and is truncated, so the required SDC calculation is not fully implemented. Additionally, the required `contracts/output.schema.yaml` (or `schema.yaml`) file is missing, so the output cannot be verified against the schema.
- `T013b` (rejected 1x): declared artifact(s) missing/empty/invalid: src/analysis/plv.py, tests/unit/test_plv.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

