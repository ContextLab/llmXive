# Tasks: Predicting Corrosion Potential from Composition and Environment

**Inputs**: `spec.md`, `plan.md`, original research idea, existing artifacts, and reviewer feedback.

The checklist below follows the canonical `- [ ] T### [P?] [USx?] description with file path` format.  
Unchecked boxes indicate work that still needs to be completed or corrected; checked boxes denote tasks whose artifacts have already been verified.

---

## Phase 1 – Project setup & core utilities  

- [ ] **T001** Create the required project directory hierarchy (`code/`, `data/`, `data/raw/`, `data/processed/`, `data/logs/`, `results/`) and produce a verification manifest.  
  **File path**: `code/utils/setup_dirs.py` → generates `state/setup_dirs_verified.json`.  
  **Verification**: Running `python -m code.utils.setup_dirs` exits with status 0, creates all directories, writes a JSON array where each entry contains `"path"` (absolute) and `"created_at"` (ISO‑8601 timestamp), and a subsequent check task confirms the file exists and is non‑empty.

- [ ] **T001a** Verify that `state/setup_dirs_verified.json` exists and contains entries for all required directories.  
  **File path**: `code/utils/verify_setup.py` → reads the manifest and asserts completeness.  
  **Verification**: Script exits with status 0 only when all directories are listed; otherwise it raises `RuntimeError`.

- [X] **T002** Implement custom exception classes `DataInsufficientError` and `SchemaMismatchError`.  
  **File path**: `code/utils/exceptions.py`.  
  **Verification**: Import succeeds (`from code.utils.exceptions import DataInsufficientError, SchemaMismatchError`) and unit tests in `tests/unit/test_exceptions.py` assert inheritance from `Exception`.  

- [X] **T003** Set up reproducible logging infrastructure used throughout the pipeline (FR‑010).  
  **File path**: `code/utils/logging.py` exposing `get_logger(name: str) -> logging.Logger`.  
  **Verification**: Logs written via `get_logger()` contain timestamp, level, and message, are saved to `data/logs/pipeline.log`, and a unit test (`tests/unit/test_logging.py`) checks file creation and JSON‑line format.  

- [X] **T003a** Verify that `data/logs/pipeline.log` exists and contains at least one entry for each pipeline stage.
  **File path**: `code/utils/verify_logging.py` → scans the log file and asserts non‑emptiness per stage.  
  **Verification**: Script exits with status 0 only when the log is populated; otherwise raises `RuntimeError`.

- [ ] **T028** Pin random seeds in a central configuration file and ensure all scripts load them.  
  **File path**: `code/utils/config_loader.py` reads `config/seeds.yaml` (contains `random_seed: 42`).  
  **Verification**: Unit test (`tests/unit/test_seeds.py`) checks that `np.random.seed`, `random.seed`, and `torch.manual_seed` (if torch is present) are set to the configured value.

---

## Phase 2 – Schema contracts  

- [X] **T004** Create the JSON‑Schema contract files required for ingestion and processed data (FR‑001 – FR‑004).  
  **File paths**:  
  `specs/001-predict-corrosion-potential-from-comp/contracts/ingest.schema.yaml`  
  `specs/001-predict-corrosion-potential-from-comp/contracts/dataset.schema.yaml`  
  **Verification**: Both files exist, contain the definitions shown in the specification, and pass `yamllint` without errors.

- [ ] **T004a** Write the actual `ingest.schema.yaml` file content as defined in the spec.  
  **File path**: same as above – ensures the file is populated.

- [ ] **T004b** Write the actual `dataset.schema.yaml` file content as defined in the spec.  
  **File path**: same as above – ensures the file is populated.

- [ ] **T005** Generate a reusable schema‑validation utility script.  
  **File path**: `code/utils/validate_schemas.py` providing `validate(data: dict, schema_path: Path) -> None`.  
  **Verification**: Importable and callable; a unit test (`tests/unit/test_validate_schemas.py`) validates a compliant sample against each schema without raising.  

---

## Phase 3 – Data ingestion  

- [ ] **T006** Implement the NIST‑IR‑8200 download script with exponential‑backoff retry logic (FR‑001, FR‑015) and optional Materials Project augmentation (FR‑019). Abort with `DataInsufficientError` if < 500 records after merging.   <!-- FAILED-IN-EXECUTION: code/cli/run_pipeline.py exit=1 -->
  **File path**: `code/data/download_nist.py`.  
  **Outputs**: `data/raw/nist/` (raw NIST CSV/JSON) and `data/raw/materials_project/` (composition augment files).  
  **Verification**: Successful run creates both directories, logs attempts in `data/logs/download.log`, writes `data/logs/download_summary.json` containing `record_count` and `alloy_designation_count`, and exits with non‑zero status if thresholds are unmet.

- [ ] **T027** Generate SHA‑256 checksums for all files under `data/raw/` and record them in `state/projects/PROJ-376-predicting-corrosion-potential-from-comp.yaml`.  
  **File path**: `code/utils/checksums.py`.  
  **Verification**: After execution, the state YAML contains an `artifact_hashes` map with entries for each raw file; a unit test confirms the map is populated.

- [ ] **T007** Add a schema‑validation step that checks the raw ingest against `ingest.schema.yaml`, enforces non‑null composition, pH, temperature, corrosion potential, and the minimum‑record constraints (FR‑011, FR‑014, FR‑017).  
  **File path**: `code/data/validate_raw.py`.  
  **Artifact**: `data/logs/schema_validation.json` summarising total records, unique alloys, and any violations.  
  **Verification**: Script exits with status 0 only when all criteria are satisfied; otherwise it raises `SchemaMismatchError` with a clear message.  

---

## Phase 4 – Preprocessing  

- [ ] **T009** Enhance the logging utilities to record diagnostics for every excluded record (missing env, extreme pH, schema violations).  
  **File path**: `code/utils/logging.py` (enhanced) – logs written as JSON lines to `data/logs/pipeline.log` with keys `record_id`, `reason`, `timestamp`.  
  **Verification**: After running `preprocess.py`, `pipeline.log` contains entries for each excluded record; a unit test (`tests/unit/test_exclusion_logging.py`) asserts presence.

- [ ] **T008** Implement the preprocessing pipeline (FR‑003, FR‑013, FR‑016, FR‑020).  
  **File path**: `code/data/preprocess.py`.  
  **Steps**:  
  • Drop rows missing `ph`, `temperature_celsius`, or `corrosion_potential_mV`.  
  • Flag out‑of‑range pH (< 0 or > 14) as outliers and write them to `data/processed/extreme_conditions.csv`.  
  • Apply centered‑log‑ratio (CLR) transformation to all elemental weight fractions.  
  • One‑hot encode `electrolyte_type`.  
  **Outputs**: `data/processed/clean_dataset.parquet`.  
  **Verification**: The Parquet file contains no nulls in required fields; a checksum file `data/logs/preprocess_checksum.json` is created.

- [ ] **T010** Implement Leave‑One‑Specific‑Alloy‑Out (LOSO) splitting with a pre‑check for ≥ 10 distinct alloy designations (FR‑004, FR‑012, FR‑017).  
  **File path**: `code/data/split.py`.  
  **Outputs**: `data/processed/train_set.parquet` and `data/processed/test_set.parquet`.  
  **Verification**: `data/logs/split_validation.json` reports `"overlap_count": 0` and `"unique_alloys_train"` / `"unique_alloys_test"` counts; the script aborts with `DataInsufficientError` if the alloy count threshold is violated.  

- [ ] **T011** Verify split integrity (zero overlap) as a separate validation step.  
  **File path**: `code/utils/validate_split.py`.  
  **Artifact**: `data/logs/split_integrity.json` containing `"overlap_count": 0`.  
  **Verification**: Script exits with status 0 only when overlap count is zero; otherwise it raises `ValueError`.  

---

## Phase 5 – Model training & evaluation  

- [ ] **T012** Train Random Forest and Gradient Boosting regressors on the LOSO training set (FR‑005, FR‑021).  
  **File path**: `code/models/train.py`.  
  **Artifacts**: `results/models/random_forest.pkl`, `results/models/gradient_boosting.pkl`.  
  **Verification**: Training completes within 30 minutes on the GitHub Actions runner (checked via `data/logs/train_time.json`).  

- [ ] **T013** Evaluate both models on the held‑out test set, compute R², RMSE (mV), and a null‑baseline (mean prediction) (FR‑006).  
  **File path**: `code/models/evaluate.py`.  
  **Artifact**: `results/metrics.json` containing `model_type`, `r2_score`, `rmse_mV`, and `baseline_r2`.  
  **Verification**: The JSON file adheres to `model_output.schema.yaml` (validated by `code/utils/validate_model_output.py`).  

- [ ] **T014** Implement the “learnable” classification logic (FR‑007, FR‑008, SC‑001, SC‑007). Perform a 1 000‑permutation test on each model’s R², apply Bonferroni correction, and require RMSE < 150 mV. Write the result to `results/model_output.json`.  
  **File path**: `code/models/evaluate.py` (extended).  
  **Verification**: `results/model_output.json` contains the boolean `is_learnable` and all required fields; a unit test (`tests/unit/test_learnability.py`) checks the logic on a synthetic but schema‑conforming example.  

- [ ] **T014a** Validate that `results/model_output.json` conforms to `model_output.schema.yaml` and that the `is_learnable` field is present and boolean.  
  **File path**: `code/utils/validate_model_output.py`.  
  **Verification**: Script exits with status 0 only when schema validation passes; otherwise raises `ValidationError`.  

- [ ] **T015** Enforce the primary‑model performance threshold R² > 0.6 (FR‑021, SC‑008). Produce a check file and abort if not met.  
  **File path**: `code/utils/check_r2_threshold.py`.  
  **Artifact**: `results/r2_threshold_check.json` with `"passes_threshold": true/false`.  
  **Verification**: Script raises `RuntimeError` when the threshold fails; CI expects exit 0 only when `passes_threshold` is true.  

- [ ] **T025** Assert that the RMSE for the selected model does not exceed the ASTM G59 tolerance of 150 mV and record the outcome.  
  **File path**: `code/utils/check_rmse_tolerance.py`.  
  **Artifact**: `results/rmse_tolerance_check.json` with `"within_tolerance": true/false`.  
  **Verification**: Script raises `RuntimeError` if `within_tolerance` is false.  

---

## Phase 6 – Interpretability  

- [ ] **T016** Compute **Conditional Permutation Importance** (CPI) for the best‑performing model (FR‑007, FR‑008).  
  **File path**: `code/models/interpret.py`.  
  **Artifacts**: `results/interpretability/feature_importance.png`, `results/interpretability/feature_importance.json`.  
  **Verification**: The JSON conforms to the `feature_importance` schema in `model_output.schema.yaml`; a unit test (`tests/unit/test_permutation_importance.py`) validates the structure and that at least the top‑5 features have `p_value < 0.05` after correction.  

- [ ] **T017** Generate **Accumulated Local Effects (ALE)** plots for the top three element‑environment interaction pairs (FR‑009).  
  **File path**: `code/models/interpret.py` (plotting routine).  
  **Outputs**: PNG files `results/interpretability/ale_<feature1>_vs_<feature2>.png`.  
  **Verification**: Each PNG is non‑empty and a summary CSV `results/interpretability/ale_summary.csv` lists the plotted pairs.  

- [ ] **T024** Generate **Partial Dependence Plots (PDP)** for the same three interaction pairs to satisfy FR‑009.  
  **File path**: `code/models/interpret.py` (PDP routine).  
  **Outputs**: PNG files `results/interpretability/pdp_<feature1>_vs_<feature2>.png`.  
  **Verification**: Each PNG is non‑empty and a summary CSV `results/interpretability/pdp_summary.csv` lists the plotted pairs.  

- [ ] **T018** Compile a concise summary report that states whether specific elements consistently reduce corrosion potential across environments (FR‑018).  
  **File path**: `results/interpretability/summary.md`.  
  **Verification**: The markdown contains a “Top 5 features” table, references at least one ALE and one PDP plot, and includes a concluding sentence such as “Chromium consistently lowers corrosion potential across the examined pH range.”  

---

## Phase 7 – Reproducibility & handoff  

- [ ] **T019** Write `quickstart.md` documenting a single CLI command to run the full pipeline and listing the expected final artifacts.  
  **File path**: `quickstart.md`.  
  **Verification**: A fresh checkout followed by `python -m code.cli.run_pipeline` reproduces all artifacts listed in the document; the CI runs an integration test that checks for their existence.  

- [ ] **T020** Add an integration test that executes the entire pipeline via the CLI, validates `results/model_output.json` against its schema, and asserts that `is_learnable` is a boolean.  
  **File path**: `tests/integration/test_full_pipeline.py`.  
  **Verification**: The test passes on the GitHub Actions runner without exceeding the 6‑hour runtime limit.  

- [ ] **T026** Record total pipeline execution time and assert it does not exceed 6 hours (SC‑005).  
  **File path**: `code/utils/record_runtime.py`.  
  **Artifact**: `data/logs/pipeline_runtime.json` with `"total_seconds"` and `"within_limit": true/false`.  
  **Verification**: Script raises `RuntimeError` if `within_limit` is false.  

---

## Phase 8 – Optional polish (non‑essential for scientific validation)  

- [ ] **T021** Update `README.md` with installation, API reference, contribution guidelines, and development setup sections.  
  **Verification**: After update, a CI step checks that `README.md` exists and contains the required sections.  

- [ ] **T022** Profile `code/data/download_nist.py` for memory usage – record the measurement in `data/logs/memory_profile.txt` and assert peak memory ≤ 2 GB.  
  **Verification**: CI test parses the file and fails if the value exceeds 2 GB.  

- [ ] **T023** Optimize `code/data/preprocess.py` for speed – store benchmark in `data/logs/preprocess_benchmark.txt` and assert runtime ≤ 30 seconds.  
  **Verification**: CI test reads the benchmark and fails if the runtime is greater than 30 seconds.  

- [ ] **T029** Verify that `data/logs/pipeline.log` is populated for every stage of the pipeline (non‑empty).  
  **Verification**: Script scans the log and raises `RuntimeError` if any stage is missing.  

---

### Dependency map (selected)

| Task | Satisfies FR/US | Produces / Consumes |
|------|-----------------|---------------------|
| T001 | – | Creates directories used by all later tasks |
| T001a | – | Verifies `state/setup_dirs_verified.json` |
| T002 | – | Exception classes used by validation & ingestion |
| T003 | FR‑010 | Logging utilities; creates `data/logs/pipeline.log` |
| T003a | FR‑010 | Verifies log completeness |
| T028 | Constitution‑I | Seed config file and loader |
| T004 | FR‑001 – FR‑004 | Schema files for validation |
| T004a/T004b | – | Populate the schema files |
| T005 | – | Validation utility used by T006‑T007 |
| T006 | FR‑001, FR‑002, FR‑015, FR‑019 | Raw files consumed by T007 |
| T027 | Constitution‑III | Checksums recorded in state YAML |
| T007 | FR‑011, FR‑014, FR‑017 | `schema_validation.json` |
| T009 | FR‑010 | Diagnostic entries in `pipeline.log` |
| T008 | FR‑003, FR‑013, FR‑016, FR‑020 | Clean dataset consumed by T010 |
| T010 | FR‑004, FR‑012, FR‑017 | Train/Test sets consumed by T012 |
| T011 | – | Split integrity check |
| T012 | FR‑005, FR‑021 | Model pickle files |
| T013 | FR‑006 | `results/metrics.json` |
| T014 | FR‑007, FR‑008, SC‑001 – SC‑007 | `results/model_output.json` |
| T014a | – | Validates `model_output.json` |
| T015 | FR‑021, SC‑008 | R² threshold check |
| T025 | SC‑002 | RMSE tolerance check |
| T016 | FR‑007, FR‑008 | Conditional permutation importance |
| T017 | FR‑009 | ALE plots |
| T024 | FR‑009 | PDP plots |
| T018 | FR‑018 | Interpretability summary |
| T019 | FR‑010 | End‑to‑end usage guide |
| T020 | – | Full‑pipeline integration test |
| T026 | SC‑005 | Total runtime check |
| T021‑T023 | – | Documentation & performance polish |
| T029 | FR‑010 | Log‑non‑empty verification |

*All pending tasks are unchecked; completed tasks are marked `[x]` once their verification criteria are satisfied.*  
