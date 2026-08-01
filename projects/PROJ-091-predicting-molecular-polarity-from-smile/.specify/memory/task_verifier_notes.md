# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T018** — declared artifact(s) missing/empty/invalid: data/processed/descriptors.parquet
- **T019** — The `code/main.py` defines the validation functions but does not invoke them in the execution flow, and the required `data/processed/descriptors.parquet` file is absent, so the runtime assertion cannot actually verify a valid descriptors file.
- **T026** — declared artifact(s) missing/empty/invalid: data/processed/model.pkl
- **T032** — The repository contains a partially‑written `code/models/interpret.py` (the file ends abruptly and the `get_cluster_aware_importance` function is incomplete), and the required input artifacts `data/processed/descriptors.parquet` and `data/processed/model.pkl` are absent, so the script cannot perform the intended Cluster‑Aware SHAP analysis. The task’s core requirements are therefore not satisfied.
- **T034a** — No artifact (e.g., script, notebook, data file, or result table) showing the computed Jaccard similarity of top feature clusters across multiple bootstrap resamples is present; the claim provides only a description without any concrete output. The required evidence is missing.
- **T034b** — The submission provides no code, data, or results showing that Jaccard similarity of top SHAP features across bootstrap resamples was computed; there is no artifact (script, output file, or figure) demonstrating compliance with spec SC‑003. Consequently the required deliverable is missing.
- **T036** — No SHAP summary plot, feature‑importance report, or any files distinguishing collinear clusters were supplied. The implementer’s response contains only the task description and project context, without the required visual or data artifacts, so the requirement is not met.
