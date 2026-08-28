# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T008c** — The `generate_polynomial_test_data` function is only partially defined (truncated) and never creates or saves the required `data/results/test_data_polynomial.npy`. Moreover, the verification script `scripts/hash_artifacts.sh` is absent, so the required checksum check cannot be performed. The task’s critical output file and verification steps are missing.
- **T014a** — The repository lacks the required `data/results/test_data_polynomial.npy` file, and the `src/experiments/baseline_runner.py` source shown does not contain an implementation of the `load_test_data` function (or any code that loads that file). Consequently the task’s core requirement—providing a working `load_test_data` that returns `X_test, y_test` from the specified NumPy file—is not satisfied. The missing data file and absent function must be added for the task to be complete.
- **T049a** — declared artifact(s) missing/empty/invalid: src/experiments/scaling.py
- **T049b** — declared artifact(s) missing/empty/invalid: src/experiments/scaling.py
- **T049c** — declared artifact(s) missing/empty/invalid: src/experiments/scaling.py, data/results/scaling_law.csv
- **T074** — declared artifact(s) missing/empty/invalid: src/utils/cost_curve_generator.py, data/results/cost_curve_data.csv
- **T076** — declared artifact(s) missing/empty/invalid: src/experiments/cost_analyzer.py, data/results/cost_metrics.json
