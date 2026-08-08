# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T012** — No code changes to `logic_generator.py`, no generated dataset, and no metadata flags or statistical validation are present. The required artifact (the updated generator script and the ≥3,000 samples partitioned into High‑Entropy, Low‑Entropy, and Target‑Specific subsets) is missing, so the task is not satisfied.
- **T013** — declared artifact(s) missing/empty/invalid: data/raw/test_set.csv
- **T014** — No code, script, or test output showing a contradiction‑detection step (e.g., a SAT‑based solvability check) is present. The provided artifacts only describe dataset generation and distillation pipelines; there is no implementation or evidence that unsolvable problems are identified and discarded. Implementer must add the SAT‑check logic and demonstrate it works (e.g., logs or unit tests).
- **T016** — declared artifact(s) missing/empty/invalid: data/raw/high_entropy.csv, data/raw/low_entropy.csv, data/raw/target_specific.csv, data/raw/test_set.csv
- **T044** — No code, script, test, or documentation showing a hash‑based distinctness check was added to the generator is present. The required artifact (implementation of the distinctness verification and evidence it is used by T013) is missing, so the task is not satisfied.
- **T024** — The submission contains no code, script, or documentation showing that early‑stopping logic was added to any training loop, nor any record of the epoch when a loss threshold is first met. Without such artifacts, the task requirement is not satisfied.
- **T025** — No code, script, or logs showing that `ResourceMonitor` hooks were added to the training script, that RAM usage is capped at 7 GB, that a 6‑hour wall‑clock limit is enforced, or that a specific error code is emitted on breach are present. The required artifact is missing, so the task is not satisfied.
- **T026** — No `DistillationRun` JSON files are present in `data/processed/`, and there is no evidence (e.g., command logs, script output) showing that `distill_loop.py` was run for the High, Low, and Target datasets. The required artifacts are missing, so the task is not satisfied.
- **T042** — declared artifact(s) missing/empty/invalid: data/processed/trace_consistency_report.json
- **T033** — declared artifact(s) missing/empty/invalid: data/processed/statistical_results.json
