# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T010** — The repository lacks the required `contracts/dataset.schema.yaml` file, and `code/ingestion.py` contains no logic that reads a schema or aborts with “FATAL: Dataset Mismatch” when required columns are absent. The task’s core requirement—schema‑based verification and fatal exit—is therefore not satisfied.
- **T013** — No code, script, or log files implementing the subject‑validation logic are present; the evidence consists only of the task description and project spec. The required artifact—a piece of software that joins fMRI and MWQ data, excludes unmatched subjects, and records exclusion counts—is missing.
- **T014** — No code, script, configuration, or log file was provided that implements the per‑subject mean FD > 0.5 mm exclusion or records the exclusion counts (FR‑008). Without such artifacts, the requirement cannot be verified as satisfied.
- **T015** — No code, script, or test file was presented that adds a zero‑variance (`global_signal_sd == 0`) exclusion check and logs a warning. The provided project description and user stories do not contain the required implementation artifact, so the task is not satisfied.
- **T022** — The provided materials contain only the project specification and user stories; there is no code, script, function, or output that computes the empirical p‑value as the proportion of null MAEs ≤ the observed MAE. Consequently, the required artifact is missing.
- **T025** — declared artifact(s) missing/empty/invalid: data/results/model_report.json
