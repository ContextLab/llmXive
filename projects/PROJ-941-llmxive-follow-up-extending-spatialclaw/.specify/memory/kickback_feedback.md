# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T058` (rejected 1x): The `code/stats/sensitivity.py` file exists but the provided excerpt does not show a concrete sweep over the required epsilon values nor any code that writes `results/analysis/flat_object_sensitivity.csv`. Moreover, the expected output CSV file is missing from the repository. The task’s required artifact (the CSV with the sensitivity results) is not present.
- `T060` (rejected 1x): The script `code/utils/verify_baseline_consistency.py` exists, but the required output file `results/analysis/baseline_determinism_report.md` is missing, and there is no evidence that the script actually runs the baseline twice and writes a determinism report confirming negligible variance. The task’s core requirement is therefore unmet.
- `T061` (rejected 1x): The required output file `results/analysis/bonferroni_verification.txt` does not exist, and the provided script is incomplete (truncated) with no evidence that it writes the verification results. The task’s core deliverable is missing.
- `T046` (rejected 1x): The provided `code/utils/verify_run.py` is truncated and contains obvious bugs (e.g., `return ta` instead of returning the task‑id set) and lacks the core logic to load all `results/runs/run_*.json` files, count runs per task, compare against `n_runs`, write the integrity report, and abort further analysis. Consequently the reported `run_integrity_report.json` cannot be trusted as produced by a correct implementation. The verification code must be completed and functional.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

