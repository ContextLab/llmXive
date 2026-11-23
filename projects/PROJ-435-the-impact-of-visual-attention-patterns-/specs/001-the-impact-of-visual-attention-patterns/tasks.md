# Tasks: The Impact of Visual Attention Patterns on Susceptibility to Misleading Headlines  

**Input**: `specs/001-impact-of-visual-attention-patterns/spec.md`, `plan.md` (implementation plan), existing project artifacts.  

**Verification**: Each task includes explicit verification steps. All paths are relative to the repository root.  

---  

## Phase 0 – Project scaffolding  

- [ ] **T001** [US0] Create the canonical project directory tree and a helper script.  
  - **Artifact(s)**: `scripts/init_project.py` (exposes `setup_project_structure()`), empty directories `code/`, `data/raw/`, `data/derived/`, `data/processed/`, `tests/`, `state/`, `output/`, `docs/`.  
  - **Verification**: Run `python scripts/init_project.py`; afterwards `tree` (or `ls -R`) must show all listed directories and the script must exit with code 0.  

- [ ] **T002** [US0] Add a pinned `requirements.txt` and a minimal `pyproject.toml` that configures the linting/formatting tools.   <!-- FAILED-IN-EXECUTION: code/verify_requirements.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/verify_requirements.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/verify_requirements.py exit=1 -->
  - **Artifact(s)**: `requirements.txt` (Python 3.11, `pandas`, `numpy`, `statsmodels`, `datasets`, `nltk`, `vaderSentiment`, `ruff`, `black`, `flake8`, `pytest`, `shapely`), `pyproject.toml` (contains `[tool.black]`, `[tool.ruff]` sections).  
  - **Verification**: `pip install -r requirements.txt` succeeds, `ruff --version` and `black --version` run without error, and `ruff check code/` returns no lint failures on a clean repository.  

- [ ] **T003** [US0] Create concrete lint/format configuration files.  
  - **Artifact(s)**: `.ruff.toml` (sets `select = ["E", "F", "W", "C90"]`), `.flake8` (basic ignore list), `pyproject.toml` already contains Black settings (`line-length = 88`).  
  - **Verification**: `ruff check .` and `flake8 .` both exit with status 0; `black --check .` reports no changes needed.  

- [ ] **T023** [FR‑001] Checksum raw data files after ingestion.  
  - **Artifact(s)**: `state/artifacts.yaml` (mapping `data/raw/*.parquet` → SHA‑256 hash).  
  - **Verification**: After data ingestion, a Python script recomputes the hash of each file in `data/raw/` and asserts that the entry in `state/artifacts.yaml` matches the computed hash.  

- [ ] **T024** [FR‑001] Run a PII scan on all files under `data/raw/`.  
  - **Artifact(s)**: `state/pii_scan_report.json` (contains `has_pii: false` on success).  
  - **Verification**: The scan script exits with code 0 and the JSON report contains `"has_pii": false`; any detection causes the pipeline to abort.  

- [ ] **T026** [FR‑001] Create a logging configuration file with required top‑level keys.  
  - **Artifact(s)**: `code/config/logging_config.yaml` containing `level`, `format`, and `handlers` sections.  
  - **Verification**: Loading the YAML with `yaml.safe_load` yields a dict with the three required top‑level keys; missing keys cause the script to exit with an error.  

---  

## Phase 1 – Data ingestion & validation  

- [ ] **T004** [FR‑001] Create a central configuration file for the pipeline.  
  - **Artifact(s)**: `code/config.yaml` containing at least the keys `dataset_id`, `random_seed`, `ivt_duration_threshold`, `fixation_min_duration_ms`. Example values: `dataset_id: "myorg/misinfo-eye-tracking"`, `random_seed: 42`, `ivt_duration_threshold: 30`, `fixation_min_duration_ms: 100`.  
  - **Verification**: `python -c "import yaml, pathlib; cfg = yaml.safe_load(open('code/config.yaml')); assert set(['dataset_id','random_seed','ivt_duration_threshold','fixation_min_duration_ms']).issubset(cfg)"` runs without AssertionError.  

- [ ] **T005** [FR‑001] Implement a data‑loading script that fetches the verified eye‑tracking dataset via the 🤗 datasets library.  
  - **Artifact(s)**: `code/utils/data_loader.py` (function `load_raw_dataset()`), output file `data/raw/eye_tracking_raw.parquet`.  
  - **Side‑effects**: Compute SHA‑256 of the parquet file and write `state/artifacts.yaml` (mapping `eye_tracking_raw.parquet → <hash>`); log the resolved `dataset_id` in `state/runtime_events.json`.  
  - **Verification**: After running `python -m code.utils.data_loader`, the parquet file exists, its hash entry is present in `state/artifacts.yaml`, and `state/runtime_events.json` contains a field `"dataset_id": "<value from config.yaml>"`.  

- [ ] **T006** [FR‑001] Validate the raw file against the `raw_gaze.schema.yaml` contract.  
  - **Artifact(s)**: `code/utils/validate_raw_schema.py` (uses `jsonschema.validate`), validation report `state/schema_validation.json`.  
  - **Verification**: The script exits with code 0 and `state/schema_validation.json` contains `"valid": true`.  

---  

## Phase 2 – Preprocessing (User Story 1)  

- [ ] **T007** [FR‑001] Implement I‑VT fixation detection.  
  - **Artifact(s)**: `code/utils/fixation_detection.py` exposing `detect_fixations(gaze_df, min_duration_ms)`; defaults read from `code/config.yaml`.  
  - **Verification**: Unit test `tests/unit/test_fixation_detection.py` asserts that a synthetic gaze stream with a 120 ms stationary period yields a fixation record of duration ≥ 120 ms.  

- [ ] **T008** [FR‑001] Implement ROI‑mapping logic.  
  - **Artifact(s)**: `code/utils/roi_mapping.py` exposing `map_to_roi(gaze_df, roi_definitions)`; uses `shapely.geometry.Polygon`.  
  - **Verification**: Integration test `tests/integration/test_roi_mapping.py` maps a point known to lie inside a dummy ROI and checks that the resulting `roi_type` column equals the ROI name.  

- [ ] **T009** [FR‑001] Build the preprocessing pipeline.  
  - **Artifact(s)**: `code/pipelines/preprocess_gaze.py` (CLI entry `python -m code.pipelines.preprocess_gaze --threshold 100`).  
  - **Outputs**: `data/derived/preprocessed_gaze.csv` (columns: participant_id, headline_id, fixation_duration, roi_type, …), `output/exclusion_log.txt` (list of participants removed for > 20 % data loss).  
  - **Verification**: After execution, `output/exclusion_log.txt` contains at least one line, and `data/derived/preprocessed_gaze.csv` has a `source_fixation_duration` column for every retained participant.  

- [ ] **T010** [SC‑001] Generate a data‑quality summary.  
  - **Artifact(s)**: `code/pipelines/data_quality_report.py` producing `data/derived/data_quality_summary.csv` with columns `participant_id`, `data_loss_percent`, `excluded_flag`.  
  - **Verification**: The summary file rows sum to the total number of participants in the raw dataset; the count of `excluded_flag == True` matches the number reported in `output/exclusion_log.txt`.  

---  

## Phase 3 – Valence calculation (User Story 1 continued)  

- [ ] **T011** [FR‑003] Calculate headline emotional valence and handle lexicon fallback.  
  - **Artifact(s)**: `code/services/valence_calculator.py` (function `compute_valence(texts)`).  
  - **Outputs**: `data/derived/valence_scores.csv` (columns: `headline_id`, `valence`, `lexicon_used`).  
  - **Side‑effect**: If average NRC coverage < 50 %, the script switches *all* headlines to VADER and logs the event (`"lexicon_switch": true`) in `state/runtime_events.json`.  
  - **Verification**: After running the script, `data/derived/valence_scores.csv` exists, contains a `lexicon_used` column, and `state/runtime_events.json` contains a boolean field `"lexicon_switched"` reflecting the actual behavior.  

---  

## Phase 4 – Merging & outlier handling (User Story 2)  

- [ ] **T012** [FR‑001 & FR‑004] Merge all analysis‑ready tables and cap extreme CRT scores.  
  - **Artifact(s)**: `code/pipelines/merge_datasets.py` producing `data/derived/merged_dataset_full.csv`.  
  - **Processing steps**:  
    1. Load `preprocessed_gaze.csv`, `valence_scores.csv`, and the belief outcome column (`belief_rating`) from the raw parquet.  
    2. Cap `cognitive_reflection_score` at the 1st and 99th percentiles (global).  
    3. Compute `headline_length` (word count) and `total_fixation_duration` (sum of all fixations per participant‑headline).  
  - **Verification**: The resulting CSV validates against `contracts/dataset.schema.yaml` (no missing required columns) and the CRT column contains no values outside the percentile caps.  

---  

## Phase 5 – Mixed‑effects regression (User Story 2)  

- [ ] **T014** [FR‑004 & FR‑007] Fit the mixed‑effects model and apply Holm‑Bonferroni correction.  
  - **Artifact(s)**: `code/services/run_regression.py` (function `run_mixed_effects(df)`).  
  - **Output**: `data/processed/regression_results.json` adhering to `contracts/output.schema.yaml`. The JSON must contain the interaction term, corrected p‑value, `family_wise_error_rate`, and a boolean `significance_flag`.  
  - **Verification**: Validation script `code/utils/validate_regression_output.py` confirms the JSON matches the schema; the field `interaction_term.is_significant` reflects Holm‑Bonferroni‑adjusted significance and `family_wise_error_rate` is present.  

- [ ] **T015** [SC‑005] Record total pipeline runtime and compare against the 300‑minute wall‑clock limit.  
  - **Artifact(s)**: `state/runtime_metrics.json` with keys `total_runtime_seconds`, `limit_seconds`, `within_limit`.  
  - **Verification**: After the full pipeline (tasks T001–T014) finishes, `state/runtime_metrics.json["within_limit"]` is `true`.  

---  

## Phase 6 – Robustness & sensitivity analysis (User Story 3)  

- [ ] **T016** [FR‑005] Perform a fixation‑duration threshold sweep (50 ms, 100 ms, 150 ms).  
  - **Artifact(s)**: `code/pipelines/robustness_sweep.py` (loops over thresholds, re‑runs preprocessing → merge → regression).  
  - **Output**: `data/processed/robustness_report.json` – an array of objects each with `threshold_ms`, `interaction_p_value`, `is_significant`.  
  - **Verification**: The JSON contains exactly three entries; each entry passes schema validation (`contracts/output.schema.yaml` → `robustness` array).  

- [ ] **T017** [SC‑003] Check stability of the three‑way interaction across the sweep.  
  - **Artifact(s)**: `data/processed/stability_check.json` with boolean fields `consistent_direction`, `consistent_significance`, `ci_overlap_summary`.  
  - **Verification**: Running `python -m code.pipelines.stability_check` reads `robustness_report.json` and writes `stability_check.json`; the script exits with code 0 only if both `consistent_direction` and `consistent_significance` are `true`.  

---  

## Phase 7 – Final outputs & hand‑off  

- [ ] **T018** [FR‑006] Generate the causal‑framing statement.  
  - **Artifact(s)**: `code/services/causal_framing.py` reads `regression_results.json` and writes `output/causal_framing_statement.txt`.  
  - **Verification**: The text file is non‑empty and contains the phrase “causal” if the experimental design permits, otherwise contains “associational”.  

- [ ] **T019** [Documentation] Update project README and quick‑start guide.  
  - **Artifact(s)**: `docs/README.md` and `docs/quickstart.md` now list the exact commands to run each pipeline stage (`python -m scripts.init_project`, `python -m code.utils.data_loader`, `python -m code.pipelines.preprocess_gaze`, …).  
  - **Verification**: A reviewer can follow the steps from a fresh clone and reproduce all artifacts without manual edits.  

- [ ] **T020** [Testing] Add comprehensive contract and integration tests for the whole workflow.  
  - **Artifact(s)**:  
    - `tests/contract/test_ingestion_schema.py` (validates raw parquet against `raw_gaze.schema.yaml`).  
    - `tests/contract/test_regression_schema.py` (validates `regression_results.json`).  
    - `tests/contract/test_robustness_schema.py` (validates `robustness_report.json`).  
    - `tests/integration/test_mixed_effects_recovery.py` (runs regression on a tiny real subset and asserts that the three‑way coefficient is present and the JSON conforms to the schema).  
    - `tests/integration/test_sensitivity_analysis.py` (executes `robustness_sweep.py` and checks that `stability_check.json` reports consistency).  
  - **Verification**: `pytest -q` reports 0 failures.  

- [ ] **T021** [End‑to‑end] Provide a one‑command quick‑start script that executes the full analysis from raw download to final report.  
  - **Artifact(s)**: `code/quickstart.py` (calls the pipeline modules in the correct order).  
  - **Verification**: Running `python -m code.quickstart` completes in < 300 minutes on the CI runner, produces `data/processed/regression_results.json`, `output/causal_framing_statement.txt`, and exits with status 0.  

- [ ] **T022** [Data hygiene] Record SHA‑256 hashes for **every** file written under `data/`, `output/`, and `state/`.  
  - **Artifact(s)**: `state/artifacts.yaml` (mapping relative paths → hex hashes).  
  - **Verification**: `python -c "import yaml, hashlib, pathlib; art = yaml.safe_load(open('state/artifacts.yaml')); for p,h in art.items(): assert pathlib.Path(p).read_bytes() and hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() == h"` runs without AssertionError and also asserts that every file under the three directories appears in the mapping.  

- [ ] **T025** [Data model] Implement the data‑model module (`src/models/participant.py`, `src/models/stimulus.py`, `src/models/gaze_event.py`, `src/models/analysis_result.py`) and add schema‑validation tests.  
  - **Artifact(s)**: Model class files and `tests/contract/test_data_model_schema.py`.  
  - **Verification**: Importing each model class succeeds; the contract test validates that instances serialized to JSON conform to the schemas defined in `contracts/`.  

---  

### Dependency ordering  

| Task | Must finish before |
|------|--------------------|
| T001 | – |
| T002, T003, T023, T024, T026 | T001 |
| T004 | T002, T003, T023, T024, T026 |
| T005, T006 | T004 |
| T007, T008 | T005 |
| T009, T010 | T007, T008 |
| T011 | T009 |
| T012 | T009, T011 |
| T014 | T012 |
| T015 | T014 |
| T016 | T014 (re‑run with varied thresholds) |
| T017 | T016 |
| T018 | T014 |
| T019, T020 | T018 |
| T021 | T020 |
| T022 | T021 |
| T025 | – (independent, but should exist before any code that imports the models) |
| T026 | – (logging config must exist before any pipeline execution) |

---  

*All random seeds are fixed in `code/config.yaml` (`random_seed: 42`) and reset before each robustness iteration to guarantee reproducibility.*  