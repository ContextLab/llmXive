# Tasks: Predicting the Impact of Cold Work on Recrystallization Kinetics in Aluminum Alloys

**Input**: Design documents from `/specs/001-cold-work-recrystallization/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup & Foundational

**Purpose**: Project initialization, basic structure, and core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T001 [P] Create project root directories: `projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/code`, `projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/tests`, `projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/data`, `projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/artifacts`. **Requirement**: Create `.gitkeep` files in all new directories to ensure they are tracked by version control.
- [ ] T002 [P] Create data subdirectories: `data/raw`, `data/processed`, `data/split`. **Requirement**: Create `.gitkeep` files in all new directories.
- [ ] T003 [P] Create artifacts subdirectories: `artifacts/models`, `artifacts/reports`, `artifacts/figures`. **Requirement**: Create `.gitkeep` files in all new directories.
- [ ] T004 [P] Configure `pyproject.toml` with initial configuration for ruff and black (line-length: a standard maximum limit, rules E, W, F).
- [ ] T005 [P] Create `code/__init__.py` and basic project scaffolding.
- [ ] T006 [P] Generate deterministic synthetic baseline data using `code/generate_synthetic.py` with seed=42 and output `data/raw/synthetic_baseline.csv`. **Schema**: Columns must include `cold_work_pct` (float, 0-100), `Mn_wt` (float), `Mg_wt` (float), `Si_wt` (float), `Cu_wt` (float), `annealing_temp_K` (float), `time_to_peak_min` (float). **Logic**: Use a deterministic physical kinetics model + noise. **Data Hygiene**: MUST compute the SHA-256 checksum of the generated CSV using the `sha256sum` command and write it to `data/raw/synthetic_baseline.csv.sha256` in the format `hash filename` (two spaces). **Versioning**: MUST record this checksum in the project's state YAML (`state/projects/PROJ-240-predicting-the-impact-of-cold-work-on-re.yaml`) under `artifact_hashes`. **Error Handling**: If generation fails, raise `RuntimeError` immediately; do NOT fall back to mock data. **Dataset Cap**: If the requested generation size exceeds 10,000 rows, the generator MUST cap the output at 10000 rows to satisfy FR-003 and Constitution Principle VII.
- [ ] T007 [P] Calculate synthetic baseline statistics and write `artifacts/reports/baseline_stats.json`. **Logic**: Read `data/raw/synthetic_baseline.csv`, calculate the mean of `time_to_peak_min`, and store it as `baseline_mean`. **Requirement**: This file is required for SC-006 (MAE threshold check).
- [ ] T008 [P] Implement orchestration in `code/main.py`. **Logic**: This script must be the single entry point that calls the ingestion, feature engineering, training, and evaluation scripts in sequence. **Requirement**: Must handle errors and exit with non-zero code on failure.
- [ ] T009 [P] Implement dataset size validation in `code/ingest.py`: Raise `ValueError` immediately if the dataset size is < 50 rows (FR-008) to ensure 'fail-fast' behavior. **Requirement**: This check must occur BEFORE any feature engineering or model training.
- [ ] T010 [P] [US1] Generate `artifacts/reports/ingestion_metrics.json` and `artifacts/reports/validation_log.json`. **Schema**: `ingestion_metrics.json` must contain `rows_ingested`, `rows_filtered`, `null_handling_success_rate`. `validation_log.json` must contain `rows_ingested`, `rows_filtered`, `null_counts`, `clipped_outliers_count`, `clipped_values_list`, `threshold_99th_percentile`. **Requirement**: These metrics are required for SC-007.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: User Story 1 - Data Ingestion and Feature Construction (Priority: P1) 🎯 MVP

**Goal**: Ingest raw experimental data (synthetic primary) and transform into a structured dataset with engineered interaction features.

**Independent Test**: The system can be tested by running the data pipeline on the synthetic generator (seed=42) and verifying the output DataFrame contains the required columns, calculated interaction features (`cold_work * Mn_content`, etc.), and no null values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T011 [P] [US1] Write TDD unit test for physical bound validation in `tests/unit/test_validation.py` (test fails initially).
- [ ] T012 [P] [US1] Write TDD unit test for interaction feature engineering in `tests/unit/test_engineering.py` (test fails initially).

### Implementation for User Story 1

- [ ] T013 [US1] Implement orchestration in `code/ingest.py`: Load `data/raw/synthetic_baseline.csv` (from T006) as the PRIMARY and mandatory source. Do NOT attempt to fetch external data in this step. Output `data/processed/validated.csv` and `artifacts/reports/validation_log.json`. **Requirement**: Ensure the dataset size is >= 50 rows (T009) and <= 10000 rows (T006 cap). **Fail-Fast**: If the dataset size is < 50 rows after loading, raise `ValueError` immediately (FR-008) before any further processing.
- [ ] T014 [US1] Implement row filtering for missing "time-to-peak softening" in `code/ingest.py` (exclude rows, do not impute target).
- [ ] T015 [US1] Implement physical bound validation (0 ≤ cold work ≤ 100%, positive time) in `code/ingest.py`.
- [ ] T016 [US1] Implement missing composition value handling in `code/ingest.py`: Impute using the mean of the specific alloy series (group by alloy type or concentration range) or flag for exclusion as per spec Edge Cases. Do NOT use a global mean for all rows.
- [ ] T017 [US1] Implement unit normalization for time-to-peak (minutes) in `code/ingest.py`.
- [ ] T018 [US1] Implement outlier clipping on target variable at 99th percentile in `code/ingest.py` (FR-007) before any statistical analysis. Log clipped values to `artifacts/reports/validation_log.json`. **Requirement**: The clipped data must be the ONLY data used for subsequent statistical tests. **Artifact**: Write `clipped_outliers_count` and `clipped_values_list` to `validation_log.json`.
- [ ] T019 [US1] Implement interaction feature engineering in `code/engineer.py`: Calculate `cold_work * Mn_content`, `cold_work * Mg_content`, `cold_work * Si_content`, `cold_work * Cu_content`. **Constraint**: Do NOT include `cold_work * Temperature`. Use exact column names from T006 (e.g., `cold_work_pct`, `Mn_wt`, `annealing_temp_K`). Include annealing temperature as a direct feature. **Data Cap**: Assume dataset is already capped at 10000 rows by T006/T013. Output `data/processed/engineered_features.csv`.
- [ ] T020 [US1] Generate final dataset artifact `data/processed/final_dataset.csv` ready for modeling.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Predictive Model Training and Validation (Priority: P2)

**Goal**: Train a Random Forest Regressor using CPU-only execution, validate with 5-fold CV, and evaluate on a held-out test set.

**Independent Test**: The system can be tested by running the training script on `data/processed/final_dataset.csv`; it must output a trained model artifact and report mean CV R² score and held-out MAE, completing within 6 hours on 4GB RAM.

**⚠️ DEPENDENCY**: This phase MUST wait for T020 (final_dataset.csv) completion.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Unit test for VIF calculation in `tests/unit/test_vif.py`.
- [ ] T022 [P] [US2] Unit test for model training with small subset in `tests/unit/test_train.py`.

### Implementation for User Story 2

- [ ] T023 [US2] Implement data splitting logic in `code/train.py`: An 80/20 stratified split (train/test) with random seed=42. Stratify on `time_to_peak_min` binned into 5 bins. **Requirement**: Save split indices or ensure reproducibility for use in Phase 4.
- [ ] T024 [US2] Implement Random Forest Regressor training (CPU-only) in `code/train.py`. **Model Type**: Train the **Interaction Model** (full feature set including interactions) to serve as the primary predictive model. Ensure dataset size ≤ 10000 rows (FR-003). Handle pure aluminum (zero variance) gracefully by detecting the condition across the entire dataset and setting a `pure_aluminum_flag: true` in `artifacts/reports/training_metrics.json`, then skipping interaction importance calculation. **Output**: Write `pure_aluminum_flag` as a boolean field in the JSON report. **Requirement**: This task requires T020 completion.
- [ ] T025 [US2] Implement k-fold cross-validation in `code/train.py` and calculate mean R² and std dev.
- [ ] T026 [US2] Implement held-out test set evaluation in `code/train.py`: Calculate MAE and R² on the test set. **Requirement**: Compare MAE against [deferred] of the `baseline_mean` read from `artifacts/reports/baseline_stats.json` (T007).
- [ ] T027 [US2] Save trained model to `artifacts/models/kinetic_model.pkl`. **Format**: Use `pickle` protocol 4 for cross-version compatibility.
- [ ] T028 [US2] Generate `artifacts/reports/training_metrics.json` containing CV scores and test set MAE/R². **Format**: JSON schema must include `cv_r2_mean`, `cv_r2_std`, `test_mae`, `test_r2`, and `pure_aluminum_flag`.
- [ ] T029 [US2] Implement "Pure Aluminum" dataset detection in `code/train.py`: Check if standard deviation of all composition columns (Mn, Mg, Si, Cu) is zero. If so, set `pure_aluminum_flag` to `true` in `artifacts/reports/training_metrics.json` and `artifacts/reports/shap_interaction_report.json` (if applicable) and log a warning. **Requirement**: The `pure_aluminum_flag` must be a structured field in the JSON report, not just a log message, to ensure testability per Edge Cases.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Statistical Significance and Interaction Analysis (Priority: P3)

**Goal**: Statistically verify that interaction terms improve prediction accuracy and identify key drivers via SHAP.

**Independent Test**: The system can be tested by running the analysis script; it must output a p-value from a Permutation Test (p < 0.05) and a SHAP interaction value report.

**⚠️ DEPENDENCY**: This phase MUST wait for T027 (kinetic_model.pkl) completion.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Unit test for Permutation Test logic in `tests/unit/test_permutation.py`.
- [ ] T031 [P] [US3] Unit test for SHAP interaction calculation in `tests/unit/test_shap.py`.

### Implementation for User Story 3

- [ ] T032 [US3] Implement Baseline Model (Additive: cold work + composition, NO interactions) training in `code/evaluate.py` for comparison. **Requirement**: Use the SAME data split (seed=42) as T023 to ensure fair comparison.
- [ ] T033 [US3] Implement Interaction Model (cold work + composition + interactions) training in `code/evaluate.py` (re-use logic from T024 but with full feature set) to ensure consistency for the Delta-Permutation Test. **Requirement**: Use the SAME data split (seed=42) as T023.
- [ ] T034 [US3] Implement Delta-Permutation Test in `code/evaluate.py`:
 1. Train Additive Model (T032) and Interaction Model (T033) on the SAME data split.
 2. Generate error distributions (MAE per fold) for BOTH models using k-fold cross-validation.
 3. **Comparison**: Compare the error distribution of the Additive Model against the error distribution of the Interaction Model (unshuffled) using the Mann-Whitney U test.
 4. Calculate p-value (FR-005) based on the overlap of these two distributions to determine if the interaction terms provide statistically significant improvement. Output to `artifacts/reports/statistical_significance.json`.
- [ ] T035 [US3] Implement Permutation Importance calculation in `code/evaluate.py`: Calculate permutation importance (drop in R² score) for interaction terms and verify > 0.01 threshold (SC-003). Update `artifacts/reports/statistical_significance.json` with key `permutation_importance`.
- [ ] T036 [US3] Implement SHAP Interaction Value analysis in `code/evaluate.py` to rank features by unique contribution (FR-006). **Prerequisites**: `data/processed/engineered_features.csv` (from T019) and `artifacts/models/kinetic_model.pkl` (from T027). **Parameters**: Use `TreeExplainer` with `nsamples=1000` for determinism.
- [ ] T037 [US3] Generate `artifacts/reports/statistical_significance.json` containing p-value, test statistic, and conclusion.
- [ ] T038 [US3] Generate `artifacts/reports/shap_interaction_report.json` with top features and interaction terms. Include `pure_aluminum_flag` status if detected in T029.
- [ ] T039 [US3] Verify Success Criteria:
 1. Check p-value < 0.05 (from T034/T037).
 2. Check Permutation Importance > 0.01 (from T035).
 3. Check R² > 0.6 (SC-001). **Logic**: Read `test_r2` from `artifacts/reports/training_metrics.json`. If R² <= 0.6, flag failure. Do NOT flag if R² > 0.6.
 Flag in report if any criteria fail (do not crash, but document failure).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Documentation updates: Update `README.md` installation steps and `quickstart.md` with a 5-step execution guide.
- [ ] T041 [P] Refactor `code/utils.py` for clarity and performance. **Metric**: Reduce cyclomatic complexity score of `utils.py` functions to < 5 using `radon cc code/utils.py -a`.
- [ ] T042 [P] Refactor `code/ingest.py` to ensure strict error handling on data fetch. **Logic**: If external data fetch fails, proceed with the synthetic dataset already loaded; do not halt. (Note: Synthetic is primary per FR-001).
- [ ] T043 [P] Optimize model training loop in `code/train.py` to ensure <60 min runtime. **Metric**: Reduce training time compared to baseline.
- [ ] T044 [P] Optimize data loading in `code/engineer.py` and `code/evaluate.py`. **Metric**: Reduce memory peak usage via chunking.
- [ ] T045 [P] Write unit tests for `code/utils.py` in `tests/unit/test_utils.py`.
- [ ] T046 [P] Write unit tests for `code/engineer.py` in `tests/unit/test_engineer.py`.
- [ ] T047 [P] Write unit tests for `code/evaluate.py` in `tests/unit/test_evaluate.py`.
- [ ] T048 [P] Security hardening (input sanitization).
- [ ] T049 [P] [Optional] Implement external data fetching logic in `code/ingest_external.py` to attempt fetching from NIST/HuggingFace. **Logic**: If fetch fails, log a warning and proceed with the synthetic dataset already loaded in T006/T013; do NOT halt the pipeline. Synthetic is the primary source per FR-001. Merge external data only if explicitly configured and validated. This task is non-blocking and separate from the primary ingestion flow.
- [ ] T050 [P] Run `quickstart.md` validation to ensure end-to-end execution of the full pipeline (US1 + US2 + US3).

---

## Phase 6: Revision & Analysis Resolution (Post-Analysis)

**Purpose**: Address specific reviewer concerns and ensure strict adherence to the "No Fabrication" and "Real Data" rules.

- [ ] T051 [P] [Review] Ensure T029 correctly flags pure aluminum datasets in the report artifacts. **Requirement**: Verify `pure_aluminum_flag` is present in `training_metrics.json` and `shap_interaction_report.json` when applicable.
- [ ] T052 [P] [Review] Verify T034 implements distribution-based comparison for the Permutation Test. **Requirement**: Confirm the test compares CV error distributions (Additive vs Interaction), not single MAE values.
- [ ] T053 [P] [Review] Verify T019 does not include `cold_work * Temperature`. **Requirement**: Confirm feature engineering strictly follows FR-002.
- [ ] T054 [P] [Review] Verify T006 generates checksums. **Requirement**: Confirm `synthetic_baseline.csv.sha256` exists and is recorded in state YAML.
- [ ] T055 [P] [Review] Verify T049 logic for data source failures. **Requirement**: Confirm that T049 correctly distinguishes between:
 1. **Local Synthetic Generator Failure** (T006): Must raise an error (Fail-Loud).
 2. **External Data Fetch Failure** (T049): Must proceed with synthetic data (Fail-Safe/Fallback).
 Ensure no task requires raising an error for external fetch failures, as this contradicts FR-001 and T049.
- [ ] T056 [P] [Review] Verify T056 (main.py) implementation. **Requirement**: Confirm `code/main.py` exists and correctly orchestrates the pipeline (T006 -> T013 -> T019 -> T024 -> T034).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup & Foundational (Phase 1)**: No dependencies - can start immediately
- **User Stories (Phase 2+)**: All depend on Phase 1 completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision (Phase 6)**: Depends on completion of Phase 5 and analysis feedback

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 1 - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Phase 1 - Depends on final_dataset.csv from US1
- **User Story 3 (P3)**: Can start after Phase 1 - Depends on trained model from US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- Once Phase 1 completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Write TDD unit test for physical bound validation in tests/unit/test_validation.py"
Task: "Write TDD unit test for interaction feature engineering in tests/unit/test_engineering.py"

# Launch all models for User Story 1 together:
Task: "Implement orchestration in code/ingest.py to load synthetic data"
Task: "Implement interaction feature engineering in code/engineer.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup & Foundational
2. Complete Phase 2: User Story 1
3. **STOP and VALIDATE**: Test User Story 1 independently
4. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 1 → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 1 together
2. Once Phase 1 is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All tasks must run on free CPU-only CI (limited cores, constrained RAM, no GPU). No 8-bit/4-bit quantization, no CUDA, no large LLMs.
- **Data Integrity**: Use `code/generate_synthetic.py` for baseline data if real data is unavailable; **synthetic is the PRIMARY source**. If external fetch fails, proceed with synthetic (do not halt).
- **Data Flow**: Ensure data ingestion (US1) completes before model training (US2), and model training completes before validation (US3).
- **Statistical Rigor**: Permutation Test (comparing Additive vs. Interaction models) and SHAP Interaction Values are mandatory for US3 to validate the "pinning effect" hypothesis.
- **Imputation Logic**: Missing composition values must be imputed using the mean of the specific alloy series, not a global mean.
- **Interaction Terms**: Explicitly calculate `cold_work * Mn_content`, `cold_work * Mg_content`, `cold_work * Si_content`, `cold_work * Cu_content`. **Do NOT** calculate `cold_work * Temperature`.
- **Revision Focus**: Phase 6 tasks specifically address the "No Fabrication" rule by ensuring data loaders fail loudly on local generation errors but fall back to synthetic data on external fetch errors, maintaining the synthetic generator as the guaranteed primary source.