# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T012** — The claim provides no evidence that a `research.md` file exists with a new section citing the source for the Cohen's f = 0.25 effect size. No file content or diff is shown, so we cannot verify that the required documentation was added. The implementer must supply the updated `research.md` containing the citation and justification.
- **T012#1** — The `calculate_anova_power` function computes the sample size but does not implement the required check to raise `SystemExit` when `total_n < 50`, and the script never calls `save_power_analysis` to create `data/analysis/power_report.json` (the file is missing). The implementation must add the power‑threshold guard and ensure the JSON report is written (with only the required keys).
- **T015** — declared artifact(s) missing/empty/invalid: code/stimuli/asset_generator.py
