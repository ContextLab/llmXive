# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T014** — The provided `verify_us1.py` defines the correlation logic but the required output file `data/results/us1_verification.json` does not exist, and the truncated `run_verification_and_save` function does not show that results are written in the specified schema. Consequently the task’s core requirement of persisting verification results is unmet.
- **T028** — The provided `run_statistical_test` function is only partially implemented (truncated), never reads `data/results/simulation_summary.csv`, does not write the required JSON output, and the referenced `simulation_summary.csv` and `statistical_test_results.json` files are absent. The task’s full decision‑tree logic and mandatory bootstrap CI handling are not present.
- **T029c** — declared artifact(s) missing/empty/invalid: data/results/simulation_summary.csv
- **T029d** — declared artifact(s) missing/empty/invalid: data/results/simulation_summary.csv
- **T042a** — The required `data/results/simulation_summary.csv` is absent, so the script cannot read any data, and the claimed `docs/paper/bias_vs_beta.png` is only a placeholder text (401 bytes) rather than a real plot image generated from the CSV. Both essential artifacts are missing or invalid.
- **T042b** — The required output artifacts (`docs/paper/coverage_vs_beta.pdf`, `data/results/simulation_summary.csv`, and `docs/paper/coverage_regression.json`) are all absent, so the regression test and figure generation have not been produced. The script exists, but without the data and generated files the task is not fulfilled.
