# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No directory listings or file system evidence were provided showing that the required paths (e.g., `projects/PROJ-710-robustness-of-confidence-intervals-to-di/code/`, `.../data/`, `.../analysis/`, `.../utils/`, `.../tests/`, `.../artifacts/`) actually exist. The implementer’s claim is unsubstantiated, so the required artifact is missing.
- `T005` (rejected 1x): declared artifact(s) missing/empty/invalid: code/data/synthetic_pop.py, code/data/ground_truth.json
- `T014` (rejected 1x): The submission contains only the task description and specification excerpts; no code files, functions, or other artifacts implementing the required edge‑case logic (noise‑scale clamping, collinearity detection, bootstrap sample‑size enforcement) are present. Consequently the required reusable functions are missing, so the task is not satisfied.
- `T013` (rejected 1x): The repository lacks the required `code/data/ground_truth.json` file, so the script cannot read the ground‑truth data as specified. Moreover, the provided excerpt of `code/main.py` does not show the inner 1,000‑bootstrap‑resample loop, the per‑sample CI construction, deviation calculation, or writing to `artifacts/coverage_intermediate.csv`, and the file is truncated before any such logic. These essential components are missing, so the task is not genuinely completed.
- `T015` (rejected 1x): No `artifacts/coverage_intermediate.csv` or `artifacts/coverage_results.csv` were supplied, and there is no code or output showing the `deviation_from_nominal` column being calculated and written. The required aggregation artifact is missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

