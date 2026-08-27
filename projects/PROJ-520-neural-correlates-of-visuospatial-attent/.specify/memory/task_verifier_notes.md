# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T014** — No code, configuration, tests, or documentation were provided that demonstrate a sample‑size validation step (halting <50 epochs/condition, flagging <100 epochs/condition). Without any artifact to inspect, we cannot confirm the requirement was implemented. The task remains unfulfilled.
- **T017** — declared artifact(s) missing/empty/invalid: data/processed/epochs_cleaned.fif
- **T018** — The required input file `data/processed/epochs_cleaned.fif` does not exist, and the provided `code/feature_extraction.py` is truncated (ending mid‑function) with no visible logic that actually invokes the Morlet decomposition on the low‑frequency band. Both the essential data artifact and a complete implementation are missing.
- **T022** — No code, data, or log files were supplied that implement the “feature validation” step or record validation failures as required by US2. Without concrete artifacts (e.g., a validation script, test results, or failure logs), the claim cannot be verified. The implementer must provide the actual validation implementation and accompanying logs.
- **T023** — declared artifact(s) missing/empty/invalid: data/processed/features_matrix.csv
- **T024** — The required file `data/processed/feature_metadata.json` does not exist, so no documentation of electrode collinearity or correlation structure is present. The implementer must create this JSON file with the appropriate metadata.
- **T025** — The required input file `data/processed/features_matrix.csv` does not exist, so the classifier cannot be trained as specified. Although `code/classification.py` contains functions for loading the CSV and performing k‑fold LDA training, the essential data artifact is missing, violating the task requirement.
