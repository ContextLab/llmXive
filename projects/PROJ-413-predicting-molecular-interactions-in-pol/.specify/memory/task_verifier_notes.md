# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T017** — declared artifact(s) missing/empty/invalid: data/curated/curated_dataset.csv
- **T018** — declared artifact(s) missing/empty/invalid: data/curated/curated_dataset.csv, data/processed/descriptors.csv
- **T019** — The required `data/curated/curated_dataset.csv` file does not exist, so its SHA256 cannot be computed. Moreover, `code/utils/hash_state.py` only defines generic hashing utilities and never calls `compute_sha256` on the specific `curated_dataset.csv` (or stores the result), so the task’s requirement is not fulfilled.
- **T024** — The required input file `data/curated/curated_dataset.csv` and the output file `data/processed/graphs.pt` are both absent, so the conversion pipeline cannot have been executed. Moreover, the provided `graph_build.py` is incomplete (truncated) and does not clearly implement the specified atom‑type‑to‑integer and bond‑order‑to‑float mapping or produce a PyG `Data` object with only the topological features required. The task therefore remains unfinished.
