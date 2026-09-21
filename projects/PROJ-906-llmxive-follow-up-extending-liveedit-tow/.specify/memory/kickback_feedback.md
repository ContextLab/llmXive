# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T013b` (rejected 1x): The `stratify_by_motion` function correctly implements the threshold logic, but the required `data/flow/magnitudes.json` file is absent and the processor does not contain any code that reads this JSON to assign categories to clips. Consequently the full task—stratifying clips based on actual flow magnitudes from the dataset—is not satisfied.
- `T017` (rejected 1x): The repository lacks the required `data/metrics/baseline_results.json` file, and the provided `tests/unit/test_reporter.py` is truncated (e.g., an unfinished assertion) so it cannot verify the report generation. Moreover, the `reporter.py` implementation shown does not demonstrate writing the merged data to `BASELINE_RESULTS_PATH`. The missing output file and incomplete test mean the task’s requirements are not met.
- `T024b` (rejected 1x): The repository lacks a `data/metrics/flow_results.json` file, and the provided `code/analysis/reporter.py` snippet does not include a `generate_flow_report` implementation that merges T016b and T008 data and writes the result. Consequently the required flow‑metrics report generation is not present, so the task is not fulfilled.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

