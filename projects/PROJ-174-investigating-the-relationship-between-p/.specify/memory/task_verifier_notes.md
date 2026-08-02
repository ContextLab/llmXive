# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T005** — declared artifact(s) missing/empty/invalid: code/logging_config.py, code/logs/preprocess.log, results/quality_report.csv
- **T002d** — declared artifact(s) missing/empty/invalid: state/test_artifacts.yaml
- **T010** — The required artifact `tests/test_data_loader.py` does not exist on disk, so no unit test for data loader validation is present. The task cannot be considered completed until a non‑empty test file is added at the specified location.
- **T013** — declared artifact(s) missing/empty/invalid: code/preprocessing/load_data.py, config.yaml
- **T016** — The repository contains `code/analysis/correlations.py`, which appears to implement Pearson correlation and Benjamini‑Hochberg correction, but the required output file `results/correlations.csv` is absent, so the script’s primary deliverable is not present. Without the CSV the task’s requirement is not met.
- **T017** — The provided `code/preprocessing/filter.py` contains signal‑processing utilities but no logic that writes exclusion counts to `results/quality_report.csv`, nor does the repository contain the required `results/quality_report.csv` file. Consequently the quality‑report generation task is not fulfilled.
- **T023** — No code, script, or output implementing the likelihood‑ratio test for comparing nested models is present; the only material is the task description and specifications, with no concrete artifact to verify. The required implementation artifact is missing.
- **T024** — declared artifact(s) missing/empty/invalid: config.yaml
- **T025** — declared artifact(s) missing/empty/invalid: results/model_summary.csv
- **T029** — The required files `results/limitations.md` and `results/classification_metrics.csv` are missing, so the limitation note and the status column update cannot be verified. Consequently the ground‑truth labeling changes and removal of predictive‑validity claims are not demonstrated.
- **T031** — declared artifact(s) missing/empty/invalid: results/sensitivity_analysis.csv
- **T032** — No artifact (e.g., plot, CSV, or script) showing the continuous correlation between predicted probability and search time is present; the only material is the task description, which does not satisfy the requirement for a concrete output. The implementer must provide the actual correlation output (e.g., a figure or data file).
- **T035a** — declared artifact(s) missing/empty/invalid: scripts/profile_memory.py, results/memory_profile.csv
