# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T019a` (rejected 1x): No `run_benchmarks.py` script or any related output files are present; thus there is no evidence that the required benchmark generation (exactly 10 reasoning paths per question with the specified sampling parameters on GSM8K and MMLU) has been implemented. The implementer must provide the script and a demonstration (e.g., sample output or logs) showing it produces the correct number of paths with the given settings.
- `T014` (rejected 1x): No evidence of a modified `train.py` was provided—there is no code showing validation of recursion depth, OOM detection, error logging, or a non‑zero exit on violation. The required artifact (the updated script implementing the hard‑fail behavior) is missing.
- `T019b` (rejected 1x): No `run_benchmarks.py` file or any code snippet, test output, or documentation was provided to show that the script exists, is non‑empty, and actually runs single‑path inference on MMLU and GSM8K for an accuracy baseline. Without the script (or evidence of its execution/results), the task requirement is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

