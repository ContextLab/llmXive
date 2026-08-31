# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directories (`code/`, `data/raw`, `data/processed`, `results`, `tests/unit`, `tests/integration`) is provided; the only artifact shown is a feature specification, not a project folder structure. The implementer must create and show these directories (with at least placeholder files) to satisfy the task.
- `T003` (rejected 1x): The provided evidence only describes user stories and testing for sparse‑attention heuristics; there are no ruff or black configuration files, scripts, or documentation present. Consequently, the required linting/formatting setup is missing.
- `T018` (rejected 1x): No code changes or files were presented showing a fallback implementation in `code/heuristics/`; the evidence lacks any artifact that selects the first k blocks when scores are near‑zero. Consequently the required logic is missing.
- `T024` (rejected 1x): declared artifact(s) missing/empty/invalid: results/benchmark_report.json
- `T025` (rejected 1x): No code, configuration, or log output was presented that adds logging for exclusion counts when RULER samples are corrupted or lack the “needle” string. The required artifact (e.g., modified inference script, logging statements, or example log file) is missing, so the task’s requirement is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

