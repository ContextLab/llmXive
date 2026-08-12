# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T009** — No configuration files, scripts, or documentation for managing ENCODE API keys and local paths are present in the provided evidence; therefore the required environment configuration management artifact is missing.
- **T015** — The `code/data/save_dataset.py` script is present but appears truncated and does not show the complete logic to load the intermediate CSV and write the Parquet file, and the required output file `data/processed/unified_ctcf_dataset.parquet` is missing. The task is not satisfied until the script fully implements the save operation and the Parquet file exists and is non‑empty.
- **T016** — No code, test, or documentation artifact was presented showing that a validation step was added to ensure each row contains a fixed‑length sequence and matching chromatin values, nor that an error is raised when nulls remain. The required implementation and its verification are missing.
- **T017** — No code, configuration, or log output showing that logging for data ingestion (including cell type counts and exclusion reasons) was added. The claim lacks any concrete artifact (e.g., updated ingestion script, logging statements, sample log files) to verify the requirement.
- **T019** — declared artifact(s) missing/empty/invalid: tests/integration/test_training_loop.py
- **T021** — The `code/models/train.py` file is present but ends abruptly (truncated code, missing the training loop, loss computation, and any handling of majority/minority class ratios). Moreover, the required dataset `data/processed/unified_ctcf_dataset.parquet` does not exist on disk. Both the script implementation and the input data are missing, so the task is not genuinely completed.
- **T024** — declared artifact(s) missing/empty/invalid: data/models/best_ctcf_predictor.pth
- **T025** — No code, data, or result files were presented that demonstrate a synthetic DNA sequence with a strong CTCF motif and low ATAC‑seq signal being run through the trained model, nor any reported probability showing it is ≤ 0.2. The required test artifact is missing, so the task is not satisfied.
- **T030** — declared artifact(s) missing/empty/invalid: code/interpret/validate_features.py
