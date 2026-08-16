# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T065a** — The review found no `code/schemas/injected_datasets.json` or `code/schemas/clusters.json` files, nor any inline JSON schema definitions for these artifacts. Without the required schema files, the task’s deliverable is missing.
- **T012** — The provided `code/data_loader.py` contains only dataset downloading and loading logic and explicitly forbids synthetic fallbacks; it lacks any synonym‑replacement or sentence‑shuffling implementation, does not generate clusters, and never writes `data/processed/injected_datasets.json` (the file is missing). Consequently the required synthetic redundancy injection and validation artifacts are absent.
