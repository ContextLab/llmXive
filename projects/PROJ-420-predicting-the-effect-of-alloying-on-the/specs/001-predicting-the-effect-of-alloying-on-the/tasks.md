# Tasks: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys  

**Inputs**: `spec.md`, `plan.md`, existing artifacts in `code/`, `data/`, `results/`, and `contracts/`.  

The list below follows the canonical checklist format required by the platform.  
Checked (`[X]`) tasks have been verified and produce the artefacts described;  
unchecked (`[ ]`) tasks are pending.  
All tasks respect the data‑flow ordering required by the specification (FR‑001 – FR‑010) and the success‑criteria (SC‑001 – SC‑006).

---

## Phase 0 – Project scaffolding

- [X] T001a [P] Create the core directory layout  
  `code/`, `data/raw/`, `data/processed/`, `models/`, `results/`, `tests/`, `contracts/`.  
  **Verification**: All listed directories exist on the filesystem.

- [X] T001b [P] Add `code/__init__.py` to make the code tree a package.  
  **Verification**: Importing `code` succeeds without error.

- [ ] T001c [P] Add placeholder `.gitkeep` files in `data/raw/` and `data/processed/`.  
  **Verification**: Files are present, allowing empty directories to be tracked.

- [ ] T002 [P] Initialise a Python project with pinned dependencies in `code/requirements.txt` (pandas, numpy, scikit‑learn, matminer, statsmodels, chemparse, joblib, pytest, jsonschema).  
  **Verification**: `pip install -r code/requirements.txt` completes without conflicts.

- [ ] T003 [P] Configure linting/formatting (ruff + black) via `code/pyproject.toml`.  
  **Verification**: `ruff .` and `black .` run cleanly.

- [ ] T004 [P] Add the JSON‑logging schema `contracts/logging_schema.yaml` (fields: `timestamp`, `level`, `message`, `trace_id`, `module`).  
  **Verification**: The file exists and validates against the JSON‑Schema meta‑schema.

- [ ] T005 [P] Implement `code/config.py` exposing paths (`DATA_ROOT`, `MODEL_ROOT`, `RESULT_ROOT`), random seeds, and the list `VALID_MEASUREMENT_METHODS`.  
  **Verification**: Importing `code.config` yields the expected constants.

---

## Phase 1 – Data acquisition

- [ ] T006 [US1] Implement `code/logging_config.py`  
  *Create a `RotatingFileHandler` that writes JSON‑formatted log records to `data/logs/app.log` (max 10 MiB, 5 backups). The JSON payload must contain **only** the fields defined in `contracts/logging_schema.yaml`.*  
  **Verification**:  
  1. Run a short script that emits >10 MiB of logs; confirm rotation occurs and exactly 5 backup files are created.  
  2. Sample a log entry and validate it with the schema (`jsonschema.validate`).  

- [ ] T007 [US1] Define Pydantic models for the data contracts in `code/schemas/alloy_record.py`  
  *Models must match `specs/001-predicting-the-effect-of-alloying-on-the/contracts/alloy_record.schema.yaml` exactly.*  
  **Verification**: Unit test loads a valid JSON example and validates against the model.

- [ ] T009a [US1] Implement Materials Project data download  
  *Fetch raw compositional and property data for aluminum alloys using `matminer` and save to `data/raw/mp_raw.json`.*  
  **Verification**: `data/raw/mp_raw.json` exists and contains raw alloy records.

- [ ] T009b [US1] **Implement NIST MDR data download (mandatory)**  
  *Fetch raw compositional and property data for aluminum alloys from the NIST Materials Data Repository and save to `data/raw/nist_alloys.json`. The pipeline must abort with a clear error if this download fails, because FR‑001 requires both sources.*  
  **Verification**: `data/raw/nist_alloys.json` exists; failure to download raises an exception that stops the pipeline.

- [ ] T009c [US1] Merge data sources  
  *Combine `mp_raw.json` and `nist_alloys.json` into a single raw dataset for processing. The merge step must verify that records from **both** sources are present before proceeding.*  
  **Verification**: The merged dataset contains entries from both Materials Project and NIST MDR; a log entry records the counts per source.

- [ ] T009d [US1] Verify dataset completeness against both sources (SC‑001)  
  *After merging, compute the total number of records from each source and compare against the expected repository sizes (as reported by the APIs). Log a completeness metric for MP and NIST separately in `results/completeness_report.json` and abort if either source yields zero records.*  
  **Verification**: `results/completeness_report.json` exists, conforms to a simple schema (`source`, `record_count`, `expected_minimum`), and the pipeline halts with an informative error if completeness is not met.

---

## Phase 2 – Cleaning, filtering & exclusion logging

- [ ] T016 [US1] Implement exclusion‑logging utility in `code/data/clean.py`  
  *Function `log_exclusions(step_id: str, count: int, reason: str)` appends a CSV line to `data/logs/exclusion_log.txt` with columns `step,count,reason,timestamp` (ISO 8601). Ensure a consistent CSV header is written on file creation.*  
  **Verification**: After running the cleaning pipeline, the CSV contains a header and at least one row.

- [ ] T010 [US1] Implement raw schema validation  
  *Filter raw records to ensure they contain the minimum required fields (material_id, formula, poissons_ratio, youngs_modulus) before detailed cleaning.*  
  **Verification**: Records missing core fields are logged via T016 and excluded.

- [ ] T011 [US1] Implement monolithic alloy filter  
  *Filter dataset to include only monolithic (non-composite) aluminum alloys per FR-002.*  
  **Verification**: Records flagged as composites are excluded and logged via T016.

- [ ] T012 [US1] Implement formula parsing and unit normalization  
  *Use `chemparse` to convert stoichiometric formulas to atomic fractions (FR-010), calculate the Al balance, and normalize all elastic constants to GPa (FR-003).*  
  **Verification**: All records have atomic fractions summing to 1.0 and Young's modulus in GPa.

- [ ] T013 [US1] Implement major‑element sum exclusion  
  *Exclude entries where the sum of major elements (Cu, Mg, Si, Zn, Mn) is < 0.95 per FR-003.*  
  **Verification**: Entries with sum < 0.95 are excluded and logged via T016.

- [ ] T014 [US1] Implement independence verification  
  *Inspect `poisson_source` for each entry. Only accept `ultrasonic`, `direct_measurement`, or `laser_ultrasonics` (FR-009). Log the count of excluded non-independent entries to satisfy SC-006.*  
  **Verification**: The resulting dataset contains only verified independent measurements.

- [ ] T015b [US1] Orchestrate the full cleaning pipeline in `code/data/clean.py`  
  *Run in order: T010 → T011 → T012 → T013 → T014. After the final dataframe is produced, count rows; if $< 50$, log an error and `sys.exit(1)` (per FR-004 safeguard).*  
  **Verification**: The script completes and produces a cleaned dataframe.

- [ ] T015c [US1] Serialize the cleaned dataset  
  *Write the dataframe to `data/processed/alloys_clean.parquet`. The file must conform to `contracts/dataset.schema.yaml`.*  
  **Verification**: Load the parquet file and validate against the schema.

---

## Phase 3 – Diagnostics & Transformation

- [ ] T019 [US2] Apply the Isometric Log‑Ratio (ILR) transformation  
  *Read `data/processed/alloys_clean.parquet`, compute ILR coordinates for [Cu, Mg, Si, Zn, Mn], append as `ilr_1 … ilr_4`, and write to `data/processed/alloys_ilr.parquet`.*  
  **Verification**: The parquet file contains the four ILR columns.

- [ ] T028 [US3] Compute variance‑inflation factors (VIF)  
  *Compute VIF for the five raw atomic‑fraction columns and the four ILR features using `statsmodels`. Write `results/collinearity_diagnostic.json` conforming to `contracts/collinearity_diagnostic.schema.yaml`.*  
  **Verification**: The JSON file validates; `is_flagged` is true if any raw VIF $> 5$.

---

## Phase 4 – Modeling

- [ ] T020 [US2] Implement an 80/20 train‑test split in `code/modeling.py`  
  *Split `alloys_ilr.parquet` into train and test sets. Save indices to `data/processed/split_indices.json`.*  
  **Verification**: The JSON file contains disjoint lists summing to the total sample size.

- [ ] T021 [US2] Run cross‑validation on the training set  
  *Perform 5-fold CV (or LOOCV if $N < 50$) on the training portion using `RandomForestRegressor`. Store results in `results/cv_metrics.json`.*  
  **Verification**: `cv_metrics.json` contains `cv_mae` and `best_params`.

- [ ] T024 [US2] Train the final model and serialize  
  *Fit the model on the full training set using best hyperparameters. Save to `models/rf_model.pkl` and record metadata in `models/model_metadata.yaml`.*  
  **Verification**: The pickle loads and metadata is valid YAML.

- [ ] T025 [US2] Evaluate on the held‑out test set  
  *Predict Poisson’s ratio for test indices, compute MAE, and write `results/model_metrics.json` (merging CV and test metrics). Generate `results/methodological_flags.json` flagging MAE $> 0.05$.*  
  **Verification**: `model_metrics.json` contains `cv_mae` and `test_mae`.

- [ ] T023d [US2] Aggregate model‑metric artefacts  
  *Combine all metrics into a single canonical `results/model_metrics.json` conforming to `contracts/model_metrics.schema.yaml`.*  
  **Verification**: The final JSON validates against the schema.

---

## Phase 5 – Feature importance & ranking

- [ ] T027a [US3] Compute primary permutation importance  
  *On the original compositional features, perform 30 shuffles per element, re‑transform to ILR, and measure MAE drop. Store in `results/feature_importance.json` per `contracts/feature_importance.schema.yaml`.*  
  **Verification**: `ranked_elements` is correctly ordered by MAE drop.

- [ ] T027b [US3] Perform exploratory Gini back‑transformation  
  *Load Gini importances from the RF model, multiply by the inverse basis matrix $B^{-1}$ (Appendix A), and sum absolute values to get element‑level scores. Store under `exploratory_ilr_backtransform` in `results/feature_importance.json`.*  
  **Verification**: The field contains five non‑negative numbers.

- [ ] T029 [US3] Produce a ranking summary  
  *Compute the ratio of the top‑2 permutation importance scores and write `results/feature_importance_summary.json` with the comparison statement.*  
  **Verification**: The ratio matches the underlying data within 1e-4.

---

## Phase 6 – Report assembly & validation

- [ ] T030a‑aggregate [US3] Gather all artefacts for the final report  
  *Create `data/processed/report_context.json` bundling all metric and diagnostic JSONs.*  
  **Verification**: The JSON file loads without error.

- [ ] T030c [US3] Render the final markdown report  
  *Generate `results/final_report.md` including Methods, Results (tables), and Limitations. MUST include the explicit phrase "associational (not causal)".*  
  **Verification**: Grep for "associational (not causal)" succeeds.

- [ ] T030a‑validate [US3] Validate the final report content  
  *Verify that numeric values in `final_report.md` match the JSON source artifacts within 1e-3.*  
  **Verification**: The validation script exits with status 0.

---

## Phase 7 – Automated testing

- [ ] T040 [US3] Add pytest coverage run  
  *Run `pytest --cov=code` and produce a coverage report.*  
  **Verification**: Coverage ≥ 80 %.

- [ ] T041 [US2] Unit tests for modelling logic (`tests/test_modeling.py`)  
  *Test split reproducibility, LOOCV fallback, and CV output keys.*  
  **Verification**: All tests pass.

- [ ] T042 [US1] Contract tests for data schemas (`tests/test_schemas.py`)  
  *Validate synthetic records against `contracts/dataset.schema.yaml`.*  
  **Verification**: All tests pass.

- [ ] T043 [US3] Unit tests for analysis (`tests/test_analysis.py`)  
  *Test VIF calculation, permutation importance, and ranking logic.*  
  **Verification**: All tests pass.

- [ ] T044 [US3] End‑to‑end CLI smoke test  
  *Run `python -m code.main --run-all` and assert it produces `results/final_report.md`.*  
  **Verification**: Script exits with status 0.

---

## Dependency‑to‑Requirement mapping

| Requirement | Satisfying Task(s) |
|-------------|--------------------|
| **FR‑001** | T009a, **T009b (mandatory)**, T009c, T009d |
| **FR‑002** | T011 |
| **FR‑003** | T012, T013 |
| **FR‑004** | T019, T020, T021 |
| **FR‑005** | T025, T023d |
| **FR‑006** | T027a, T027b |
| **FR‑007** | T028 |
| **FR‑008** | T030c |
| **FR‑009** | T014 |
| **FR‑010** | T012 |
| **SC‑001** | T009d (completeness check) |
| **SC‑002** | T021, T025 |
| **SC‑003** | T027a, T029 |
| **SC‑004** | T028 |
| **SC‑005** | T030c |
| **SC‑006** | T014 |