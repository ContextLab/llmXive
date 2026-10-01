# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T017` (rejected 1x): The repository contains `code/data/generate_perturbations.py`, but it is incomplete (truncated) and does not show the logic that iterates over tasks, generates up to three candidates per task, enforces the 656‑sample cap, or writes the unfiltered list to `data/processed/perturbation_candidates_raw.json`. Moreover, the required JSON file is absent, so the core output and verification step are missing. The next implementer must finish the generation loop, ensure deterministic ordering, enforce the cap, and create the correctly‑structured `perturbation_candidates_raw.json` file.
- `T021` (rejected 1x): The required output file `data/processed/inference_logs.json` does not exist, and the provided `code/model/inference.py` is incomplete (truncated) with no evidence of fallback model selection, timeout enforcement, code execution logging, or writing to the specified JSON schema. The task’s core requirements are therefore unmet.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

