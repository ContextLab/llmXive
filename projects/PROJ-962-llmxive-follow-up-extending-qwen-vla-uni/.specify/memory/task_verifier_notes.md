# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — The provided evidence shows that `code/`, `code/utils/`, `code/tests/`, `data/raw/`, `data/processed/`, and `data/results/` directories exist, but the required `artifacts/models/` directory is not present in the artifact list. The missing `artifacts/models/` directory means the full directory structure specified in task T001a has not been created.
- **T001c** — The file `code/01_ingest_cluster.py` does exist, but it is a fully‑implemented script (13 KB of code) rather than an empty scaffold as the task required. The task explicitly demanded only an empty placeholder file, so the provided artifact does not satisfy the specification.
- **T001d** — `code/02_train_models.py` and `code/04_simulate_eval.py` exist but contain full implementations (non‑empty), and `code/03_inference.py` is missing entirely. The task required three empty files, which is not met.
- **T001e** — The three required files exist, but each contains full implementations rather than being empty placeholders as the task explicitly demanded. The task “initialize … as empty files” is not satisfied.
- **T001f** — The `code/tests/__init__.py` file is present, but the required `.gitkeep` file is missing from the `code/tests` directory. The task is not fully satisfied.
- **T004** — The provided `code/utils/seeds.py` sets Python’s `random` and NumPy seeds but never imports torch nor calls `torch.manual_seed`, contrary to the task’s requirement to set the torch seed (and any `random_state` for other libraries). Consequently the script does not ensure full reproducibility across all scripts.
- **T017** — declared artifact(s) missing/empty/invalid: data/processed/clusters.json, data/processed/assignments.parquet
- **T018** — declared artifact(s) missing/empty/invalid: data/results/coverage_report.json
- **T021a** — declared artifact(s) missing/empty/invalid: data/processed/train_embeddings.parquet, data/processed/assignments.parquet, data/processed/clusters.json, data/processed/embedding_verification.json, data/processed/train_embeddings.sha256
- **T023** — declared artifact(s) missing/empty/invalid: code/03_inference.py
- **T024** — declared artifact(s) missing/empty/invalid: code/03_inference.py
- **T025** — declared artifact(s) missing/empty/invalid: code/03_inference.py
- **T026** — declared artifact(s) missing/empty/invalid: code/bench_inference.py, data/results/inference_benchmark.csv
- **T032b** — declared artifact(s) missing/empty/invalid: data/processed/vla_proxy_baseline.parquet
- **T036** — declared artifact(s) missing/empty/invalid: data/results/fidelity_metrics.json, data/results/fidelity_scores_per_sample.json
- **T035c** — declared artifact(s) missing/empty/invalid: data/results/fidelity_scores_per_sample.json
- **T035d** — declared artifact(s) missing/empty/invalid: data/results/fidelity_scores_per_sample.json
- **T037a** — declared artifact(s) missing/empty/invalid: data/results/evaluation_report.md
- **T067** — Requested task execution failed; rerun successfully: code/run_cpu_validity_check.py exit=-1
