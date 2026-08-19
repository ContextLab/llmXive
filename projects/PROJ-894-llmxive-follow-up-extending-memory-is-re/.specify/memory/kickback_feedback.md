# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T019b` (rejected 1x): The required `data/processed/greedy_results.csv` file does not exist, and the provided `code/runner.py` is incomplete (truncated) and only contains a generic placeholder implementation that does not actually run the Greedy strategy or write the required columns to a CSV. The task’s core output is therefore missing.
- `T019c` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/noisy_lazy_results.csv
- `T013` (rejected 1x): The provided `code/runner.py` is truncated and does not contain logic to compute normalized accuracy, record nodes visited, latency, status, or write these fields to `data/processed/baseline_results.csv`. Moreover, the required `baseline_results.csv` file is absent. The task’s core output artifact is missing and the runner implementation is incomplete.
- `T019d` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/noisy_greedy_results.csv
- `T024a` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/statistical_results.json
- `T024b` (rejected 1x): No statistical analysis artifact (e.g., a CSV or report showing paired t‑test or Wilcoxon results, p‑values, confidence intervals, or Point‑Biserial correlation) was provided. The claim lacks the required output files or documented results, so the task’s requirement is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

