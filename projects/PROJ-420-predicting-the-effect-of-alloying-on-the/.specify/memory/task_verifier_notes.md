# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T006b** — declared artifact(s) missing/empty/invalid: results/methodological_flags.json, schema.yaml
- **T006c** — declared artifact(s) missing/empty/invalid: results/residuals.json, schema.yaml
- **T006d** — declared artifact(s) missing/empty/invalid: data/processed/split_indices.json, schema.yaml
- **T006e** — declared artifact(s) missing/empty/invalid: results/collinearity_diagnostic.json, schema.yaml
- **T006f** — declared artifact(s) missing/empty/invalid: results/final_report.json, schema.yaml
- **T006** — The `code/logging_config.py` file is truncated mid-function (ending at `log_path = Path(effective_`), meaning the implementation of the `RotatingFileHandler` with the required `maxBytes=10MB` and `backupCount=5` is missing and the file is syntactically invalid. Additionally, the required log file `data/logs/app.log` does not exist, so the verification step regarding rotation and valid JSON output cannot be performed.
- **T007b** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T009c** — The `code/merge.py` file exists but is truncated and does not show a complete implementation of the required deduplication and conflict‑resolution logic. Moreover, the essential input files `data/raw/mp_alloys.json`, `data/raw/nist_alloys.json`, and the constants module `code/constants.py` are missing, so the script cannot function as specified. The missing data files and constants, plus the incomplete code, must be provided/fixed for the task to be considered complete.
- **T016** — `code/data/clean.py` contains the `log_exclusion` function that writes CSV lines to `data/logs/exclusion_log.txt`, satisfying the code‑side requirement, but the required output file `data/logs/exclusion_log.txt` is missing from the repository. The task demands the artifact (the log file) to exist (and be non‑empty), which is not provided. The implementer must create the file (or demonstrate its creation) to complete the task.
- **T015c** — The `code/data/clean.py` file shown does not contain any logic that writes a Parquet file, checks the row count against 50, calls `sys.exit(1)`, or conditions the write on T015b’s success. Moreover, the expected output file `data/processed/alloys_clean.parquet` is absent from the repository. These missing pieces mean the task’s requirements are not satisfied.
- **T019** — The repository contains `code/data/clean.py`, but the required output file `data/processed/alloys_ilr.parquet` is absent, so the ILR‑transformed data was not saved as specified. Consequently the task’s deliverable is not present.
