# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T013** — The required `data/selected_dataset_id.txt` file is absent, so the script cannot obtain the dataset ID. Moreover, the provided `code/download.py` is truncated and shows no concrete implementation of downloading files to `data/raw/` or computing a SHA‑256 checksum. Both the essential input file and the core functionality are missing.
- **T015b** — The required `data/processed/ica_components.csv` file does not exist, and the `perform_ica_and_remove_artifacts` function in `code/preprocess.py` is truncated/incomplete, lacking the logic to compute kurtosis, spectral peaks, and write the CSV. The task’s core output is therefore missing.
- **T023** — No filtered epoch files were provided in `data/processed/band_filtered/`, nor any power spectral density plots or quantitative verification showing peaks in the theta (4–7 Hz) and gamma (30–45 Hz) bands as required. The claim lacks the concrete output artifacts and verification data needed to confirm the task was completed.
- **T025** — declared artifact(s) missing/empty/invalid: data/metrics/synchrony_metrics.csv
- **T026** — The repository lacks the required `data/metrics/synchrony_timing.json` file, and the provided `code/synchrony.py` does not contain a timing wrapper that logs durations to that JSON or raises an exception for runs exceeding 30 minutes. The task’s core functionality is therefore missing.
