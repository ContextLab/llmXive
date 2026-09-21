# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T017** — declared artifact(s) missing/empty/invalid: data/curated/curated_dataset.csv
- **T018** — declared artifact(s) missing/empty/invalid: data/curated/curated_dataset.csv, data/processed/descriptors.csv
- **T019** — The required `data/curated/curated_dataset.csv` does not exist, so no hash can be computed, and `code/utils/hash_state.py` contains only generic utility functions without any code that actually calculates and records the SHA256 of that specific CSV file. The task’s core requirement is therefore unmet.
- **T024** — The required input CSV (`data/curated/curated_dataset.csv`) and the generated output file (`data/processed/graphs.pt`) are both missing, and the provided `graph_build.py` is incomplete (truncated) and does not demonstrate writing the PyG `Data` objects to the expected `.pt` file. The task therefore is not fulfilled.
- **T025** — No `analysis/topology_audit.md` file was provided, nor any excerpt showing its contents. Without the markdown file containing the required sections (Node Counts, Edge Counts, Pruning Statistics, Physical Parameterization Summary), the claim that the task is complete cannot be verified. The implementer must supply the generated `analysis/topology_audit.md` with the specified information.
