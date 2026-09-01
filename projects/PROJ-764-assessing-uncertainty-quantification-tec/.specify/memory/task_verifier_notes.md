# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T009** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T012** — The repository contains `code/models/baseline_nn.py` with a 2‑layer heteroscedastic network, but the file does not include the required pre‑save parameter‑count assertion nor any code that saves a model checkpoint to `results/models/baseline_seed42.pt`. Moreover, the expected model file is absent from the `results/models` directory. The task’s core requirement—producing and saving the validated model artifact—is therefore unmet.
- **T016b** — The repository contains a `code/main.py` file, but its content is truncated and does not show the required global timeout handler, the explicit waiting for T013/T014 completion, or the full pipeline that merges T016a outputs. Moreover, the expected output file `results/uq_predictions_base.csv` is absent. These missing pieces mean the orchestrator does not fulfill the stated requirements.
- **T018** — declared artifact(s) missing/empty/invalid: results/uq_predictions_base.csv
- **T022b** — The repository contains `code/uq/metrics.py` with a `decompose_uncertainty` function, but there is no script or notebook that imports and runs this function to create `results/uq_predictions.csv`. Moreover, both `results/uq_predictions_base.csv` and the required output `results/uq_predictions.csv` are missing, so the specified CSV with the required columns has not been generated. The task’s core requirement—populating the predictions CSV using the decomposition function—is therefore unmet.
- **T023** — No PDF or PNG reliability diagram files are present in the `results/` directory (or any other location). The required visual artifacts for each UQ method are missing, so the task is not satisfied.
- **T024** — declared artifact(s) missing/empty/invalid: results/calibration_report.csv
- **T025a** — The required output file `results/ece_scores_by_seed.json` is missing, so the aggregated ECE scores for the three seed runs have not been provided. Without this artifact, the task is not satisfied.
- **T025b** — declared artifact(s) missing/empty/invalid: results/ece_scores_by_seed.json
- **T025c** — declared artifact(s) missing/empty/invalid: results/significance_test_results.json
