# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/logging.py
- `T008` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T010` (rejected 1x): No evidence of a `data/raw/` directory or any checksum‑verification code (e.g., scripts, functions, or configuration files) is provided. The required artifact is missing, so the task is not satisfied.
- `T011` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/splits.py
- `T028` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/splits.py, src/models/ensemble.py
- `T015b` (rejected 1x): The provided `src/data/ingest.py` does not contain any logic that checks a count and writes `data/processed/data_scarcity_flag.json`, and the expected JSON file is absent from the repository. Both the required code change and the output artifact are missing.
- `T016` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/graph_construction.py
- `T017` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/sweep_cutoff.py, data/results/cutoff_sensitivity.json
- `T018` (rejected 1x): No code, script, configuration, or documentation was provided that implements outlier handling (i.e., detecting samples with coordination numbers > 6 and flagging them for exclusion from training while keeping them in the test set). The required artifact is missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

