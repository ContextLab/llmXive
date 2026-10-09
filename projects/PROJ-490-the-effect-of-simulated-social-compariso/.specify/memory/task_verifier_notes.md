# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001b** — Checked the `requirements.txt` file (present and includes flake8, pylint, black). No `README.md` was found, nor any linting/formatting configuration files (e.g., `.flake8`, `.pylintrc`, `pyproject.toml`), so the task’s requirement to configure the tools and provide a README is not satisfied.
- **T002a** — The collector reports `dataset.schema.yaml` as MISSING at the requested path, and although a file with that name appears in the `contracts/` directory listing, no content evidence was supplied to verify it contains the required field definitions (participant_id, pre/post_self_esteem, comparison_tendency, avatar_condition with enum [0,1]) or the N ≥ 100 validation rule (FR-001). The next implementer must ensure the schema file exists at `projects/PROJ-490-the-effect-of-simulated-social-compariso/contracts/dataset.schema.yaml` with the full explicit definitions and sample-size validation rule, a
- **T002b** — The collector reports the requested `output.schema.yaml` as MISSING at its expected location, and while a file of that name appears in the `contracts/` directory listing, no content was collected for it, so I cannot verify it contains the required schema (object with required `imputed_data_checksum` and `missingness_report`, with `total_rows`/`rows_excluded`/`missingness_pct` properties). The implementer must ensure the file exists at `projects/PROJ-490-the-effect-of-simulated-social-compariso/contracts/output.schema.yaml` with exactly the specified definitions and provide its content as evide
- **T002c** — The file `results.schema.yaml` does exist inside `projects/PROJ-490-the-effect-of-simulated-social-compariso/contracts/` (per the directory listing), but no content was collected for it, so I cannot verify it contains the required schema (object with required `coefficients`/`assumptions`/`data_source_type`, the coefficient item fields `name`/`estimate`/`std_err`/`p_value`, the assumption fields `shapiro_p`/`breusch_pagan_p`/`vif_max`, and the `["real","synthetic"]` enum). The next implementer should re-run evidence collection (or provide the file's contents) so the schema can be checked agains
- **T013a** — declared artifact(s) missing/empty/invalid: data/processed/pre_imputation_validation.json
- **T014a_new** — declared artifact(s) missing/empty/invalid: data/processed/pre_imputation_validation.json
- **T013b** — declared artifact(s) missing/empty/invalid: data/processed/imputed_data.csv, data/processed/post_imputation_validation.json
- **T017** — declared artifact(s) missing/empty/invalid: data/processed/imputed_data.csv
- **T018a** — declared artifact(s) missing/empty/invalid: tests/unit/test_regression.py
- **T021** — declared artifact(s) missing/empty/invalid: data/processed/regression_coefficients.csv, data/processed/model_diagnostics.json
- **T030** — declared artifact(s) missing/empty/invalid: data/processed/final_report.json
- **T030a** — declared artifact(s) missing/empty/invalid: data/processed/final_report.json
- **T034** — declared artifact(s) missing/empty/invalid: state/reproducibility_check.yaml
- **T065** — declared artifact(s) missing/empty/invalid: tests/unit/test_data_fetch.py
- **T079** — declared artifact(s) missing/empty/invalid: tests/unit/test_data_fetch.py
