# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T029** — The repository contains a `code/06_permutation_test.py` file, but it does not import the training logic from `code/04_train_model.py` and the file is truncated before showing the full implementation. Moreover, the required output file `data/processed/permutation_results.json` is missing. Consequently, the task’s specifications are not satisfied.
- **T035** — The provided `code/03_compute_graph_metrics.py` shows no import or use of `joblib.Parallel` (or any parallel construct) and contains only a sequential processing flow. There is also no code or reported metrics demonstrating that the runtime for 100 subjects was reduced to under 30 minutes. The required refactor and verification are missing.
