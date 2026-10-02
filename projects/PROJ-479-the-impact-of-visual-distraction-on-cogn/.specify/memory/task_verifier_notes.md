# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T035** — No code, script, or documentation was provided showing that the analysis pipeline was updated to apply `scipy.stats.multitest.multipletests(method='holm')`. The required artifact (an analysis script with Holm‑Bonferroni family‑wise error correction) is missing, so the task is not satisfied.
- **T036** — The required `results/statistics/multiplicity_table.csv` file is missing, so the core output cannot be verified. Although the Holm‑Bonferroni citation is present in `data/citations.yaml`, there is no evidence that it was embedded in a report via T045. The task therefore remains unfinished.
- **T036a** — declared artifact(s) missing/empty/invalid: results/statistics/summary_p_values.md
- **T019a** — The repository lacks the required `results/statistics/power_analysis_a_priori.md` file, and the provided `code/03_analysis.py` (even though it imports `FTestPower`) does not contain any implementation that performs the a‑priori power calculation or writes the markdown report. The task’s core deliverable is therefore missing.
