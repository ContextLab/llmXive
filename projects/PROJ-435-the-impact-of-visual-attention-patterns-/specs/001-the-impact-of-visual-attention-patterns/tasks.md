---  
description: "Task list for feature implementation"  
---  

# Tasks: The Impact of Visual Attention Patterns on Susceptibility to Misleading Headlines  

**Input**: Design documents from `/specs/001-impact-of-visual-attention-patterns/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`  

**Tests**: Tests are optional and only included when explicitly requested in the specification.  

**Organization**: Tasks are grouped by phase and then by user story to enable independent implementation and testing of each story.  

## Phase 1: Setup (Shared Infrastructure)  

- [ ] T001 Create project structure per implementation plan: `code/`, `data/raw/`, `data/derived/`, `data/processed/`, `tests/`, `state/` (see `scripts/init_project.py`).  
- [X] T002 Initialize Python 3.11 project with pinned dependencies (`requirements.txt`).  
- [ ] T003 [P] Configure linting (`ruff`/`flake8`) and formatting (`black`) tools.  

---  

## Phase 2: Foundational (Blocking Prerequisites)  

**Purpose**: Core infrastructure that must be complete before any user‑story work can begin.  

- [ ] T008a [P] Create logging configuration file `code/config/logging_config.yaml` with schema:  

  ```yaml
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  handlers:
    - console
    - file
  ```  

- [X] T008b [P] Implement `code/utils/logging_init.py` to load `code/config/logging_config.yaml`, validate required keys, and initialise the global logger.  

- [ ] T005 [P] Create `code/config.yaml` (contains `random_seed:` and `dataset_id:`) and implement `code/utils/data_loading.py` to fetch the eye‑tracking dataset via `datasets.load_dataset(dataset_id, split=..., revision="v1.0")`, compute SHA‑256 checksum, write raw parquet to `data/raw/eye_tracking_raw.parquet`, and log the dataset ID to `state/runtime_events.json`.  

- [ ] T004 [FR-001][FR-002] Implement `code/utils/validate_dataset_schema.py` to verify that `data/raw/eye_tracking_raw.parquet` contains required columns (`headline_text`, `belief_rating`, `cognitive_reflection_score`, `fixation_duration`) **and** ROI definitions (`source_attribution`, `headline_body`). Write validation result to `state/schema_validation.json`.  

- [ ] T004b [FR-004][SC-002] Extract empirical outcome: load `data/raw/eye_tracking_raw.parquet`, enforce presence of a numeric `belief_rating` column (raise `DataInvalidError` if missing or non‑numeric), and write `data/derived/empirical_outcomes.csv` (`participant_id`, `headline_id`, `belief_rating`, `headline_text`).  

- [ ] T006 [FR-001] Implement `code/utils/fixation_detection.py` with I‑VT algorithm (default) and optional I‑DT support. Parameters (`ivt_duration_threshold`, `idt_dispersion_threshold`) are read from `code/config.yaml`. Enforce a minimum fixation duration of 100 ms.  

- [ ] T007 Implement data‑model classes:  

  - `code/models/participant.py` (`id`, `crt_score`, `random_intercept`)  
  - `code/models/stimulus.py` (`id`, `headline_text`, `valence`, `random_intercept`)  
  - `code/models/gaze_event.py` (`timestamp`, `duration`, `roi`, `participant_id`)  

- [ ] T015 [P] Implement ROI‑mapping logic in `code/utils/roi_mapping.py` using point‑in‑polygon to assign each gaze point to a ROI; output adds `roi_type` column to gaze records.  

- [ ] T018 **Core Preprocessing (US‑1)**: Implement `code/02_preprocess_gaze.py` to ingest raw data, apply fixation detection (T006), filter participants with ≥ 20 % data loss, map gaze points to ROIs (T015), handle missing ROI trials, treat zero fixations as duration 0, accept `--threshold` CLI arg for robustness sweeps, and write `data/derived/preprocessed_gaze.csv` plus `output/exclusion_log.txt`.  

- [ ] T040 **Data Quality Report (US‑1)**: Implement `code/02_data_quality_report.py` to read `output/exclusion_log.txt` and `state/data_hashes.json`, compute exclusion statistics, and write `output/data_quality_report.csv` (`participant_id`, `data_loss_pct`, `excluded_flag`).  

- [ ] T021 **Valence Calculation (FR‑003)**: Using `data/derived/empirical_outcomes.csv`, compute NRC lexical coverage; if average coverage < 50 % switch to VADER for **all** headlines, add `lexicon_used` column (`"NRC"` or `"VADER"`), log the fallback event to `state/runtime_events.json`, and write `data/derived/valence_scores.csv`.  

- [ ] T010 [P] [US1] Contract test for data‑ingestion output schema (`tests/contract/test_ingestion_schema.py`).  

- [ ] T011 [P] [US1] Integration test for I‑VT preprocessing on a noisy sample (`tests/integration/test_ivt_preprocessing.py`).  

---  

## Phase 3: User Story 1 – Core Data Ingestion & Preprocessing (Priority P1)  

**Goal**: Produce a clean, ROI‑annotated gaze dataset and a data‑quality report.  

- [ ] T015 (implemented in Phase 2) – ROI‑mapping logic.  
- [ ] T018 (implemented in Phase 2) – Preprocessing script.  
- [ ] T040 (implemented in Phase 2) – Data‑quality report.  

---  

## Phase 4: User Story 2 – Mixed‑Effects Regression Analysis (Priority P2)  

**Goal**: Fit the three‑way interaction model and record corrected statistics.  

- [ ] T020a **Synthetic Data Generator**: Implement `code/utils/synthetic_data_generator.py` to create `data/synthetic/ground_truth.csv` with configurable `n_participants`, `m_headlines`, true three‑way interaction = 0.5, random intercepts, and Gaussian noise (σ = 1.0).  

- [ ] T023 **Data Merge & Outlier Capping**: Merge `data/derived/preprocessed_gaze.csv` (T018), `data/derived/empirical_outcomes.csv` (T004b), and `data/derived/valence_scores.csv` (T021) on `participant_id` & `headline_id`.  

  1. Validate required columns; raise `DataMissingError` if absent.  
  2. Cap `cognitive_reflection_score` at the 1st and 99th percentiles globally.  
  3. Preserve `lexicon_used` as a covariate.  
  4. Compute `headline_length` (word count) and `total_fixation_duration` (sum of fixation durations).  

  Write `data/derived/merged_dataset_full.csv`.  

- [ ] T024 [FR‑007][SC‑004] **Mixed‑Effects Regression & Holm‑Bonferroni Correction**: Using `statsmodels`, fit  

  ```
  belief_rating ~ fixation_duration * valence * crt
                 + headline_length + total_fixation_duration
                 + (1|participant_id) + (1|headline_id)
  ```  

  on `data/derived/merged_dataset_full.csv`.  

  1. Fit model with random intercepts for participants and headlines.  
  2. Apply Holm‑Bonferroni correction to **all** fixed‑effect tests (primary effects, interactions, and controls).  
  3. Write `data/derived/regression_results.csv` containing raw and adjusted p‑values, coefficients, CIs, and interaction terms.  

- [ ] T017 **Measure Runtime**: Implement `code/06_measure_runtime.py` to record wall‑clock time for the full pipeline, compare to the 300‑minute limit, and write `state/runtime_metrics.json` (`total_runtime_minutes`, `limit_minutes`, `status`).  

- [ ] T019 [P] [US2] Contract test for regression output schema (`tests/contract/test_regression_schema.py`).  

- [ ] T020 [P] [US2] Integration test for coefficient recovery on synthetic data: load `data/synthetic/ground_truth.csv`, run the regression logic (as in T024) on the synthetic set, and assert that the estimated three‑way interaction coefficient is within 5 % of the true value and that random intercepts are identified.  

---  

## Phase 5: User Story 3 – Robustness & Sensitivity Analysis (Priority P3)  

**Goal**: Demonstrate that findings are stable across methodological variations.  

- [ ] T032 **Robustness Runner**: Refactor the regression pipeline from T024 into a reusable function `run_regression(threshold: int) -> dict` that accepts a fixation‑duration threshold, executes the full preprocessing‑through‑regression flow, and returns regression statistics.  

- [ ] T034 **Headline‑Length Control Verification**: Extend `code/05_regression_analysis.py` (now part of T032) to assert that `headline_length` is included as a fixed effect; write a short verification log `output/verification_log.txt`.  

- [ ] T033 **Robustness Sweep**: For each fixation‑duration threshold in {50 ms, 100 ms, 150 ms}:  

  1. Reset the random seed to `config.random_seed`.  
  2. Load raw gaze data (`data/raw/eye_tracking_raw.parquet`).  
  3. Apply fixation detection with the current threshold (bypassing the full T018 pipeline).  
  4. Map gaze points to ROIs (T015) and re‑apply participant filtering (as in T018).  
  5. Merge with valence and outcome data (T023 logic).  
  6. Run regression via the robustness runner (T032).  
  7. Compute `mean_belief_rating`, `std_dev_belief`, and `range_belief` for the current threshold.  
  8. Append a row to `data/derived/robustness_report.csv` (`threshold_ms`, `mean_belief`, `std_dev`, `range`, `interaction_coeff`, `p_adj`).  

- [ ] T039 **Stability Check**: Read `data/derived/robustness_report.csv`, verify that the sign and significance of the three‑way interaction term are consistent across thresholds, and write `output/stability_check.json` with fields `consistent_direction`, `consistent_significance`, `ci_overlap_summary`.  

- [ ] T029 [P] [US3] Contract test for robustness‑report schema (`tests/contract/test_robustness_schema.py`).  

- [ ] T030 [P] [US3] Integration test for threshold‑sweep stability (`tests/integration/test_sensitivity_analysis.py`).  

---  

## Phase N: Polish & Cross‑Cutting Concerns  

- [ ] T045 **Documentation Updates**: Refresh `docs/README.md` with final pipeline steps and update `paper/abstract.md` using the causal framing statement generated by T028.  

- [ ] T046 **Code Cleanup & Refactoring**: Reduce cyclomatic complexity of `code/utils/fixation_detection.py` and `code/utils/roi_mapping.py` to < 10, verify with `ruff --max-complexity=10`, and write `output/refactoring_report.txt`.  

- [ ] T047 **Performance Optimisation**: Vectorise the merge operation in T023, cache intermediate results in T018, and confirm that total runtime < 300 min and memory < 7 GB on the reference dataset; output metrics to `output/performance_metrics.json`.  

- [ ] T048 [P] **Additional Unit Tests**:  

  - `tests/unit/test_fixation_detection.py` (edge cases: exact threshold, zero‑duration).  
  - `tests/unit/test_valence_calculation.py` (lexicon fallback logic).  

- [ ] T049 **Quickstart Validation**: Run the quick‑start script (`code/quickstart.py`) and verify successful end‑to‑end execution; fix any failures.  

- [ ] T050 **Artifact Checksumming**: Ensure every file written to `data/`, `output/`, and `state/` is recorded with a SHA‑256 hash in `state/artifacts.yaml`.  

- [ ] T028 [P] **Final Report Generation**: Implement `code/07_generate_causal_framing.py` to read `data/derived/regression_results.csv`, extract the three‑way interaction coefficient and corrected p‑value, and compose a causal framing statement respecting FR‑006; write `output/causal_framing_statement.txt`.  

---  

## Dependencies & Execution Order  

| Phase | Must finish before | Notes |
|------|--------------------|-------|
| **Setup** (Phase 1) | – | Independent |
| **Foundational** (Phase 2) | Setup | All logging, config, and data‑loading tasks must succeed before any user‑story work. |
| **User Story 1** | Foundational | T018 → T040 (contracts T010/T011) |
| **User Story 2** | Foundational & US 1 outputs | T020a → T023 → T024 → T017 (contracts T019/T020) |
| **User Story 3** | Foundational & US 2 outputs | T032 (uses T024 logic) → T033 → T039 (contracts T029/T030) |
| **Polish** (Phase N) | All previous phases | Generates documentation, final report, and performs cleanup. |

Parallelism (`[P]`) may be exploited where tasks have no direct file‑level conflicts and their hard dependencies are satisfied.  

---  

*All random seeds are pinned in `code/config.yaml` (`random_seed: 42`) and reset before each robustness iteration to guarantee reproducibility. Every artifact written is recorded in `state/` with a SHA‑256 hash to satisfy Constitution III (Data Hygiene). The belief rating column serves as the required empirical outcome and also captures participants’ confidence in the headline, addressing the reviewer’s suggestion without adding new data collection.*
