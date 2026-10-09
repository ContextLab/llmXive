# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T000** — The spec.md file does not contain a “# Verified datasets” block with URLs and SHA‑256 checksums, and there is no evidence that any public developer productivity dataset was located, its URL tested, or its variables validated. Consequently the prerequisite FR‑001 is not satisfied.
- **T049** — The file `code/validate/citations.py` exists, but its implementation is broken: it calls `download_dataset` (imported from `dataset_search`) expecting a file path, yet `download_dataset` returns a boolean and requires a `Path` object, causing runtime errors; similarly `check_csv_variables` is invoked with the wrong signature. Because the agent cannot actually verify citations as required, the task is not genuinely completed.
- **T051** — declared artifact(s) missing/empty/invalid: data/output/citation_validation.json
- **T001b** — The evidence shows that `data/` exists and contains an `output/` subdirectory, but the required `data/raw/` and `data/processed/` subdirectories are reported as MISSING. These directories must be present for the task to be considered complete.
- **T004** — declared artifact(s) missing/empty/invalid: specs/001-code-generation-performance-outcomes/contracts/dataset.schema.yaml
- **T007** — declared artifact(s) missing/empty/invalid: artifacts.yaml, state/projects/PROJ-462-evaluating-the-impact-of-code-generation/artifacts.yaml
- **T008b** — declared artifact(s) missing/empty/invalid: code/analysis/experience.py
- **T017** — declared artifact(s) missing/empty/invalid: data/raw/sample_developer_productivity.csv
