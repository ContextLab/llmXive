# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T008a** — The provided `code/imbalance.py` contains functions that compute the Gini‑based target imbalance scores and correctly skip properties with fewer than 100 samples, but the script does not produce (or the repository does not contain) the required `results/target_imbalance_scores.csv` file. The CSV output artifact is missing, so the task’s deliverable is not satisfied.
- **T008b** — The repository lacks the required input file `data/processed/descriptors.parquet` and the expected output `results/compositional_imbalance_score.csv`. Moreover, `code/imbalance.py` is truncated and never completes the compositional imbalance calculation (no K‑Means clustering with k=50 or Gini of cluster counts). The implementation does not fulfill the specified task.
