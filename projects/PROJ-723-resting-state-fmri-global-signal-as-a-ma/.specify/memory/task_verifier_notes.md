# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T010** — The repository lacks the required `contracts/dataset.schema.yaml` file, and `code/ingestion.py` contains no logic that reads a schema or aborts with “FATAL: Dataset Mismatch” when required columns (e.g., global_signal, global_signal_sd) are absent. The task’s core verification requirement is therefore unmet.
- **T013** — No code, script, or log files implementing the subject‑validation logic are present; the evidence consists only of the task description and project spec. The required artifact—a piece of software that joins fMRI and MWQ data, excludes unmatched subjects, and records exclusion counts—is missing.
- **T014** — No code, script, configuration, or log file was provided that implements the per‑subject mean FD > 0.5 mm exclusion or records the exclusion counts (FR‑008). Without such artifacts, the requirement cannot be verified as satisfied.
- **T015** — No code, script, or test file was presented that adds a zero‑variance (`global_signal_sd == 0`) exclusion check and logs a warning. The provided project description and user stories do not contain the required implementation artifact, so the task is not satisfied.
- **T016** — declared artifact(s) missing/empty/invalid: data/processed/cleaned_data.csv
- **T022** — The provided materials contain only the project specification and user stories; there is no code, script, function, or output that computes the empirical p‑value as the proportion of null MAEs ≤ the observed MAE. Consequently, the required artifact is missing.
- **T023** — declared artifact(s) missing/empty/invalid: data/results/delta_r2.json
- **T024** — The repository contains a partially‑implemented `code/diagnostics.py` (the `run_collinearity_diagnostics` function is cut off and does not show JSON writing or VIF‑threshold warnings). Moreover, the required input file `data/processed/cleaned_data.csv` and the expected output `data/results/diagnostics.json` are absent. The task’s deliverables are therefore not present.
- **T025** — declared artifact(s) missing/empty/invalid: data/results/model_report.json
