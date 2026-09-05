# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007** — declared artifact(s) missing/empty/invalid: code/validate_schema.py, data/derived/schema_validation.json
- **T011a** — The submission contains only the task description and acceptance criteria; there are no actual code files, computed power estimates, fitted model outputs, or visualizations provided. Consequently, the required preprocessing script, power calculations, model results, and plots are missing, so the task is not genuinely completed.
- **T011c** — The `code/model_fit.py` file is present but incomplete (truncated and ends with an unfinished statement), and the required output artifacts `results/lmm_final_summary.json` and `data/derived/residuals.csv` do not exist. Consequently, the task’s deliverables are not fully provided.
- **T013** — The repository contains `code/visualize.py`, but the required input `data/derived/residuals.csv` is missing, and the expected output `results/power_drift_scatter.png` was not generated. Without the data file the script cannot run, and the verification step (existence and non‑zero size of the plot) fails. The missing files must be provided and the script executed to produce the plot with the regression line and confidence interval.
- **T025** — declared artifact(s) missing/empty/invalid: code/aggregate.py
- **T027** — No code, script, data file, or report implementing the required input permutation validation (the non‑parametric permutation test for the power‑drift analysis) is present; the claim provides no artifact to verify that the permutation test logic was added. Consequently the task’s requirement is not satisfied.
- **T030** — declared artifact(s) missing/empty/invalid: results/final_report.md
- **T031** — No pytest execution log, report, or test result artifacts are present; the implementer provided no evidence that unit or integration tests were run or that they all passed. Consequently, the requirement to run `pytest` and verify test success is not satisfied.
- **T032** — No updated `README.md` file is provided or shown; there is no evidence of execution instructions or expected output descriptions being added. The required artifact is missing, so the task is not satisfied.
