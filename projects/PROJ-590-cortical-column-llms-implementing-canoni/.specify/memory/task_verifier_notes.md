# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T008c** — declared artifact(s) missing/empty/invalid: src/training/homeostasis.py
- **T012b** — The integration test file exists, but it writes logs to a temporary directory and only asserts the temporary `gradient_norms.json` was created. The required repository file `data/logs/gradient_norms.json` is missing, so the task of populating that path is not satisfied.
- **T012c** — The repository contains a `tests/integration/test_microcircuit_training.py` file, but its contents are truncated (e.g., the training configuration ends abruptly at `log_interv`) and there is no evidence that it actually runs the model with `log_gradient_norms` enabled. Moreover, the required output file `data/logs/gradient_norms_microcircuit.json` is missing. The integration test does not demonstrably produce the gradient‑norms JSON needed for SC‑002 verification.
- **T015** — declared artifact(s) missing/empty/invalid: src/experiments/baseline_runner.py
- **T016** — The provided `tests/integration/test_baseline_validation.py` is truncated and does not show the required assertions (e.g., checking that `baseline_metrics.json` exists, contains the keys `train_mae`, `test_mae`, `degradation_pct`, and that degradation is computed correctly with zero‑division handling). Moreover, the expected `data/results/baseline_metrics.json` file is absent. The implementer must supply the full test implementation with the specified checks and ensure the test creates/validates the JSON file.
- **T020** — declared artifact(s) missing/empty/invalid: src/models/hybrid_network.py
- **T026a** — declared artifact(s) missing/empty/invalid: src/experiments/ablation.py, data/configs/ablation_configs.json
- **T026b** — declared artifact(s) missing/empty/invalid: src/experiments/ablation.py, data/results/ablation_results.json
- **T027** — declared artifact(s) missing/empty/invalid: src/experiments/scaling.py
