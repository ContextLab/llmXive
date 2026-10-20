# Tasks: Predicting Corrosion Potential from Composition and Environment

**Input**: Design documents from `/specs/001-predict-corrosion-potential/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

**Tests**: The examples below include test tasks. Tests are OPTIONAL – only include them if explicitly requested in the feature specification.

## Phase 1: Setup and first end‑to‑end analysis

- [ ] T001 Establish the required project directory hierarchy and produce a verification manifest.  
  **File path**: `code/utils/setup_dirs.py` (creates `code/`, `data/`, `data/raw/`, `data/processed/`, `data/logs/`, `results/`, `state/`).  
  **Artifact**: `state/setup_dirs_verified.json` – an array of objects `{"path": "<absolute_path>", "created_at": "<ISO8601_timestamp>"}` for each directory.  
  **Verification**: Running `python code/utils/setup_dirs.py` must exit with status 0, all directories must exist, and the JSON manifest must be valid.

- [ ] T045 Measure total pipeline execution time and enforce the ≤ 6 h limit (SC‑005).  
  **File path**: `code/utils/runtime_tracker.py` (wraps the full CLI run).  
  **Artifact**: `data/logs/pipeline_runtime.json` containing `{"total_seconds": <float>, "within_limit": true/false}`.  
  **Verification**: After a full pipeline run, the JSON must exist and `within_limit` must be true; otherwise the pipeline exits with a non‑zero status.

- [ ] T046 Compute SHA‑256 checksums for all raw data files and store them in a manifest.  
  **File path**: `code/utils/checksum.py`.  
  **Artifact**: `data/logs/checksums_manifest.json` – a list of `{ "file": "<relative_path>", "sha256": "<hex>" }`.  
  **Verification**: Running the script after ingestion must produce a non‑empty manifest with a checksum entry for each file in `data/raw/`.

- [ ] T047 Record content hashes for all produced artifacts in the project state file (Constitution V).  
  **File path**: `code/utils/version_hashes.py`.  
  **Artifact**: `state/projects/PROJ-376-predict-corrosion-potential-from-comp.yaml` – updated `artifact_hashes` map with `{ "<relative_path>": "<sha256>" }`.  
  **Verification**: After any artifact creation step, the state file contains a matching hash entry.

- [ ] T005 [ ] Implement custom exception classes `DataInsufficientError` and `SchemaMismatchError` in `code/utils/exceptions.py`.  
  **Verification**: Import the module and assert the classes exist; unit tests in `tests/unit/test_exceptions.py` must pass.

- [ ] T006 Set up reproducible logging infrastructure in `code/utils/logging.py` (FR‑010).  
  **Verification**: Logs written via `get_logger()` contain timestamps, severity levels, and are saved to `data/logs/pipeline.log`. *(Removed unsafe `[P]` tag; logging is sequential.)*

- [ ] T007 Create base data‑model classes (`AlloyRecord`, `EnvironmentRecord`, `CorrosionMeasurement`) using Pydantic v2 in `code/models/data_models.py`.  
  **Verification**: `tests/unit/test_data_models.py` validates correct schema enforcement for valid and invalid inputs.

## Phase 2: Contracts and foundational infrastructure

- [ ] T004 Create the JSON‑Schema contract files required for ingestion and processed data.  
  **File paths**:  
  `specs/001-predict-corrosion-potential-from-comp/contracts/ingest.schema.yaml`  
  `specs/001-predict-corrosion-potential-from-comp/contracts/dataset.schema.yaml`  
  **Content**: Must match the definitions provided in the specification (see the `ingest.schema.yaml` and `dataset.schema.yaml` sections).  
  **Verification**: `yamllint` runs without errors and a validation script (`code/utils/validate_schemas.py`) reports both schemas as valid.

- [ ] T014a Generate the schema‑validation utility script `code/utils/validate_schemas.py`.  
  **File path**: `code/utils/validate_schemas.py` (loads the YAML schemas and provides a `validate(data, schema_path)` function).  
  **Verification**: Importable and usable by downstream validation tasks; unit test `tests/unit/test_validate_schemas.py` must pass.

- [ ] T014 Implement the schema‑validation step in `code/data/preprocess.py`.  
  **Checks**: Conformance to `ingest.schema.yaml`, non‑null composition, pH, temperature, corrosion potential; total record count ≥ 500; at least 10 distinct `specific_alloy_designation`.  
  **Failure mode**: Raise `SchemaMismatchError` with a clear message.  
  **Artifact**: `data/logs/schema_validation.json` summarising counts and validation status.  
  **Verification**: Running the script on the raw files must exit 0 only when all criteria are satisfied.

- [ ] T008 Implement the data‑ingestion script `code/data/download_nist.py`.  
  **Requirements**:  
  • Download alloy composition and corrosion records from the NIST‑IR‑8200 database (FR‑001, FR‑002).  
  • Apply exponential backoff retry logic for HTTP 429 responses (up to 3 retries, base 5 s, max 60 s) (FR‑015).  
  • Merge composition data from the Materials Project API (`[UNRESOLVED-CLAIM: https://materialsproject.org` — ConnectionError: HTTPSConnectionPool(host='materialsproject.org%60', port=443): Max retries exceeded with url: / (Caused by NameResolutionError("HTTPSConnection(host='materialsproject.org%60', port=443): Failed to resolve 'materialsproject.org%60' ([Errno -2] Name or service not known)"))]) when available (FR‑019).  
  • Abort with `DataInsufficientError` if no programmatic URL is known or the record count is < 500.  
  **Outputs**: Raw files under `data/raw/nist/` and `data/raw/materials_project/`.  
  **Verification**: Successful run creates both directories and logs attempts in `data/logs/download.log`.

- [ ] T009 Implement the preprocessing pipeline in `code/data/preprocess.py`.  
  **Steps**:  
  • Drop rows missing `ph`, `temperature_celsius`, or `corrosion_potential_mV`.  
  • Flag records with out‑of‑range pH (< 0 or > 14) as outliers; write them to `data/processed/extreme_conditions.csv`.  
  • Apply centered‑log‑ratio (CLR) transformation to all elemental weight fractions (FR‑020).  
  • One‑hot encode `electrolyte_type`.  
  • Output a Parquet file `data/processed/clean_dataset.parquet`.  
  **Verification**: The Parquet file contains no nulls in required fields and the outlier CSV is non‑empty when applicable.

- [ ] T016 Add diagnostic logging for all excluded records (missing pH, extreme pH, schema violations) to `data/logs/pipeline.log`.  
  **Format**: JSON lines with keys `record_id`, `reason`, `timestamp`.  
  **Verification**: After running `preprocess.py`, the log file must contain at least one entry for each excluded record.

## Phase 3: Dataset splitting

- [ ] T015 Implement LOSO (Leave‑One‑Specific‑Alloy‑Out) splitting in `code/data/split.py`.  
  **Pre‑check**: Verify ≥ 10 distinct alloy designations; otherwise raise `DataInsufficientError`.  
  **Outputs**: `data/processed/train_set.parquet` and `data/processed/test_set.parquet`.  
  **Verification**: `data/logs/split_validation.json` reports `"overlap_count": 0`.

- [ ] T017 Verify split integrity (zero overlap) using the validation log produced by T015.  
  **Artifact**: `data/logs/split_validation.json`.  
  **Verification**: The JSON must contain `"overlap_count": 0`.

## Phase 4: Model training and evaluation

- [ ] T020 Implement `code/models/train.py` to train Random Forest and Gradient Boosting regressors on the LOSO training set.  
  **Requirements**: CPU‑only scikit‑learn, `random_state=42`, respect FR‑005 and FR‑021.  
  **Artifacts**: `results/models/random_forest.pkl`, `results/models/gradient_boosting.pkl`.

- [ ] T021 Implement `code/models/evaluate.py` to calculate R² and RMSE (mV) on the held‑out test set and compute a null‑baseline (mean prediction).  
  **Artifact**: `results/metrics.json`.

- [ ] T022 Implement the “learnable” classification logic in `code/models/evaluate.py`.  
  **Logic**:  
  1. Perform a permutation test (1 000 permutations, seed 42) on each model’s R²; apply Bonferroni correction across the two models.  
  2. Declare a model “learnable” only if `R² > 0.0` **and** the corrected p‑value < 0.05 **and** RMSE < the ASTM tolerance from `config/astm_g59_tolerance.yaml`.  
  3. Write the boolean field `is_learnable` to `results/model_results.json` conforming to `model_output.schema.yaml`.  
  **Verification**: The JSON file contains `is_learnable: true/false` and all required fields; a unit test in `tests/unit/test_learnability.py` validates the logic.

- [ ] T048 Enforce primary model R² > 0.6 on the held‑out test set (FR‑021, SC‑008).  
  **File path**: `code/models/evaluate.py` (post‑metric calculation).  
  **Artifact**: `results/r2_threshold_check.json` – a JSON file with `{ "model_type": "<best-model>", "r2_score": <float>, "passes_threshold": true/false }`.  
  **Verification**: The script writes the artifact and aborts with a clear error if `passes_threshold` is false; unit test `tests/unit/test_r2_threshold.py` confirms that a failure triggers a non‑zero exit code and that the JSON reflects the pass/fail status.

- [ ] T048a Add a validation step that asserts SC‑008 by reading `results/r2_threshold_check.json` and failing the pipeline if the threshold is not met.  
  **File path**: `code/utils/validate_r2_threshold.py`.  
  **Artifact**: None (raises exception on failure).  
  **Verification**: Integrated into the pipeline; CI checks that the script exits with status 0 when the threshold is satisfied.

- [ ] T023a Create configuration file `config/astm_g59_tolerance.yaml` with `tolerance_mV: 150` (FR‑021, SC‑002).  
  **Verification**: The file exists and can be parsed with `yaml.safe_load`.

- [ ] T049 Validate `results/model_output.json` against `contracts/model_output.schema.yaml`.  
  **File path**: `code/utils/validate_model_output.py`.  
  **Artifact**: Validation passes silently; failures raise a `ValidationError`.  
  **Verification**: CI runs the script and expects exit 0.

- [ ] T024 Save model artifacts and metrics to `results/model_results.json` conforming to `contracts/model_results.schema.yaml`.  
  **Verification**: `code/utils/validate_schema.py` validates the file without errors.

## Phase 5: Interpretability and reporting

- [ ] T027 Compute conditional permutation importance for the best‑performing model (`code/models/interpret.py`) (FR‑007).  
  **Parameters**: 1 000 permutations, Bonferroni/FDR correction (FR‑008).  
  **Artifacts**: `results/interpretability/feature_importance.png` and `results/interpretability/feature_importance.json`.

- [ ] T028 Generate Accumulated Local Effects (ALE) plots for the top element‑environment interaction pairs (e.g., Chromium vs pH) (`code/models/interpret.py`) (FR‑009).  
  **Outputs**: PNG files under `results/interpretability/ale_*.png`.

- [ ] T030 Compile a summary report (`results/interpretability/summary.md`) stating whether specific elements consistently reduce corrosion potential across environments (FR‑018).  
  **Verification**: The markdown file contains the heading “Top 5 features”, references at least one ALE plot, and includes a concluding statement on element consistency.

## Phase 6: Reproducible results and paper handoff

- [ ] T031 Create `quickstart.md` that documents the single CLI command to run the full pipeline (`python code/cli/run_pipeline.py`) and lists the expected final artifacts (`clean_dataset.parquet`, `model_results.json`, interpretability figures).  
  **Verification**: Executing the command from a fresh checkout reproduces all artifacts and the quick‑start steps complete without error.

- [ ] T038 Add integration test `tests/integration/test_full_pipeline.py` that runs the pipeline via the CLI, asserts the existence and schema‑validity of `results/model_results.json`, and checks that `is_learnable` is a boolean.  
  **Verification**: The test passes on the CI runner.

## Phase 7: Polish & cross‑cutting concerns

- [ ] T039a Update `README.md`: Add installation section with specific steps.  
- [ ] T039b Update `README.md`: Add API reference section for key scripts.  
- [ ] T039c Update `README.md`: Add contribution guidelines section.  
- [ ] T039d Update `README.md`: Add development setup instructions.  

- [ ] T033 Profile `code/data/download_nist.py` to ensure peak memory usage stays below 2 GB; record the measurement in `data/logs/memory_profile.txt`.  
  **Verification**: The reported peak memory < 2 GB.

- [ ] T034 Optimize `code/data/preprocess.py` to complete preprocessing of 10 000 rows in under 30 seconds; benchmark result stored in `data/logs/preprocess_benchmark.txt`.  
  **Verification**: Benchmark file reports elapsed time ≤ 30 s.

- [ ] T035 [ ] Additional unit tests for edge cases (pH > 14, pH < 0) in `tests/unit/`.  
- [ ] T036 Run `quickstart.md` validation to ensure full pipeline reproducibility.
