# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T032** — The repository lacks the required `data/processed/sensitivity_analysis.json` file, and the shown portion of `code/analysis.py` does not contain any implementation of a sensitivity‑analysis loop, R² recording, Kruskal‑Wallis test, or JSON saving logic. Consequently the task’s specifications are not met.
- **T033** — declared artifact(s) missing/empty/invalid: data/processed/model_results.json
- **T039** — The required output files `data/processed/vif_analysis.json` and `data/processed/vif_iteration_log.json` are absent, and the provided `code/analysis.py` excerpt ends before any iterative VIF‑retraining logic is shown. Without these artifacts, the task’s specifications are not satisfied.
- **T040** — The required output file `data/processed/feature_importance.csv` does not exist, and the provided `code/analysis.py` snippet (truncated) shows no implementation that computes permutation importance and writes the ranked list to that path. The task’s core artifact is missing.
- **T043** — The repository contains a partially‑implemented `code/plotting.py`, but it does not include code that iterates over the top‑5 features, creates the required seaborn regplots, and writes a PNG to `data/processed/corr_plot_top5.png`. Moreover, the expected output file `data/processed/corr_plot_top5.png` is absent. The task’s core deliverable – the saved scatter‑plot image – is missing.
- **T045** — declared artifact(s) missing/empty/invalid: data/processed/analysis_summary.json
