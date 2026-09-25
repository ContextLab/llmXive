# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory tree or file list showing the required folders (`src/data`, `src/analysis`, `src/utils`, `src/cli`, `tests/unit`, `tests/integration`, `data/raw`, `data/processed`, `data/results`, `results`, `state`) is provided. The claim lacks any concrete evidence that the project structure was actually created.
- **T012** — The `src/data/generate_primes.py` file is truncated (the `run_pipeline` function ends abruptly and never writes any CSV), and the required output file `data/processed/raw_gaps.csv` does not exist. Consequently, the prime‑gap generation and streaming to the specified CSV file have not been realized.
- **T015** — The `src/data/ingest_zeros.py` script is present but truncated and never writes to `data/raw/zeta_zeros.csv` (its `OUTPUT_FILE` points to `data/processed`). Moreover, the required output file `data/raw/zeta_zeros.csv` does not exist at all. The ingestion logic therefore does not satisfy the task’s requirement to fetch, parse, and populate the raw CSV file.
- **T018b** — The provided `distribution_test.py` contains only stub functions and comments; it does not implement the sliding‑window computation, normalization, or CSV writing. Moreover, the required output file `data/processed/maximal_gaps.csv` is absent. The task’s core functionality and output artifact are therefore missing.
- **T022** — declared artifact(s) missing/empty/invalid: results/ks_test_results.json
- **T024** — No code, data, or result files were presented that compute or report the p‑value for the observed distributional alignment against the Cramér null distribution. The required artifact (e.g., a script or output file containing the calculated p‑value) is missing, so the task is not satisfied.
- **T025** — declared artifact(s) missing/empty/invalid: results/correlation_plot.png, results/correlation_results.json
- **T027** — The required artifact `tests/integration/test_robustness.py` does not exist on disk, so the integration test for the sensitivity sweep cannot be verified. The task remains unfinished until the file is created with appropriate test code.
- **T028** — declared artifact(s) missing/empty/invalid: src/analysis/robustness.py, results/robustness_sweep.json
- **T029** — declared artifact(s) missing/empty/invalid: data/null/cramer_sample.csv
