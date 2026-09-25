# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007a** — The submission contains no `data_version.json` (or schema definition) file, nor any description of its fields. Consequently the required schema with `source_url`, `checksum_sha256`, and `timestamp` is missing. The next implementer must create and provide the JSON schema file (or equivalent documentation) containing those three fields.
- **T007b** — declared artifact(s) missing/empty/invalid: src/main.py
- **T008** — declared artifact(s) missing/empty/invalid: src/data/utils.py
- **T009** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T012** — The required artifact `tests/integration/test_data.py` does not exist, so no integration test is present to verify end‑to‑end fetching and descriptor calculation. The task cannot be considered fulfilled until this file is created with a functional test.
- **T013** — declared artifact(s) missing/empty/invalid: src/data/download.py
- **T014** — declared artifact(s) missing/empty/invalid: src/data/process.py
- **T015** — declared artifact(s) missing/empty/invalid: src/data/process.py
- **T016** — The implementer did not provide a `data/processed/merge_metrics.json` file, nor any content showing the required `total_requested`, `matches`, and `fraction` fields. Without the actual JSON artifact, the task requirement is unmet.
- **T017** — declared artifact(s) missing/empty/invalid: src/data/download.py
- **T022** — declared artifact(s) missing/empty/invalid: src/analysis/dimensionality.py, data/processed/umap_embedding.csv
- **T023** — declared artifact(s) missing/empty/invalid: src/viz/plots.py, data/processed/umap_scatter.png
- **T023b** — No `clustering_results.json` file (or any other artifact) containing a logged silhouette score for the UMAP embedding is present. The implementer did not provide evidence that the score was calculated or recorded, so the task requirement is unmet.
- **T024** — declared artifact(s) missing/empty/invalid: src/analysis/clustering.py
- **T027** — No code, script, or output file implementing the “exclude clusters with <10 samples and flag as ‘insufficient power’” was provided. The evidence consists only of the task description and specification excerpt, without any concrete artifact (e.g., updated clustering/enrichment module, unit tests, or example results) demonstrating that the required logic has been added. The implementer must supply the actual implementation and proof (e.g., source file changes, test logs, or generated ranking output) showing the new exclusion behavior.
- **T025** — declared artifact(s) missing/empty/invalid: src/analysis/clustering.py
- **T026** — declared artifact(s) missing/empty/invalid: src/analysis/clustering.py, src/config.py
- **T028** — No `clustering_results.json` file or its contents were presented; the claim provides only a description without the required JSON artifact containing cluster IDs, enrichment and permutation p‑values, and diagnostic messages. Consequently the task’s deliverable is missing.
