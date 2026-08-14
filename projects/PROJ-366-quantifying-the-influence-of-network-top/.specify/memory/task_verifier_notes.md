# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T015** — No files or code were presented that create, serialize, or store graph objects under `data/processed/graphs/` in pickle or parquet format, nor any checksum generation/check verification. The required artifact is missing, so the task is not satisfied.
- **T016** — declared artifact(s) missing/empty/invalid: data/processed/graphs/node_degree_stats.json
- **T023** — No code, script, or JSON example showing the new convergence detection logic or the updated `ThermalSample` metadata with a `converged` field is provided. The required artifact (implementation that checks relative change < 1 % and writes `converged: false` on failure) is missing.
- **T024** — The required output file `data/processed/graphs/excluded_samples.json` does not exist, even though `config.yaml` sets `enforce_exclusion: true`. Without this file the outlier detection and exclusion step is not implemented, so downstream tasks cannot filter against it. The implementer must create the JSON file with the excluded sample IDs (or at least a placeholder) when the flag is true.
- **T025** — No evidence of a `data/processed/conductivities/` directory containing saved `ThermalSample` objects (graph, conductivity, metadata) was provided, nor any indication that checksums are computed and stored. The required artifact is missing, so the task is not satisfied.
- **T026** — The required output file `data/processed/conductivities/convergence_report.json` does not exist, so there is no way to verify its contents or that a thermal conductivity value falls within the configurable range. The task therefore remains unfinished.
- **T035** — declared artifact(s) missing/empty/invalid: data/processed/model_outputs/power_analysis.json
- **T032** — No code, notebook, script, or output files implementing or demonstrating SHAP (or similar) feature‑importance extraction from a trained GNN are present. Without such artifacts, we cannot confirm that the required functionality was actually delivered. The implementer must provide the implementation (e.g., a Python module or notebook) and example results showing per‑sample importance scores.
