# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T049** — declared artifact(s) missing/empty/invalid: tests/test_se_combination.py
- **T050** — The provided `pipeline.py` only adds a warning to the results dictionary; it does not write any log entry to `data/results/run_errors.log`, and that log file is absent from the repository. Consequently, the task’s requirement to explicitly log the convergence failure reason with a unique run ID is not satisfied.
- **T051** — The required output file `data/results/power_analysis.json` does not exist, and the shown portion of `code/analysis/power.py` contains no logic that writes a JSON report with effect size, sample size, power value, or a “flag if power < 80%”. The task’s core output is therefore missing.
