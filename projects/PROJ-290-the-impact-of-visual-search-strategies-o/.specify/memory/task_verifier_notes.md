# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T012** — The repository lacks the required `data/validation_report.json` file, and the provided `code/data/validate.py` only contains a partial ROI‑fallback function – it does not perform the full checks for `gaze_coordinates`, `response_times`, `emotion_labels`, and `roi_annotations`, nor does it write a JSON report or halt on missing critical variables as specified.
- **T013** — No code, script, or documentation implementing the Generic ROI Fallback (3x3 grid) logic is present; the artifact is missing entirely, so the requirement is not satisfied. The next implementer must add the fallback implementation and provide the corresponding source file or test evidence.
- **T014** — The submission provides no code, script, or documentation showing a participant‑exclusion routine that drops participants with >20 % missing gaze data, nor any log output reporting the exclusion rate. Without these artifacts the requirement cannot be verified.
- **T015** — The submission provides no visible `data/raw/` directory nor any checksum files documenting downloaded datasets; no artifacts were presented to verify that the required structure and checksum records exist. The task therefore remains unfulfilled.
- **T037a** — No evidence was provided that `hash_artifacts.py` was executed, nor that a `state/` directory containing updated hash files exists; the required artifact (the updated hashes) is missing.
- **T019** — declared artifact(s) missing/empty/invalid: data/processed/features.csv
- **T020** — The `classification.py` script defines the ratio calculation and logs a warning, but it never writes the resulting DataFrame to `data/processed/features.csv`, and that CSV file is absent from the repository. Consequently the required artifact (the updated features CSV) is missing.
- **T024b** — declared artifact(s) missing/empty/invalid: data/processed/labels_k2.csv, data/processed/labels_k3.csv
- **T025** — declared artifact(s) missing/empty/invalid: results/sensitivity_report.yaml
- **T026** — declared artifact(s) missing/empty/invalid: results/sensitivity_report.yaml
- **T038** — declared artifact(s) missing/empty/invalid: results/report.md
