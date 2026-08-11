# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T011** — The repository contains a `tracing.py` file, but it is truncated and shows no evidence of iterating over 100 ImageNet validation images, saving routing matrices, or producing the required log files. Both `data/results/tracing_log.jsonl` and `data/results/memory_profile_raw.jsonl` are missing, and there are no routing cache files in `data/routing_cache/`. The task’s core outputs are absent.
- **T012** — The provided `clustering.py` is truncated and does not contain code that saves cluster centers to `data/routing_cache/cluster_centers.json`, prints the silhouette score, or implements the null‑hypothesis fallback. Moreover, the required `cluster_centers.json` file is missing entirely. The task’s core output is therefore not present.
- **T013** — The repository contains `code/src/canonical_map.py`, but the required output file `data/routing_cache/canonical_map.json` is missing, so the verification step cannot be satisfied. The implementation has not produced the expected JSON artifact.
- **T036** — declared artifact(s) missing/empty/invalid: src/tracing.py, src/benchmark.py
- **T037** — The required file `src/tracing.py` is missing entirely, so there is no code to verify batch size, memory logging, or RAM usage. Without the artifact, the task cannot be considered fulfilled.
- **T038** — declared artifact(s) missing/empty/invalid: src/clustering.py, data/results/null_hypothesis_flag.json
- **T018** — The repository contains a `static_model.py` file, but the implementation is truncated, has an unfinished `get_static_routing_weight` method, and never loads the required `data/routing_cache/canonical_map.json`. Moreover, the `canonical_map.json` file itself is missing, so the model cannot be instantiated with the static routing map as required.
- **T029** — declared artifact(s) missing/empty/invalid: src/benchmark.py
- **T019** — The repository lacks a functional `src/metrics.py`, and the required result files `data/results/benchmark_results.csv` and `.json` are not present. Moreover, `benchmark.py` contains placeholder generation logic and does not actually run inference, compute FID, or write the specified schema, so the task’s core requirements are unmet.
