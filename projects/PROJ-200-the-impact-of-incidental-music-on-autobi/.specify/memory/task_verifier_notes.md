# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T029** — The required artifact `data/processed/user_track_pairs.parquet` is absent from the repository (the file does not exist), so no real dataset or checksum can be verified. Although `state.yaml` lists an entry for the file, the actual Parquet file is missing, violating the task requirement. The implementer must create the Parquet file (non‑empty) and ensure its checksum matches the entry in `state.yaml`.
- **T045** — The repository lacks a `run_permutation_test` implementation in `code/modeling.py` (the shown code ends inside `fit_mixed_model` and never defines the required function), and the expected output file `data/final/permutation_results.csv` does not exist. Both the core function and its result artifact are missing.
- **T038** — declared artifact(s) missing/empty/invalid: data/final/regression_summary.csv
- **T039** — declared artifact(s) missing/empty/invalid: data/final/sensitivity_analysis.csv, data/final/permutation_results.csv
- **T040** — No diagnostic plots (e.g., residual checks, QQ plots) were found in the required `data/final/plots/` directory, nor any evidence (files, screenshots, code) indicating they were generated and saved. The task’s deliverable is missing.
- **T041** — No README.md or code docstring contents were provided; without the actual files we cannot confirm that documentation was updated to reflect the specification changes. The required artifacts are missing.
