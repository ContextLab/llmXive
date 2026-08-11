# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T022d` (rejected 1x): The `src/validation/reconstruction_error.py` file exists but its implementation is truncated and does not show the required logic to write the mean and maximum error (and the validity flag) to `data/results/reconstruction_error.json`. Moreover, the expected JSON result file is absent from the repository. The task therefore remains unfinished.
- `T022e` (rejected 1x): The `generate_eval_tasks.py` script is incomplete (truncated and lacks logic to write `data/processed/eval_tasks.yaml`), and the required output file `data/processed/eval_tasks.yaml` does not exist. The task’s core requirement—producing a populated eval_tasks.yaml with held‑out task IDs or deterministic composite descriptions—is therefore unmet.
- `T030` (rejected 1x): The repository contains a partially‑implemented `src/validation/linearity_check.py` (the file is truncated and never writes the required JSON output or handles the “staged” mock‑data case). Moreover, the required input `data/processed/pairs.yaml` and the expected result file `data/results/linearity_check.json` are absent. The implementation does not satisfy the specification.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

