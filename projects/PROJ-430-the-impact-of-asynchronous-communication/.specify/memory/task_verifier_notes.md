# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the `projects/PROJ-430-the-impact-of-asynchronous-communication/` directory or its contents is provided; without a directory listing or files, we cannot confirm that the required project structure was created.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, or a `black` config) or setup scripts are present in the provided evidence, so the claim that linting (ruff) and formatting (black) have been configured cannot be verified. The required artifacts are missing.
- **T006** — No directory tree or `.gitignore` file was presented; the response contains only the task description and user scenarios, with no concrete evidence that a `data/` folder with `raw/`, `derived/`, `validation/` subfolders and appropriate ignore rules exists. The required artifact is missing.
- **T010** — declared artifact(s) missing/empty/invalid: code/data_ingestion.py
- **T011** — declared artifact(s) missing/empty/invalid: code/data_ingestion.py
- **T014** — declared artifact(s) missing/empty/invalid: code/data_ingestion.py
- **T015** — No code, script, notebook, or data file was provided that performs the weighted‑mean aggregation of pair‑level response‑time variances into a project‑level metric, as required by task T015. The evidence consists only of the task description; the actual implementation artifact is missing.
- **T015a** — The required file `data/derived/timestamp_features.parquet` does not exist, so the intermediate timestamp-derived features have not been persisted as specified. The task’s core deliverable is missing.
- **T016** — No code, configuration, or documentation showing added error handling for GitHub API rate limits or chunking logic for datasets >100 k events is present. The claim lacks any artifact (e.g., updated ingestion script, tests, or logs) that demonstrates the required OOM‑prevention measures, so the task is not satisfied.
