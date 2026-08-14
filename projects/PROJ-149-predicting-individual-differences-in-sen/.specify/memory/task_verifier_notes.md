# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T010b** — The provided `code/02_preprocess_eeg.py` is incomplete (truncated) and does not show any logic that writes retained `.fif` files or creates `data/interim/exclusion_log.csv`. Moreover, the required `exclusion_log.csv` file is absent from the repository. The task’s output artifacts are therefore missing.
- **T012** — The provided `code/03_extract_features.py` is truncated (ends with an unfinished `parser = argparse.Arg` line) and lacks the required chunked processing, 5‑minute epoch handling, and CSV writing logic. Moreover, the expected output file `data/interim/eeg_psd.csv` does not exist. These missing components mean the task requirements are not met.
- **T013** — declared artifact(s) missing/empty/invalid: data/interim/behavioral_metrics.csv, data/interim/behavioral_exclusion_log.csv
- **T015** — declared artifact(s) missing/empty/invalid: data/interim/eeg_psd.csv, data/interim/behavioral_metrics.csv, data/processed/features.csv
- **T035a** — The required artifact `data/processed/features.csv` is missing, so no schema validation could be performed; thus the task’s requirements are not met.
