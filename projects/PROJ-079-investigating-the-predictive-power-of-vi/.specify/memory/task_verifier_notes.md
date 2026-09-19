# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T011a** — The repository contains the integration test file, but it writes/checks a manifest in a temporary directory, not the required `data/manifest.json`. Moreover, the actual `data/manifest.json` file is missing, so the test cannot verify that the pipeline produces the required manifest with checksums. The task’s core requirement is not met.
- **T012** — The repository lacks a `fetch_all_data` implementation in `src/download.py` (the file only contains placeholder/stub functions that raise `NotImplementedError`). Additionally, the required unified `data/manifest.json` file is missing. Consequently, the task of fetching genomes, downloading GEO data, and producing a single manifest is not satisfied.
- **T013** — No code, data files, model artifacts, or visualizations were provided; the required pipeline outputs (merged CSV, normalized matrix, interferon‑response scores, trained model file, performance metrics, and feature‑importance plots) are absent, so the task’s functional requirements are not demonstrated.
- **T014** — declared artifact(s) missing/empty/invalid: src/preprocess.py, data/processed/normalized_counts.csv
- **T015** — declared artifact(s) missing/empty/invalid: src/preprocess.py, data/processed/ortholog_map.csv
- **T016** — declared artifact(s) missing/empty/invalid: src/preprocess.py, data/processed/isg_scores.csv
- **T017** — The required file `src/preprocess.py` does not exist, so the `filter_samples` function cannot be present or verified. Consequently the task’s implementation is missing.
- **T018a** — declared artifact(s) missing/empty/invalid: src/features.py
- **T018b** — declared artifact(s) missing/empty/invalid: src/features.py
- **T018c** — The required `src/features.py` file does not exist in the repository, so the `calculate_kmer_frequencies` function cannot be inspected or used. Consequently the task of implementing k‑mer frequency extraction for k = 3 and 4 is not fulfilled. The missing file must be added with the specified function.
- **T018d** — declared artifact(s) missing/empty/invalid: src/features.py
