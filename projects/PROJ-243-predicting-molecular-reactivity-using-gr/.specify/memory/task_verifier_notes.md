# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of a `data/raw` directory being present or created is provided; the response contains only task description and specifications without any filesystem artifact. The required directory is missing, so the task is not satisfied.
- **T001b** — No evidence of a `data/processed` directory (or any files within it) is provided; the claim cannot be verified without the actual artifact present. The required data directory is missing from the supplied artifacts.
- **T001c** — No evidence was provided showing that a `data/assets` directory exists (or contains any files). Without a visible directory or confirmation of its creation, the requirement cannot be verified as satisfied. The implementer must add the `data/assets` folder (and optionally populate it) and provide proof of its presence.
- **T002** — No evidence was presented showing that the required directories (`code`, `artifacts`, `tests`) actually exist or contain any files; without such artifacts the task requirement is not satisfied.
- **T004** — No linting or formatting configuration files (e.g., `.flake8`, `ruff.toml`, `pyproject.toml` with Black settings) or related setup scripts are present in the provided evidence, so the requirement to configure flake8/ruff and Black has not been satisfied.
- **T009** — No evidence of a logging infrastructure was presented: there are no files or code shown under `artifacts/logs/` nor a `artifacts/metrics.json`, and no description of how structured logs are written. The required artifacts are missing, so the task is not satisfied.
- **T010a** — The required artifact `data/raw/source_ref_table2.csv` does not exist, so the source table was not fetched as specified. The task’s deliverable is missing.
- **T010a#1** — declared artifact(s) missing/empty/invalid: data/raw/reference_substructures_raw.csv, data/raw/source_ref_table2.csv
- **T010b** — The required files `data/raw/reference_substructures_raw.csv` and `data/raw/checksums.json` are both missing, so no checksum verification could be performed. The task’s core requirement is therefore unmet.
- **T010d** — declared artifact(s) missing/empty/invalid: data/raw/source_kinetic_table3.csv
- **T010d#1** — declared artifact(s) missing/empty/invalid: data/raw/kinetic_dataset_raw.csv, data/raw/source_kinetic_table3.csv
- **T010e** — The required files `data/raw/kinetic_dataset_raw.csv` and `data/raw/checksums.json` are missing, so no checksum verification could be performed. The task’s core artifact does not exist, making the claim unfulfilled.
