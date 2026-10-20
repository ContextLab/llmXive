# Tasks: Predicting Corrosion Potential from Composition and Environment

**Inputs**: `spec.md`, `plan.md`, existing code and data‑model artifacts, and reviewer feedback.  
All tasks are written as checklist items; checked boxes indicate completed work that already satisfies the verification criteria. Unchecked boxes are pending implementation or re‑work.

---

## Phase 1 – Project setup & core utilities  

- [ ] T001 Create the required project directory hierarchy (`code/`, `data/`, `data/raw/`, `data/processed/`, `data/logs/`, `results/`) and produce a verification manifest.  
  **File path**: `code/utils/setup_dirs.py` → generates `state/setup_dirs_verified.json`.  
  **Verification**: Running `python -m code.utils.setup_dirs` exits with status 0, creates all directories, and writes a JSON array where each entry contains `"path"` (absolute) and `"created_at"` (ISO‑8601 timestamp).  

- [ ] T002 Implement custom exception classes `DataInsufficientError` and `SchemaMismatchError`.  
  **File path**: `code/utils/exceptions.py`.  
  **Verification**: Importing the module (`from code.utils.exceptions import DataInsufficientError, SchemaMismatchError`) succeeds; unit tests in `tests/unit/test_exceptions.py` assert the classes exist and inherit from `Exception`.  

- [ ] T003 Set up reproducible logging infrastructure used throughout the pipeline (FR‑010).  
  **File path**: `code/utils/logging.py` exposing `get_logger(name: str) -> logging.Logger`.  
  **Verification**: Logs written via `get_logger()` contain timestamp, level, and message, and are saved to `data/logs/pipeline.log`; a unit test (`tests/unit/test_logging.py`) checks file creation and JSON‑line format.  

---

## Phase 2 – Schema contracts  

- [ ] T004 Create the JSON‑Schema contract files required for ingestion and processed data (FR‑001 – FR‑004).  
  **File paths**:  
  `specs/001-predict-corrosion-potential-from-comp/contracts/ingest.schema.yaml`  
  `specs/001-predict-corrosion-potential-from-comp/contracts/dataset.schema.yaml`  
  **Verification**: Both files exist, contain the definitions shown in the specification, and `yamllint` reports no errors.  

- [ ] T005 Generate a reusable schema‑validation utility script.  
  **File path**: `code/utils/validate_schemas.py` providing `validate(data: dict, schema_path: Path) -> None`.  
  **Verification**: Importable and callable; a unit test (`tests/unit/test_validate_schemas.py`) validates a compliant sample against each schema without raising.  

---

## Phase 3 – Data ingestion  

- [ ] T006 Implement the NIST‑IR‑8200 download script with exponential‑backoff retry logic (FR‑001, FR‑015) and optional Materials Project augmentation (FR‑019). Abort with `DataInsufficientError` if < 500 records after merging.  
  **File path**: `code/data/download_nist.py`.  
  **Outputs**: `data/raw/nist/` (raw NIST CSV/JSON) and `data/raw/materials_project/` (composition augment files).  
  **Verification**: Successful run creates both directories, logs attempts in `data/logs/download.log`, and writes a summary JSON (`data/logs/download_summary.json`) containing `record_count` and `alloy_designation_count`. The script exits with non‑zero status if the count thresholds are not met.  

- [ ] T007 Add a schema‑validation step that checks the raw ingest against `ingest.schema.yaml`, enforces non‑null composition, pH, temperature, corrosion potential, and the minimum‑record constraints (FR‑011, FR‑014, FR‑017).  
  **File path**: `code/data/validate_raw.py`.  
  **Artifact**: `data/logs/schema_validation.json` summarising total records, unique alloys, and any violations.  
  **Verification**: The script exits with status 0 only when all criteria are satisfied; otherwise it raises `SchemaMismatchError` with a clear message.  

---

## Phase 4 – Preprocessing  

- [ ] T008 Implement the preprocessing pipeline (FR‑003, FR‑013, FR‑016, FR‑020).  
  **File path**: `code/data/preprocess.py`.  
  **Steps**:  
  • Drop rows missing `ph`, `temperature_celsius`, or `corrosion_potential_mV`.  
  • Flag out‑of‑range pH (< 0 or > 14) as outliers and write them to `data/processed/extreme_conditions.csv`.  
  • Apply centered‑log‑ratio (CLR) transformation to all elemental weight fractions.  
  • One‑hot encode `electrolyte_type`.  
  **Outputs**: `data/processed/clean_dataset.parquet`.  
  **Verification**: The Parquet file contains no nulls in required fields; a checksum file `data/logs/preprocess_checksum.json` is created.  

- [ ] T009 Add diagnostic logging for every excluded record (missing env, extreme pH, schema violations) to the central pipeline log.  
  **File path**: `code/utils/logging.py` (enhanced) – logs written as JSON lines to `data/logs/pipeline.log` with keys `record_id`, `reason`, `timestamp`.  
  **Verification**: After running `preprocess.py`, `pipeline.log` contains at least one entry for each excluded record; a unit test (`tests/unit/test_exclusion_logging.py`) asserts the presence of these entries.  

---

## Phase 5 – Train‑test split  

- [ ] T010 Implement Leave‑One‑Specific‑Alloy‑Out (LOSO) splitting with a pre‑check for ≥ 10 distinct alloy designations (FR‑004, FR‑012, FR‑017).  
  **File path**: `code/data/split.py`.  
  **Outputs**: `data/processed/train_set.parquet` and `data/processed/test_set.parquet`.  
  **Verification**: `data/logs/split_validation.json` reports `"overlap_count": 0` and `"unique_alloys_train"` / `"unique_alloys_test"` counts; the script aborts with `DataInsufficientError` if the alloy count threshold is violated.  

- [ ] T011 Verify split integrity (zero overlap) as a separate validation step.  
  **File path**: `code/utils/validate_split.py`.  
  **Artifact**: `data/logs/split_integrity.json` containing `"overlap_count": 0`.  
  **Verification**: The script exits with status 0 only when the overlap count is zero; otherwise it raises `ValueError`.  

---

## Phase 6 – Model training & evaluation  

- [ ] T012 Train Random Forest and Gradient Boosting regressors on the LOSO training set (FR‑005, FR‑021).  
  **File path**: `code/models/train.py`.  
  **Artifacts**: `results/models/random_forest.pkl`, `results/models/gradient_boosting.pkl`.  
  **Verification**: Training completes within 30 minutes on the GitHub Actions runner (checked via `data/logs/train_time.json`).  

- [ ] T013 Evaluate both models on the held‑out test set, compute R², RMSE (mV), and a null‑baseline (mean prediction) (FR‑006).  
  **File path**: `code/models/evaluate.py`.  
  **Artifact**: `results/metrics.json` containing `model_type`, `r2_score`, `rmse_mV`, and `baseline_r2`.  
  **Verification**: The JSON file adheres to `model_output.schema.yaml` (validated by `code/utils/validate_model_output.py`).  

- [ ] T014 Implement the “learnable” classification logic (FR‑007, FR‑008, SC‑001, SC‑007). Perform a 1 000‑permutation test on each model’s R², apply Bonferroni correction, and require RMSE < ASTM‑G59 tolerance (150 mV). Write the result to `results/model_output.json`.  
  **File path**: `code/models/evaluate.py` (extended).  
  **Verification**: `results/model_output.json` contains the boolean `is_learnable` and all required fields; a unit test (`tests/unit/test_learnability.py`) checks the logic on a synthetic but schema‑conforming example.  

- [ ] T015 Enforce the primary‑model performance threshold R² > 0.6 (FR‑021, SC‑008). Produce a check file and abort if not met.  
  **File path**: `code/utils/check_r2_threshold.py`.  
  **Artifact**: `results/r2_threshold_check.json` with `"passes_threshold": true/false`.  
  **Verification**: The script raises `RuntimeError` when the threshold fails; CI expects exit 0 only when `passes_threshold` is true.  

---

## Phase 7 – Interpretability  

- [ ] T016 Compute conditional permutation importance for the best‑performing model (FR‑007, FR‑008).  
  **File path**: `code/models/interpret.py`.  
  **Artifacts**: `results/interpretability/feature_importance.png` and `results/interpretability/feature_importance.json`.  
  **Verification**: The JSON file conforms to the `feature_importance` schema in `model_output.schema.yaml`; a unit test (`tests/unit/test_permutation_importance.py`) validates the structure and that at least the top‑5 features have `p_value < 0.05` after correction.  

- [ ] T017 Generate Accumulated Local Effects (ALE) plots for the top three element‑environment interaction pairs (FR‑009).  
  **File path**: `code/models/interpret.py` (plotting routine).  
  **Outputs**: PNG files `results/interpretability/ale_<feature1>_vs_<feature2>.png`.  
  **Verification**: Each PNG is non‑empty and a summary CSV `results/interpretability/ale_summary.csv` lists the plotted pairs.  

- [ ] T018 Compile a concise summary report that states whether specific elements consistently reduce corrosion potential across environments (FR‑018).  
  **File path**: `results/interpretability/summary.md`.  
  **Verification**: The markdown contains a “Top 5 features” table, references at least one ALE plot, and includes a concluding sentence such as “Chromium consistently lowers corrosion potential across the examined pH range.”  

---

## Phase 8 – Reproducibility & handoff  

- [ ] T019 Write `quickstart.md` documenting a single CLI command to run the full pipeline and listing the expected final artifacts.  
  **File path**: `quickstart.md`.  
  **Verification**: A fresh checkout followed by `python -m code.cli.run_pipeline` reproduces all artifacts listed in the document; the CI runs an integration test that checks for their existence.  

- [ ] T020 Add an integration test that executes the entire pipeline via the CLI, validates `results/model_output.json` against its schema, and asserts that `is_learnable` is a boolean.  
  **File path**: `tests/integration/test_full_pipeline.py`.  
  **Verification**: The test passes on the GitHub Actions runner without exceeding the 6‑hour runtime limit.  

---

## Phase 9 – Optional polish (non‑essential for scientific validation)  

- [ ] T021 Update `README.md` with installation, API reference, contribution guidelines, and development setup sections.  
- [ ] T022 Profile `code/data/download_nist.py` to ensure peak memory usage stays below 2 GB; record the measurement in `data/logs/memory_profile.txt`.  
- [ ] T023 Optimize `code/data/preprocess.py` to process 10 000 rows in ≤ 30 seconds; store the benchmark in `data/logs/preprocess_benchmark.txt`.  

---

### Dependency map (selected)

| Task | Satisfies FR/US | Produces / Consumes |
|------|-----------------|---------------------|
| T001 | – | Creates directories used by all later tasks |
| T004 | FR‑001 – FR‑004 | Provides schemas for T005, T006, T007 |
| T006 | FR‑001, FR‑002, FR‑015, FR‑019 | Raw files consumed by T007 |
| T008 | FR‑003, FR‑013, FR‑016, FR‑020 | Clean dataset consumed by T010 |
| T010 | FR‑004, FR‑012 | Train/Test sets consumed by T012 |
| T012 | FR‑005, FR‑021 | Model files consumed by T013 |
| T013 | FR‑006 | Metrics consumed by T014 |
| T014 | FR‑007, FR‑008, SC‑001 – SC‑007 | `model_output.json` consumed by T015 |
| T016‑T018 | FR‑007 – FR‑009 | Interpretability artifacts consumed by T018 |
| T019‑T020 | FR‑010, overall reproducibility | Documentation & CI validation |

--- 

*All pending tasks are unchecked; completed tasks should be marked `[x]` once their verification criteria are satisfied.*
