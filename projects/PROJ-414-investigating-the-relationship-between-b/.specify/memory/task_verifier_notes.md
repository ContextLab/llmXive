# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — Requested task execution failed; rerun successfully: tests/test_extract.py exit=1
- **T004** — Requested task execution failed; rerun successfully: code/connectivity.py exit=1
- **T006** — Checked `code/analysis.py` and `results/power_analysis.json`. The power analysis JSON is present and contains the correct fields, but the implementation explicitly avoids `statsmodels` and computes the required sample size with a custom Fisher‑z approximation, violating the task’s requirement to use `statsmodels.stats.power`. Consequently the power analysis does not meet the specification. (The missing `regression_results.csv` is acceptable because no skill‑proxy column is present.)
- **T007** — Requested task execution failed; rerun successfully: code/sensitivity.py exit=1
- **T008** — Requested task execution failed; rerun successfully: code/visualization.py exit=1
