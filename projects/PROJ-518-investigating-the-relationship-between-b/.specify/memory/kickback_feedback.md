# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T017` (rejected 1x): The provided information contains no code, test results, or output showing that the `fit_regression` function now computes and reports the Pearson correlation coefficient between flexibility and creativity. The required artifact—a modified `fit_regression` implementation (or its execution log) that produces the numeric r‑value (and optionally its p‑value) is missing. The next implementer must add the correlation calculation to `fit_regression` and supply evidence (e.g., code diff, console output, or saved results) that it runs without error and reports the coefficient.
- `T018` (rejected 1x): No evidence of a `loader.py` file containing the required `validate_and_filter_subjects` function is provided; without the actual code we cannot confirm the function exists, is non‑empty, logs warnings for missing scans, and excludes subjects with missing behavioral scores as specified. The implementer must supply the updated `loader.py` with the new function and demonstrate its behavior.
- `T019` (rejected 1x): No code defining `filter_by_motion` (or any related module) is present, nor any log output demonstrating that participants exceeding the FD or volume‑threshold criteria are excluded. The required function and its logging behavior are missing, so the task is not satisfied.
- `T020` (rejected 1x): No code, test suite, or documentation was provided showing that the `log_exclusion` function is invoked with the exact standardized reason codes (`MISSING_SCAN`, `MISSING_SCORE`, `HIGH_MOTION`) for every exclusion decision. The required artifact (implementation and/or verification evidence) is missing.
- `T022` (rejected 1x): The provided `plot_flexibility_vs_creativity` function stops after handling the “no valid data” case and does not contain code that fits a regression model, draws the regression line, or adds a confidence band. Moreover, the expected output image `docs/outputs/flexibility_vs_creativity.png` is absent, indicating the function has not been exercised to produce the required plot. The implementation therefore does not meet the task’s specification.
- `T023` (rejected 1x): The repository does not contain the required `model_residuals.png` and `model_qq.png` files, and the provided excerpt of `code/viz/plots.py` shows no implementation of a `plot_residuals` function (the file is truncated before any such definition). Consequently the task’s core requirement—generating and saving the residuals‑vs‑fitted and QQ plots—is not satisfied.
- `T030` (rejected 1x): declared artifact(s) missing/empty/invalid: data/interim/permutation_results.csv, data/interim/sensitivity_summary.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

