# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T035** — The required artifact `data/processed/collinearity_report.json` does not exist, and the provided `code/analysis.py` contains no implementation for checking the config for “population density” or “precinct size”, computing VIF values, or writing the JSON report. The task’s core functionality is therefore missing.
- **T039** — The repository contains a `config/sensitivity_thresholds.yaml` file, but `code/analysis.py` does not show any implementation that loads these thresholds, runs a sensitivity sweep, compares Negative Binomial vs. Permutation models, or writes a unified report/plot. Moreover, the required output files `data/processed/results.json` and `data/processed/sensitivity_report.md` are absent. The task’s core requirements are therefore not satisfied.
- **T041** — declared artifact(s) missing/empty/invalid: code/viz.py
