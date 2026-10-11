# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — The `code/` and `tests/` directories exist, but the required `data/` directory and its subfolders (`data/raw/`, `data/simulation/`, `data/visualization/`, `data/reports/`) are missing. The task’s core requirement of creating the full project directory structure is not satisfied.
- **T001b** — Checked the repository and found only `requirements.txt` present with the correct package list; the required `.gitignore` and `README.md` files are missing. The task is not fully satisfied until those two configuration files are added.
- **T005** — declared artifact(s) missing/empty/invalid: data/simulation_metadata.json, code/simulation/schemas/metadata_schema.json
- **T008** — the task writes platform-owned path(s) inside the project: `.github/workflows/sim.yml` (shadows `.github/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T009** — declared artifact(s) missing/empty/invalid: data/raw/, data/simulation_metadata.json
- **T010** — The file `tests/unit/test_data_generator.py` exists, but the test calls `generate_normal_data(100, mean=5, std=2, seed=42)`, which does not match the function signature (`generate_normal_data(mean, std, n, rng=None)`) and includes an unsupported `seed` argument. Consequently the unit test will raise a `TypeError` and does not actually verify that the generated data respects the specified distribution parameters. The test needs to be corrected to use the proper arguments (e.g., `generate_normal_data(mean=5, std=2, n=100)`) and optionally pass a reproducible RNG.
- **T011a** — The provided `tests/unit/test_chi_squared_fallback.py` contains a `test_chi_squared_fallback_2x2` that does not match the task specification: it calls `run_chi_squared_with_fallback` as if it returns a tuple, asserts a non‑existent method name `"fisher_fallback",` and misuses `check_low_expected_counts`. The actual utility returns a dict with method values like `"fisher_exact"` or `"chi2_yates"`. Consequently the test will fail and does not correctly verify that a 2×2 table with expected count ≈ 3 triggers the Fisher/Yates fallback. The test must be rewritten to call the function correctly, ch
- **T016** — declared artifact(s) missing/empty/invalid: data/simulation/p_values_raw.csv
- **T018** — declared artifact(s) missing/empty/invalid: data/simulation/error_rates_summary.csv
- **T023** — declared artifact(s) missing/empty/invalid: data/simulation/thresholds.json
- **T027** — declared artifact(s) missing/empty/invalid: data/visualization/
- **T031** — declared artifact(s) missing/empty/invalid: data/simulation/real_data_pvalues.csv
- **T032** — declared artifact(s) missing/empty/invalid: data/simulation/real_data_power.json
- **T034** — declared artifact(s) missing/empty/invalid: data/simulation/validation_metrics.json
- **T033** — declared artifact(s) missing/empty/invalid: data/reports/validation_report.md
