# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T026c** — declared artifact(s) missing/empty/invalid: data/artifacts/resource_monitor.log
- **T023** — The required artifact `data/artifacts/trained_models.pkl` does not exist, and `code/04_evaluation.py` does not compute RMSE, MAE, or R² (it only computes absolute errors and a paired t‑test). Both the data dependency and the specified evaluation metrics are missing.
- **T024** — The required artifact `data/artifacts/trained_models.pkl` does not exist, causing `load_models()` to raise a FileNotFoundError. Moreover, while `code/04_evaluation.py` defines a `perform_paired_ttest` function, it never actually reads the model, computes absolute errors from it, or invokes the test, so the paired‑t‑test implementation is not operational. The task’s requirement is therefore unmet.
- **T025** — declared artifact(s) missing/empty/invalid: data/artifacts/training_report.json
- **T025b** — declared artifact(s) missing/empty/invalid: data/artifacts/evaluation_metrics.json, data/artifacts/r2_gate_decision.json
- **T029** — The required model artifact `data/artifacts/trained_models.pkl` does not exist, and the `compute_shap_values` function in `code/04_evaluation.py` is incomplete (truncated) and never reaches the SHAP computation or output step. Both the input dependency and the SHAP implementation are therefore missing.
- **T030** — declared artifact(s) missing/empty/invalid: data/artifacts/shap_analysis.png
- **T031** — The required artifact `data/artifacts/shap_ranking.json` is missing, so no ranking of interaction terms has been produced or stored. The task’s deliverable is absent.
- **T033** — No code, data file, notebook, or result output was provided that reads the sensitivity‑analysis results and computes the Jaccard similarity of the top‑5 term sets across thresholds. The required artifact (e.g., a script/notebook and its computed similarity values) is missing, so the task is not satisfied.
