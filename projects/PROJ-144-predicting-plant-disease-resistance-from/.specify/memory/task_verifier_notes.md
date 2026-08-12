# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory listings or screenshots were provided showing that the required folders (`code/`, `data/raw`, `data/processed`, `tests/`, `state/`, `results/`, `contracts/`) actually exist; the evidence is absent, so the task requirement is not verified.
- **T003** — declared artifact(s) missing/empty/invalid: pre-commit-config.yaml
- **T006a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T006b** — The required `contracts/metadata.schema.yaml` file is missing, and no validation output (e.g., jsonschema or yamllint results) is provided, so the task’s core requirement is not satisfied.
- **T007a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T007b** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T017** — The required output files `data/processed/batch_corrected_matrix.csv` and `data/processed/labels.csv` are absent, and the hashes recorded in `state/artifact_hashes.yaml` correspond to empty placeholders (e.g., SHA‑256 of an empty file). Consequently the task’s core requirement—generating non‑empty processed data files and recording their checksums—has not been met.
- **T022** — declared artifact(s) missing/empty/invalid: results/shap_analysis.json
- **T024** — declared artifact(s) missing/empty/invalid: results/metrics.json, results/shap_analysis.json
- **T028** — The required output file `results/pathway_barplot.png` does not exist, so the visualization was never generated despite the presence of `results/pathway_analysis.json`. The task therefore remains unfinished.
- **T029** — The claim concerns updating `README.md` with execution instructions and adding validation to `quickstart.md`, but no such files or their contents are provided in the evidence. Without the updated README and quickstart documentation, the requirement is not met. The next implementer must supply the modified `README.md` and `quickstart.md` files showing the new instructions and validation steps.
- **T030** — No GitHub Actions workflow, CI run logs, or runtime/RAM measurements were provided; thus there is no artifact demonstrating that the full pipeline was executed on the free tier and stayed within the ≤6 h and ≤7 GB limits. The required evidence is missing.
- **T031** — No code, diff, lint report, or any refactored files are present; the only provided material is a feature specification unrelated to the “code cleanup and refactoring” task, so the required artifact is missing.
