# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of a `projects/PROJ-008-psychology-research/` directory or any of its required sub‑folders/files is provided. The implementer did not supply the project structure, so the task’s core deliverable is missing.
- **T003** — The implementer provided no linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, or `black` settings) nor any documentation showing that `ruff` and `black` have been set up and integrated into the project. Consequently, the required artifact for task T003 is missing.
- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T011** — The required file `tests/contract/test_cleaned_study_schema.py` does not exist in the repository, so the contract test for the data extraction schema is missing. The task cannot be considered completed until this test file is created and contains the appropriate test logic.
- **T019** — declared artifact(s) missing/empty/invalid: data/processed/cleaned_studies.csv, data/raw/excluded_studies.log
- **T029** — No code, configuration, or documentation was provided that shows the required conditional logic (suppressing subgroup/meta‑regression when total N < 10 and falling back to a descriptive synthesis). Without any artifact to inspect, we cannot confirm the feature was implemented. The missing deliverable is the implementation (e.g., function, script, or module) and evidence (tests or logs) demonstrating the N‑threshold behavior.
