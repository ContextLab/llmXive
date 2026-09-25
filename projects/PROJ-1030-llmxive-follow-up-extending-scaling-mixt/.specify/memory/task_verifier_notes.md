# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T017** — The `code/utils/log_memory.py` file exists but is truncated (the `log_memory_usage` function is incomplete) and never writes to the required `data/processed/memory_log.json`. Moreover, the JSON log file itself is missing, so the task’s requirement to record peak RAM usage to that path is not fulfilled.
- **T016** — declared artifact(s) missing/empty/invalid: data/processed/features.npy
- **T017#1** — declared artifact(s) missing/empty/invalid: data/processed/extract.log
- **T024** — declared artifact(s) missing/empty/invalid: data/processed/labels_raw.csv, data/processed/labels.csv, data/processed/excluded_samples.log
- **T036** — declared artifact(s) missing/empty/invalid: code/verify_latent_independence.py
- **T036#1** — declared artifact(s) missing/empty/invalid: code/verify_latent_independence.py, data/processed/latent_audit_report.json
- **T032** — The required output file `data/processed/activation_distribution.json` does not exist, and the provided `compute_baseline.py` script is truncated (ends with `logger.in`) and never actually writes the JSON to the expected location. Consequently the baseline distribution has not been computed and saved as required.
- **T032#1** — No `metrics.json` (or any other file) containing the calculated precision, recall, F1 scores and the required “random guessing” baseline is present. The claim provides only a textual description of the task; without the actual JSON output and evidence that the baseline uses the exact filtered test‑set IDs, the requirement is not satisfied. The implementer must supply a non‑empty `metrics.json` file with the computed metrics and baseline values.
- **T033** — No SHAP or other feature‑importance analysis code, results, or visualizations were provided, nor any comparison against the baseline distribution from T032.1. The claim lacks any artifact (script, notebook, data files, or report) that demonstrates the required analysis, so the task is not satisfied.
- **T035** — declared artifact(s) missing/empty/invalid: data/processed/metrics.json
