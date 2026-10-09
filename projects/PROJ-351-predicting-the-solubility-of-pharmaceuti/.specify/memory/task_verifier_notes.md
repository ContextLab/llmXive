# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — No linting or formatting configuration files (e.g., .flake8, pyproject.toml/black settings, or pre‑commit hooks) are present in the provided artifacts, so the requirement to configure flake8/black is not satisfied.
- **T003b** — The `contracts/model_output.schema.yaml` file is present, but its contents only define `status`, `artifacts`, and `errors`; it does not define the required structures for `metrics`, `statistical_test`, or `viz_manifest` as the task specifies. The schema therefore does not satisfy the task’s requirement.
- **T004** — Requested task execution failed; rerun successfully: code/data/download_esol.py exit=1
- **T005** — The script does not produce the required `data/processed/cleaned_graphs.pkl` (file is missing) and its output dictionaries lack the mandated keys (`mol` and a combined `features` dict) while also omitting SMILES canonicalization. Additionally, the exclusion log is written to the output directory rather than `data/logs/exclusions.log`, violating the logging location requirement.
- **T005b** — declared artifact(s) missing/empty/invalid: code/data/graph_tensorizer.py, data/processed/cleaned_graphs.pkl, data/processed/graph_tensors.pt
- **T009** — declared artifact(s) missing/empty/invalid: code/config.py
- **T024** — declared artifact(s) missing/empty/invalid: results/gnn_predictions.csv, results/gnn_metrics.json
- **T030** — declared artifact(s) missing/empty/invalid: code/evaluation/visualize_molecules.py, data/processed/aggregated_predictions.json, code/config.py, docs/reports/interpretability_plots/, results/viz_manifest.json
- **T032** — declared artifact(s) missing/empty/invalid: code/evaluation/write_metrics.py, results/metrics.json
- **T034** — declared artifact(s) missing/empty/invalid: results/final_report.json
