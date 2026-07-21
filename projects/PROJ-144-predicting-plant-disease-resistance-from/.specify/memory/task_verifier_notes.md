# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required directories (`code/`, `data/raw`, `data/processed`, `tests/`, `state/`) was provided; without a directory listing or files, we cannot confirm that the project structure exists. The implementer must create and show these folders (and at least placeholder files) to satisfy the task.
- **T003** — declared artifact(s) missing/empty/invalid: pre-commit-config.yaml
- **T006** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T017** — declared artifact(s) missing/empty/invalid: data/processed/batch_corrected_matrix.csv, data/processed/labels.csv
- **T022** — No code, script, notebook, or other artifact implementing VIF calculation and flagging metabolites with VIF > 5 is present; the only information is the task description itself, which does not constitute the required implementation.
- **T023** — No output documentation artifact was provided that demonstrates the findings are framed as “associational.” Without a report, summary, or any written results to inspect, we cannot verify that the implementer has ensured all findings are presented in an associational manner as required by FR‑011. The required artifact is missing.
- **T024** — Both required output files (`results/metrics.json` and `results/shap_analysis.json`) are missing from the repository, so no metrics or SHAP analysis have been logged as the task demands. The implementer must generate and save these JSON files with the appropriate logged data.
- **T025** — The repository lacks the required `code/modeling/interpret.py` file entirely, and the provided `tests/unit/test_modeling.py` contains no test exercising `map_metabolites_to_pathways` (or any other interpret module functionality). Consequently, the unit test for pathway‑mapping logic is missing.
- **T026** — declared artifact(s) missing/empty/invalid: code/modeling/interpret.py
- **T028** — declared artifact(s) missing/empty/invalid: results/pathway_barplot.png
- **T029** — The claim concerns updating `README.md` with execution instructions and adding validation to `quickstart.md`, but no such files or their contents are provided in the evidence. Without the updated README and quickstart documentation, the requirement is not met. The next implementer must supply the modified `README.md` and `quickstart.md` files showing the new instructions and validation steps.
