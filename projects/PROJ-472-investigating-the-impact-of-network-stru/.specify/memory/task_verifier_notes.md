# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T010** — The repository lacks the required `data/raw/HCP_MMP1.0_Glasser2016.zip` file, so the script cannot verify its presence, and the provided `preprocess_dMRI.py` excerpt never shows the core `tck2connectome` conversion logic. Both the essential data file and the conversion implementation are missing.
- **T049** — The `code/analysis/report.py` file contains no logic that reads `data/results/collinearity_status.json` or inserts the required “High collinearity …” sentence, and the `data/results/collinearity_status.json` file itself is missing. Both the code change and the supporting data file are absent, so the task is not satisfied.
- **T050** — No artifact (e.g., synthetic dataset, execution logs, or generated report) was provided to demonstrate that an end‑to‑end pipeline run with N=5 was performed, that the routing logic switched correctly, and that a final report was produced without errors. The claim lacks any concrete evidence.
