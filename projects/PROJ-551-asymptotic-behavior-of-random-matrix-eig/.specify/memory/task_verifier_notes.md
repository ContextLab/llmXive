# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T019a** — No NumPy code or saved `.npy` files were presented; the required `data/raw/matrix_N{N}_seed{seed}.npy` files do not exist in the provided evidence, so the task of generating and persisting raw Wigner matrices is not demonstrated.
- **T019** — The required output file `state/checksums_raw.json` does not appear in the provided evidence, and no SHA‑256 checksums of the raw matrix instances are present. Consequently the task’s core requirement—generating and recording those checksums—is not satisfied.
- **T015** — declared artifact(s) missing/empty/invalid: data/processed/single_run_results.json
- **T040a** — No files were found in the repository at the required path `data/raw/sweep/matrix_N{N}_theta{theta}_seed{seed}.npy`, and no code or logs were provided that generate such raw matrix instances. Consequently the task’s deliverable – the full set of raw matrix `.npy` files for the parameter sweep – is missing.
- **T040b** — No `state/checksums_sweep.json` file or any other evidence of computed SHA‑256 checksums for the raw matrix instances from T040a is present. The required artifact is missing, so the task is not satisfied.
- **T021a** — The repository contains `code/analysis/monte_carlo_runner.py`, but the provided snippet is truncated and does not show any code that writes results to `data/processed/mc_results.csv`. Moreover, the required CSV file is absent from the project. Without a concrete implementation that outputs the specified schema and the actual CSV file, the task is not fulfilled.
- **T021b** — declared artifact(s) missing/empty/invalid: data/processed/mc_results.csv, data/processed/threshold_identification_raw.json
- **T022c** — declared artifact(s) missing/empty/invalid: data/processed/threshold_fit_params.json
- **T024** — declared artifact(s) missing/empty/invalid: data/processed/threshold_sweep_results.csv
- **T025** — declared artifact(s) missing/empty/invalid: data/figures/outlier_probability_vs_theta.png
- **T031** — declared artifact(s) missing/empty/invalid: data/logs/edge_case_rank0.log
- **T028** — declared artifact(s) missing/empty/invalid: data/processed/sensitivity_density_sweep.csv
- **T029a** — declared artifact(s) missing/empty/invalid: data/processed/sensitivity_variation.csv
