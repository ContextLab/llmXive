# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No directory tree or file listing was provided; the implementer did not supply any artifact showing that a project directory structure was created. The required folder hierarchy is missing, so the task is not satisfied.
- **T001b** — No actual project files (e.g., README, directory layout, ingestion scripts, or any code/data) were presented; the claim provides only the specification text. Without concrete artifacts on disk, the requirement to “Create initial project files” is not satisfied. The next implementer must add the expected files (e.g., a project root with README, `requirements.txt`, initial Python/R scripts, and placeholder data directories).
- **T007** — declared artifact(s) missing/empty/invalid: src/preprocessing/id_generator.py
- **T008** — No evidence of the required directories (`data/raw/`, `data/processed/`, `data/processed/results/`) being created is provided; the response contains only task description and no filesystem artifacts. The implementer must create and show the actual directory structure.
- **T012** — declared artifact(s) missing/empty/invalid: src/ingestion/agp_loader.py
- **T013** — declared artifact(s) missing/empty/invalid: src/ingestion/ukbb_loader.py
- **T014** — declared artifact(s) missing/empty/invalid: src/ingestion/harmonizer.py
- **T015** — No PII scan report, no artifact checksum file, and no generated deliverables (e.g., unified dataset, analysis tables, or reports) are present. The implementer provided only the task description without any actual output artifacts, so the requirement is not satisfied.
- **T020b** — No pseudocount documentation artifact was supplied; there is no file, text, or other output present that describes the pseudocount methodology, its rationale, or usage. Consequently the required deliverable is missing.
- **T021** — declared artifact(s) missing/empty/invalid: src/analysis/correlation_maaslin2.py
- **T022** — No artifact (e.g., a CSV/TSV report containing the association results with raw p‑values and Benjamini‑Hochberg adjusted q‑values) was provided; the claim contains only the task description and no actual output file or code. The required FDR correction report is missing.
- **T026** — declared artifact(s) missing/empty/invalid: tests/contract/test_diff_abundance_schema.py
- **T027** — The required artifact `tests/integration/test_validation.py` does not exist in the repository, so no integration test for cross‑cohort validation is present. The task cannot be considered completed until this file is added with appropriate test code.
- **T029** — declared artifact(s) missing/empty/invalid: src/analysis/validation_cross_cohort.py
- **T030** — No code, data files, or result artifacts (e.g., the unified CSV, CLR‑transformed matrix, association table, or cross‑cohort replication rate report) were provided; therefore the required calculation of the cross‑cohort replication rate cannot be verified. The implementer must supply the actual analysis scripts and the generated output demonstrating the replication rate.
