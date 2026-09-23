# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No directory tree or file listings were provided to confirm that the requested folders (`code/`, `code/utils/`, `tests/`, `data/raw`, `data/processed`, `data/synthetic`, `models/`, `docs/`, `docs/contracts/`, `state/projects/`) actually exist. The implementer only claimed to have run the `mkdir` command without supplying any artifact or verification output.
- `T001b` (rejected 1x): No artifact (e.g., a terminal log, script, or repository commit) was provided to demonstrate that `chmod 555 data/raw` was actually run and that the directory now has read‑execute‑only permissions. Without such evidence the claim cannot be verified.
- `T006` (rejected 1x): The required file `specs/contracts/dataset.schema.yaml` is missing entirely, so no schema definition exists to verify the required fields or removal of extraneous ones. The task therefore is not satisfied.
- `T007` (rejected 1x): The required file `specs/contracts/output.schema.yaml` does not exist (the only mentioned schema file is missing), so no schema definitions for `feature_matrix` and `model_metrics` are provided. The task’s output artifact is absent.
- `T008` (rejected 1x): No logging configuration, code, or `logs/pipeline.log` file was provided; the claim lacks any artifact demonstrating that stdout capture, warning/mode‑switch logging, resource‑usage logging, or log‑rotation have been implemented. The required logging infrastructure is therefore missing.
- `T016` (rejected 1x): declared artifact(s) missing/empty/invalid: docs/research_results.md
- `T018` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/epochs.fif

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

