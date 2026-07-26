# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No directory structure (`data/raw`, `data/processed`, `data/assets`) is shown or referenced in the provided evidence; without visible artifacts, we cannot confirm the required folders were created. The implementer must add the actual directory tree (or a screenshot/listing) to demonstrate they exist.
- **T001b** — No evidence of the required `code`, `artifacts`, or `tests` directories (or their contents) is provided; the claim lacks any tangible artifact confirming their existence. The implementer must create these directories and populate them with appropriate files.
- **T003** — No linting or formatting configuration files (e.g., `.flake8`, `ruff.toml`, `pyproject.toml` with Black settings) or related setup scripts were provided. Without these artifacts, the requirement to configure flake8/ruff and Black cannot be verified as fulfilled.
- **T008** — No `artifacts/logs/` directory with structured log files nor an `artifacts/metrics.json` file is present. The implementer did not provide any code, configuration, or generated output demonstrating that logging has been set up to write to those locations. Consequently, the required logging infrastructure is missing.
- **T009a** — declared artifact(s) missing/empty/invalid: data/raw/reference_substructures_raw.csv
- **T009b** — The required file `data/raw/reference_substructures_raw.csv` does not exist, so no SHA-256 checksum can be computed or compared to the source manifest. The task cannot be considered completed until the file is present and its checksum verified.
- **T009c** — The required artifact `data/assets/reference_substructures.csv` does not exist, so no data ingestion or schema validation could have been performed. The implementer must create the CSV file with the verified data and ensure it conforms to the expected schema.
- **T009d** — declared artifact(s) missing/empty/invalid: data/raw/kinetic_dataset_raw.csv
