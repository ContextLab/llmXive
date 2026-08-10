# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T003a` (rejected 1x): No `.flake8` file or its contents were provided as evidence, so we cannot confirm that the required configuration file exists or contains valid settings. The implementer must supply the actual `.flake8` file with its configuration.
- `T004` (rejected 1x): No evidence of a `.git` directory or any proof that `git init` was executed in the project root was provided; the required artifact is missing.
- `T007a` (rejected 1x): The required schema file `contracts/dataset.schema.yaml` does not exist (only a missing `schema.yaml` is noted), so no dataset schema with the specified fields is provided. The task’s core artifact is absent.
- `T007b` (rejected 1x): The repository lacks the required `contracts/dataset.schema.yaml` file, so the validator cannot load the schema and will raise a `FileNotFoundError` instead of performing the intended checks. Additionally, the provided `validate_schema.py` snippet does not show a `validate_schema(dataframe)` function or confirm that it raises only `InsufficientDataError` on schema mismatches. Both the missing schema file and the absent/unclear implementation prevent the task from being fulfilled.
- `T009b` (rejected 1x): The required file `src/config/settings.py` does not exist, so there is no `load_config()` implementation. Moreover, even the existing `config.yaml` does not contain a top‑level `ocr_enabled` key (it has `ocr.fallback_enabled`), so the required validation could not be satisfied. The task therefore remains unfinished.
- `T014b` (rejected 1x): declared artifact(s) missing/empty/invalid: data/flagged_psd.json
- `T015c` (rejected 1x): declared artifact(s) missing/empty/invalid: data/flagged_psd.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

