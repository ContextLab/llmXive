# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of the required `projects/PROJ-150-detecting-statistical-power-drift-in-rep/` directory or its subfolders (`data/raw`, `data/derived`, `code`, `tests`, `results`, `state`) is provided; the “Actual artifacts / evidence on disk” section is empty, so the claim that the directory structure was created cannot be verified. The implementer must supply a listing or screenshot showing the created directories.
- `T001b` (rejected 1x): No `.gitignore` file content or path was provided, so we cannot confirm that a non‑empty file exists with the required exclusions (`data/raw`, `data/derived`, `__pycache__`, `.env`). The implementer must supply the actual `.gitignore` artifact showing those patterns.
- `T012a` (rejected 1x): The repository lacks the required output files (`data/derived/input_trends_models.pkl` and `data/derived/input_trends_raw.pkl`). Moreover, the provided `code/compute_trends.py` only fits a mixed model with a random intercept for `field` and does not include the `original_study_id` random effect, nor does it implement saving of the raw parameters to `input_trends_raw.pkl`. The script is also incomplete (e.g., missing imports, truncated `main`). These issues must be fixed for the task to be considered complete.
- `T012b` (rejected 1x): The repository contains `code/compute_trends.py`, but the script is truncated (the `main()` function is incomplete) and there is no `data/derived/lmm_summary.csv` file on disk. Since the required output CSV is missing (and thus cannot be checked for non‑null float values in [0, 1]), the task’s deliverable has not been satisfied. The next implementer must finish the script (ensure it runs end‑to‑end) and generate the `lmm_summary.csv` with the specified columns and valid values.
- `T013` (rejected 1x): The repository contains a partially‑implemented `code/analyze_drift.py`, but the file is truncated and does not show any likelihood‑ratio test computation or JSON writing. Moreover, the required output `data/derived/lrt_results.json` is absent. The task’s core deliverable (performing the LRT and saving the result) is therefore not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

