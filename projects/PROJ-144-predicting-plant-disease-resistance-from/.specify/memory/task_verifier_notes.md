# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T012** — The required output file `data/raw/study_manifest.json` does not exist, so the script was not shown to have been executed and no study IDs or metadata were produced. The task therefore fails the “file exists with valid JSON” verification.
- **T001a** — No directory listing or file tree was provided showing the required folders (`code/`, `data/raw`, `data/processed`, `data/intermediate`, `tests/`, `state/`, `results/`, `results/plots`, `contracts/`). Without concrete evidence that these directories exist, the task requirement is not satisfied.
- **T001b** — No `ls -R` output or any other evidence was provided to show that the directories created in T001a exist and are writable; the required verification artifact is missing.
- **T003** — declared artifact(s) missing/empty/invalid: pre-commit-config.yaml
- **T006a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T006b** — The required `contracts/metadata.schema.yaml` file is missing, and no validation output (e.g., jsonschema or yamllint results) is provided, so the task’s core requirement is not satisfied.
- **T007a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T007b** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T017** — The required output files `data/processed/batch_corrected_matrix.csv` and `data/processed/labels.csv` are absent, and the hashes recorded in `state/artifact_hashes.yaml` correspond to empty or dummy values (e.g., SHA256 of an empty string). Consequently the preprocessing step was never successfully executed, violating the task’s requirement.
- **T022** — declared artifact(s) missing/empty/invalid: data/intermediate/vif_scores.json
- **T024** — declared artifact(s) missing/empty/invalid: results/metrics.json, results/shap_analysis.json, data/intermediate/vif_scores.json
