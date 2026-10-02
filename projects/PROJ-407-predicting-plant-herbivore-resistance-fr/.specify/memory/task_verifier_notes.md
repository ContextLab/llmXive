# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T010** — The provided `code/ingest.py` is truncated, never reaches the part that would stream the HuggingFace dataset, accumulate it into a DataFrame, or write `data/raw/raw_dataset.csv` atomically; it also lacks the required `RuntimeError` with the exact message. Moreover, the expected output file `data/raw/raw_dataset.csv` is missing.
- **T014** — declared artifact(s) missing/empty/invalid: data/raw/raw_dataset.csv, data/raw/raw_dataset.csv.sha256
- **T013** — The `metadata.json` lacks the required `"mapping"` entry, and the expected `data/interim/harmonized.csv` file is absent. Moreover, `code/ingest.py` is truncated (syntax error) and does not contain logic to perform the categorical‑to‑ordinal conversion or to write the mapping to the metadata file. These core requirements are unmet.
- **T015** — declared artifact(s) missing/empty/invalid: data/interim/harmonized.csv
- **T020** — The `apply_pca_if_needed` function does not implement the variance‑explained retention rule, never writes the PCA matrix to `data/processed/pca_reduced.csv`, and the required CSV file is absent. The implementation therefore does not meet the task’s output and behavior specifications.
- **T021** — The required `data/interim/split_log.txt` file is missing, and the provided `code/preprocess.py` excerpt does not show any implementation of a genotype‑stratified `GroupShuffleSplit` nor the code that writes the split indices and logs the ratio/counts. Without the log file and visible split logic, the task’s requirements are not fully satisfied.
- **T023** — The `code/model.py` only defines an `evaluate_model` function that computes R² and MSE and never writes any results to `data/processed/model_metrics.json`; it also lacks any accuracy calculation for classification tasks. Moreover, the required `data/processed/model_metrics.json` file is missing.
- **T029b** — declared artifact(s) missing/empty/invalid: data/interim/batch_corrected_data.csv
