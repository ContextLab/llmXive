# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory tree or `__init__.py` files were presented as evidence; the required folders (`src`, `data/raw`, `data/processed`, `tests/unit`, `tests/integration`, `docs`) and empty `__init__.py` files are not shown, so the task’s deliverable is missing.
- **T004** — No evidence was provided showing that the `data/raw/`, `data/processed/`, and `data/processed/plots/` directories actually exist, nor that each contains a `.gitkeep` file. Without visible directory listings or file contents, the requirement cannot be confirmed as satisfied.
- **T009** — declared artifact(s) missing/empty/invalid: src/utils/hashing.py
- **T016** — declared artifact(s) missing/empty/invalid: data/processed/cleaned_microbiome_sleep.csv
- **T017** — The required artifact `data/processed/ingestion_report.json` does not exist, so the exclusion counts and proportion are not logged as specified. The task therefore remains unfinished.
- **T037** — The required file `src/models/schemas.py` does not exist, so no Pydantic models (`MicrobiomeSample`, `SleepMetric`, `CorrelationResult`) are defined as required. The artifact is missing, making the task unfinished.
- **T020b** — The required input file `data/processed/cleaned_microbiome_sleep.csv` is absent, and the `src/diversity.py` implementation is truncated (the `calculate_alpha_diversity` function is incomplete), so the alpha‑diversity computation using the rarefied table is not fully provided.
- **T024** — declared artifact(s) missing/empty/invalid: data/processed/correlation_results.csv
- **T029** — The required `src/report.py` file does not exist, so no report or summary table of correlations is present. The task’s core deliverable is missing.
- **T030** — No evidence of any plot files (e.g., PNG, PDF, SVG) existing in the required `data/processed/plots/` directory is provided; the implementer did not supply the saved plot artifacts, so the task requirement is not met.
- **T031** — No HTML or PDF report was provided; the evidence contains only the task description and specifications, with no actual report file, content, or generated output. The required final report with findings and handling of “No significant associations” is missing.
- **T032** — No evidence of a modified `README.md` containing “Usage Examples” and “Data Source” sections, nor any updated files in the `docs/` directory showing a pipeline flow diagram, was provided. The required documentation artifacts are missing, so the task is not satisfied.
- **T033** — No code files, diffs, or commit logs are provided showing that unused imports were removed or that module T014 was refactored to use generator expressions. Without concrete artifacts demonstrating the cleanup and refactoring, the claim cannot be verified. The implementer must supply the updated source code (or a patch/diff) that evidences the changes.
