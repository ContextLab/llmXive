# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T012b** — The `src/services/ingest.py` file does not contain the required `validate_sampled_graph` implementation (the shown excerpt only includes imports and `fetch_sample_ids`). Moreover, the expected output files `artifacts/results/sampling_validation.json` and `artifacts/results/topology_equivalence.json` are absent. Both the core function and its result artifacts are missing, so the task is not fulfilled.
- **T016** — The required Parquet file `data/processed/subgraph_with_clusters.parquet` does not exist, and the YAML state file still contains a placeholder hash instead of a real SHA‑256 hash and updated timestamp. Consequently the task’s core output and integrity update are missing.
- **T021a** — No code, logs, or test output showing a validation step for the selected `k` (silhouette stability across seeds) is present. The required artifact—implementation of the stability check and evidence that it runs and logs the chosen `k`—is missing.
