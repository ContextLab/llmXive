# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T012a** — declared artifact(s) missing/empty/invalid: src/data/extract_optical.py, data/processed/features_optical.json
- **T013a** — declared artifact(s) missing/empty/invalid: src/data/extract_audio.py, data/processed/features_audio.json
- **T016a** — The repository lacks the required input files (`features_optical.json`, `features_audio.json`) and the output CSV (`correlations_point.csv`). Moreover, `src/models/metrics.py` only defines generic correlation helpers and does not contain code that loads the JSON vectors, filters `missing_data_flag=True` samples, computes per‑dimension Pearson and Spearman point estimates, or writes the results to the specified CSV. These essential pieces are missing, so the task is not fulfilled.
- **T016b** — The provided `src/models/metrics.py` implements a custom bootstrap loop instead of using `scipy.stats.bootstrap` with `method="basic"` and does not perform stratified sampling. No code writes the required `data/processed/correlations.csv`, and the file is absent. Consequently the bootstrapping implementation and the expected output artifact are missing.
