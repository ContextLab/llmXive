# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T015` (rejected 1x): No code, configuration, or documentation for a logging mechanism or a schema definition for `excluded_molecules.csv` was provided; the claim lacks any tangible artifact to verify that the required error‑handling and schema registration were implemented.
- `T025` (rejected 1x): The repository lacks the required `data/processed/analysis_results.json` file, and the shown portion of `code/analysis.py` does not contain any implementation of Shapiro‑Wilk or Breusch‑Pagan tests (nor an import of `statsmodels`). Consequently the residual‑diagnostics functionality and result‑saving step are not present.
- `T036` (rejected 1x): I could find no evidence of the required plot files (`scatter_tpsa_vs_half_life.png`, `residuals.png`, `qq_plot.png`) or the `results_report.md` report in the repository; the claim provides only a textual description without any actual artifacts. The task therefore lacks the necessary non‑empty output files.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

