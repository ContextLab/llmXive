# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T028` (rejected 1x): No code, script, or documentation was provided that shows the implementation of logic to flag non‑compliant days while preserving the data for later analysis. The required artifact (e.g., a function, module, or database update rule) is missing, so the task is not satisfied.
- `T020` (rejected 1x): The required output file `results/power_analysis.json` does not exist, and the provided `power_simulation.py` snippet shows only data loading and a partial simulation function with no evidence of a 1,000‑iteration Monte Carlo loop, Holm‑Bonferroni correction per iteration, or JSON writing. The task’s core deliverables are therefore missing.
- `T029` (rejected 1x): declared artifact(s) missing/empty/invalid: results/sensitivity_analysis_report.md

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

