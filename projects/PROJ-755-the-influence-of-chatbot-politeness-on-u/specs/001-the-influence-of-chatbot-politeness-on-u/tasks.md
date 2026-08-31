# Tasks: The Influence of Chatbot Politeness on User-Perceived Quality

**Input**: Design documents from `/specs/001-chatbot-politeness-trust/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

<!--
 ============================================================================
 IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

 The /speckit-tasks command MUST replace these with actual tasks based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create data directories: `data/raw`, `data/processed`, `data/models`.
- [ ] T001b [P] Create code directories: `code`, `code/utils`.
- [ ] T001c [P] Create test directories: `tests`, `tests/contract`, `tests/unit`, `tests/integration`.
- [ ] T001d [P] Create documentation directories: `docs`, `state`.
- [ ] T002 Initialize Python project with `requirements.txt` (transformers, datasets, statsmodels, pandas, scikit-learn, numpy, pyyaml, tqdm, rpy2, textstat, evalue, dask, memory_profiler)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools
- [ ] T004 Setup CI workflow (GitHub Actions) to install R-base, R packages (lme4, ordinal), and Python dependencies
- [X] T006 [P] Implement `code/utils/pii_scanner.py` for PII scanning (regex for email, phone, SSN patterns)
- [X] T007 [P] Implement `code/utils/data_integrity.py` for checksumming and data integrity checks
- [ ] T008 [P] Create `contracts/dataset.schema.yaml` defining Dialogue, Utterance, and User entities
- [X] T007b [P] Update `state/projects/PROJ-755-the-influence-of-chatbot-politeness-on-u.yaml` to record checksums in `artifact_hashes.raw_data` key after T007 generates them.
 - *Logic*: Dependency: T007. Must wait for T007 to complete.
- [ ] T010 [P] [Setup] Setup environment configuration management (`.env` template for `HF_TOKEN` if needed).
 - *Logic*: Create `.env.example` with `HF_TOKEN=` placeholder. Document in `README.md` that this is for local development only and that CI secrets must be injected via GitHub Actions environment variables to ensure reproducibility on fresh runners per Constitution Principle I.

**Checkpoint**: Setup ready - Foundational phase can now begin

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure and validation that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. These tasks verify the data exists and meets schema requirements.

- [ ] T009 [P] Create `contracts/output.schema.yaml` defining CLMM results structure
- [ ] T011 [P] [Foundational] Implement `code/utils/schema_validator.py` to validate dataset schemas against `contracts/dataset.schema.yaml`
- [ ] T011b [P] [Foundational] **Proxy Validation**: Verify `quality_rating` as a proxy for trust.
 - *Logic*:
 1. **Action**: Conduct a literature review to identify and cite a specific HCI source validating `quality_rating` in HCI_P2 as a proxy for trust.
 2. **Constraint**: If no source exists, document the limitation explicitly in `research.md`.
 3. **Deliverable**: Update `research.md` with the citation or limitation statement.
 4. **Note**: This task does NOT download data; it is a research task only.
 - *Traceability*: Aligns with Plan Phase 0 Step 6.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Politeness Scoring (Priority: P1) 🎯 MVP

**Goal**: Download **HCI_P2**, **Persona-Chat**, and **EmpatheticDialogues** datasets. Filter for completeness, and compute mean politeness scores per conversation using `jfiedler/politeness-bert` on CPU. 
**Strict Abort Logic**: The pipeline MUST proceed with any dataset that has the required `quality_rating` variable. The pipeline MUST ONLY abort if ALL three datasets fail to download OR ALL three datasets are downloaded but lack the `quality_rating` variable. If a dataset is downloaded but lacks the variable, it is excluded from the merged set, and the pipeline continues with the remaining valid datasets. If only one dataset is valid, proceed with that one.

**Independent Test**: Run `code/01_download_and_score.py` on a sample of dialogues; verify `data/processed/scored_dialogues.parquet` exists with `politeness_score` and `quality_rating` columns, and that excluded dialogues are logged.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T013 [P] [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py`
- [X] T014 [P] [US1] Unit test for politeness scoring logic (batched inference) in `tests/unit/test_scoring.py`

### Implementation for User Story 1

- [ ] T015 [US1] Implement `code/01_download_and_score.py` to fetch **HCI_P2**.
 - *Logic*:
 1. **Attempt FR-001 Source**: Download `HuggingFaceH4/hci_p2` from HuggingFace.
 2. **Verify & Filter**:
    - Check for `quality_rating`, `user_id`, `dialogue_id`.
    - **Exclusion Logic**: If `quality_rating` is missing, log exclusion of HCI_P2 and set status to "excluded".
    - **Abort Condition**: If HCI_P2 is the ONLY source and it is excluded, the pipeline aborts with "NO_VALID_DATA_SOURCE".
 3. **Store**: Save raw data in `data/raw/hci_p2/` with checksums.
 4. **Output**: Update `data/raw/validation_status.json` with `status: "valid" | "excluded"`.
 - *Deliverable*: Raw HCI_P2 data in `data/raw/hci_p2/` or exclusion log.
- [ ] T015b [US1] Implement `code/01_download_and_score.py` to fetch **Persona-Chat**.
 - *Logic*:
 1. **Attempt FR-001 Source**: Download `Persona-Chat` from HuggingFace.
 2. **Verify & Filter**:
    - Check for `quality_rating`, `user_id`, `dialogue_id`.
    - **Exclusion Logic**: If `quality_rating` is missing, log exclusion of Persona-Chat and set status to "excluded". **Do NOT** attempt to derive synthetic ratings.
    - **Abort Condition**: If Persona-Chat is the ONLY source and it is excluded, the pipeline aborts with "NO_VALID_DATA_SOURCE".
 3. **Store**: Save raw data in `data/raw/persona_chat/` with checksums.
 4. **Output**: Update `data/raw/validation_status.json` with `status: "valid" | "excluded"`.
 - *Deliverable*: Raw Persona-Chat data in `data/raw/persona_chat/` or exclusion log.
- [ ] T015c [US1] Implement `code/01_download_and_score.py` to fetch **EmpatheticDialogues**.
 - *Logic*:
 1. **Attempt FR-001 Source**: Download `EmpatheticDialogues` from HuggingFace.
 2. **Verify & Filter**:
    - Check for `quality_rating`, `user_id`, `dialogue_id`.
    - **Exclusion Logic**: If `quality_rating` is missing, log exclusion of EmpatheticDialogues and set status to "excluded". **Do NOT** attempt to derive synthetic ratings.
    - **Abort Condition**: If EmpatheticDialogues is the ONLY source and it is excluded, the pipeline aborts with "NO_VALID_DATA_SOURCE".
 3. **Store**: Save raw data in `data/raw/empathetic_dialogues/` with checksums.
 4. **Output**: Update `data/raw/validation_status.json` with `status: "valid" | "excluded"`.
 - *Deliverable*: Raw EmpatheticDialogues data in `data/raw/empathetic_dialogues/` or exclusion log.
- [ ] T019 [US1] Implement filtering logic to exclude dialogues missing `quality_rating` or chatbot utterances (log counts).
 - *Logic*:
 1. **Dependency**: T015, T015b, T015c.
 2. **Check**: Verify `data/raw/validation_status.json` reflects the status of all three sources.
 3. **Filter**: Filter all available datasets for completeness.
 4. **Log**: Log counts of excluded dialogues per source.
 5. **Store**: Save filtered data to `data/raw/filtered/`.
 - *Deliverable*: Filtered raw dataset in `data/raw/filtered/`.
- [ ] T018 [US1] Implement **Schema Definition, Transformation, and Merge** for all datasets.
 - *Logic*:
 1. **Dependency**: T019.
 2. **Define Schema**: Define target schema (user_id, dialogue_id, quality_rating, age, gender, utterances, source_dataset).
 3. **Transform**: Transform filtered datasets to match schema.
 4. **Merge**: Merge all valid sources into `data/processed/merged_dialogues.parquet`.
 - *Deliverable*: `data/processed/merged_dialogues.parquet`.
- [ ] T020 [US1] Implement **Politeness Scoring** (Load, Inference, Error Handling, Save).
 - *Logic*:
 1. **Dependency**: T018.
 2. Load `jfiedler/politeness-bert` (Revision: `main`, Cache: `data/models`).
 3. Verify model file size ≤ 100MB. **Proceed with batch processing** if larger (do not abort).
 4. Iterate through utterances in batches with dynamic batch sizing.
 5. Compute politeness scores; assign NaN to failures and log counts.
 6. Compute `mean_politeness_score` per dialogue.
 7. **Standardize Globally**:
    - If dataset fits in memory (< 6GB): Calculate global mean/std using `pandas` and apply z-scoring.
    - If dataset is large (> 6GB): Use `dask.dataframe` to stream data, compute global mean/std in two passes (first pass to compute stats, second to apply), and apply z-scoring.
 8. Save to `data/processed/scored_dialogues.parquet`.
 9. **Verify**: Ensure `data/processed/scored_dialogues.parquet` exists and contains `mean_politeness_score` column.
 - *Note*: Input is merged dataset from T018.
 - *Deliverable*: `data/processed/scored_dialogues.parquet`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: Data Verification Gate (Pre-US3)

**Purpose**: Validate sample sizes for subgroup analysis before attempting US3. This task must pass for US3 to proceed.

- [ ] T012 [P] [Gate] **Sample Size Verification** for Subgroups and Primary Analysis.
 - *Logic*:
 1. **Dependency**: T018 (Merge).
 2. Load the **merged** dataset (`data/processed/merged_dialogues.parquet`).
 3. **Check Subgroups**: Count dialogues per `age` group and `gender` group.
 4. **Gate Condition**: If ANY subgroup (e.g., Male, Female, Age 18-25) has n < 30, log that US3 will be skipped for that specific group. **Do NOT** halt the pipeline for the main analysis.
 5. Generate `data/processed/validation_report.json` with schema:
 ```json
 {
 "status": "full" | "partial" | "missing_demographics",
 "demographic_completeness_pct": 0.0,
 "total_sample_size": 500,
 "primary_analysis_valid": true,
 "missing_fields": [],
 "subgroup_counts": { "male": 500, "female": 480, "age_18_25": 200,... },
 "subgroups_eligible": ["male", "female", "age_18_25"],
 "subgroups_excluded": [],
 "gate_status": "passed"
 }
 ```
 - *Deliverable*: `data/processed/validation_report.json`.
 - *Note*: This task gates US3. It must run after data download (T015, T015b, T015c) and merging (T018).

**Checkpoint**: Data verified - US3 can proceed if gate passes

---

## Phase 5: User Story 2 - Cumulative Link Mixed-Effects Analysis (Priority: P2)

**Goal**: Fit a CLMM testing the association between politeness and quality ratings, controlling for length and user random effects, with multiple-comparison correction.

**Independent Test**: Run `code/02_fit_clmm.py` on `scored_dialogues.parquet`; verify `data/processed/clmm_results.csv` contains coefficients, p-values, and that fallback to fixed-effects is logged if CLMM fails.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US2] Unit test for VIF calculation and collinearity check in `tests/unit/test_collinearity.py`
- [X] T024 [P] [US2] Integration test for CLMM execution and result schema validation in `tests/integration/test_clmm.py`

### Implementation for User Story 2

- [X] T025 [US2] Implement `code/02_fit_clmm.py` to load `scored_dialogues.parquet`
- [ ] T026 [US2] Implement VIF check for `politeness` and `conversation_length`; log warning and drop variable if VIF ≥ 5.
- [ ] T027a [US2] **CLMM Fitting**: Fit primary CLMM and record convergence status.
 - *Logic*:
 1. **Dependency**: T026.
 2. Fit CLMM via `rpy2` (formula: `quality_rating ~ politeness + conversation_length + (1|user_id)`) with `lme4`.
 3. **Extract Convergence Status**: Calculate convergence status for the fitted model.
 4. **Record Status**: Save `data/processed/project_status.json` with fields: `convergence_status` ("success" | "failed"), `model_type` ("clmm"), `error_message` (if failed), `timestamp`.
 5. **Save Results**: Save results (CLMM only) to `data/processed/clmm_primary_results.csv` with coefficients, SEs, p-values, CI, and convergence metrics.
 6. **Save Model Object**: Save the fitted model object to `data/processed/clmm_model.pkl` (pickle protocol 5) for later prediction.
 - *Note*: This task ONLY fits the primary model. No fallback logic here.
 - *Deliverable*: `data/processed/clmm_primary_results.csv`, `data/processed/project_status.json`, and `data/processed/clmm_model.pkl`.
- [ ] T027b [US2] **Sensitivity Analysis**: Sweep significance thresholds.
 - *Logic*:
 1. **Dependency**: T027a.
 2. **Action**: Re-calculate p-value significance for a range of conventional thresholds using the primary model results.
 3. **Output**: Save to `data/processed/sensitivity_analysis.json` with counts of significant effects at each threshold.
 - *Note*: This replaces the removed bootstrap convergence analysis.
 - *Deliverable*: `data/processed/sensitivity_analysis.json`.
- [ ] T027d [US2] **Immediate Fallback**: If primary CLMM fails to converge (T027a), fit fixed-effects ordinal regression.
 - *Logic*:
 1. **Dependency**: T027a.
 2. **Check**: If `data/processed/project_status.json` indicates `convergence_status: "failed"`.
 3. **Fit Fallback**: Fit fixed-effects ordinal regression (remove random effects).
 4. **Merge Results**: Append fallback results to `data/processed/clmm_primary_results.csv` (or create it if it doesn't exist) with a `model_type` column set to "ordinal_fixed_effects".
 5. **Log**: Record in `project_status.json` that fallback was used.
 - *Note*: This task handles the immediate per-model failure case as per Spec Edge Cases.
 - *Deliverable*: Updated `data/processed/project_status.json` and `data/processed/clmm_primary_results.csv`.
- [ ] T028 [US2] Implement Benjamini-Hochberg correction for p-values across fixed effects.
 - *Logic*:
 1. **Dependency**: T027a, T027d.
 2. **Selection Logic**:
 - **Default**: Use Benjamini-Hochberg (BH) correction.
 - **Switch Condition**: If the number of hypothesis tests (N) <= 3, switch to **Bonferroni** correction.
 - **Rationale**: This satisfies FR-004's "Bonferroni or Benjamini-Hochberg" requirement with a deterministic rule, avoiding subjective "deemed unsuitable" judgments.
 3. **Apply Correction**: Apply the selected method to the p-values of all fixed effects.
 4. **Save**: Update `data/processed/clmm_primary_results.csv` with corrected p-values.
 - *Deliverable*: Updated `data/processed/clmm_primary_results.csv`.
- [ ] T029 [US2] **Consolidate and Save Results**: Save final results to `data/processed/clmm_results.csv`.
 - *Logic*:
 1. **Dependency**: T028, T027d.
 2. Consolidate results from T027a/T027d (if fallback used) into a single file.
 3. Apply corrections.
 4. Save to `data/processed/clmm_results.csv`.
 - *Note*: This task ensures the final file is written after all corrections.
 - *Deliverable*: `data/processed/clmm_results.csv`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 6: User Story 3 - Robustness and Subgroup Analysis (Priority: P3)

**Goal**: Validate findings with the **textstat (politeness/afinn)** classifier (per Constitution/Plan) AND the **LIWC-2015** dictionary (per FR-005, with mandatory acquisition attempt), and conduct subgroup analyses by age/gender (n ≥ 30 guard).

**Independent Test**: Run `code/03_robustness_analysis.py`; verify `data/processed/robustness_results.csv` exists, correlation (r ≥ 0.80) is calculated, and subgroup exclusions are logged.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US3] Unit test for lexicon-based scoring logic in `tests/unit/test_lexicon_scoring.py`
- [X] T031 [P] [US3] Integration test for subgroup filtering logic (n ≥ 30) in `tests/integration/test_subgroup.py`

### Implementation for User Story 3

- [ ] T032 [US3] **Robustness Classifier (Primary)**: Implement `code/03_robustness_analysis.py` to re-score dialogues using **textstat**.
 - *Logic*:
 1. **Dependency**: T020 (Completion of US1). Load `scored_dialogues.parquet`.
 2. **Primary**: Use **textstat (politeness/afinn lexicon)** as the primary robustness tool (Constitution/Plan compliant).
 3. **Rationale**: Explicitly exclude LIWC-2015 due to proprietary licensing constraints (Constitution Principle II) in this step, but FR-005 is handled in T032c.
 4. Log the classifier used.
 - *Dependency*: T020.
 - *Traceability*: Explicitly satisfies **FR-005** (Robustness) using the approved open-source alternative.
 - *Note*: textstat is the primary requirement per Plan/Constitution.
- [ ] T032b [US3] **textstat Implementation**: Ensure textstat dictionary is loaded and applied.
 - *Logic*:
 1. **Dependency**: T032.
 2. Load textstat `politeness` or `afinn` lexicon.
 3. Apply to utterances.
 4. **Deliverable**: Save scores to `data/processed/robustness_scores_textstat.parquet` with schema: `dialogue_id`, `utterance_id`, `text`, `politeness_score`.
 - *Deliverable*: textstat-based politeness scores.
- [ ] T032c [US3] **Robustness Classifier (LIWC-2015)**: Attempt to acquire and use **LIWC-2015**.
 - *Logic*:
 1. **Dependency**: T020, T032.
 2. **Check**: Attempt to load LIWC-2015 from `data/models/liwc_2015/liwc_2015_dictionary.txt`.
 3. **Acquisition**: If missing, attempt to acquire via `huggingface_hub.hf_hub_download` (repo: "liwc/liwc-2015" or verified wrapper) or `pip install liwc`.
 4. **Mandatory Requirement**:
 - **If Acquisition Fails**: Log WARNING "LIWC-2015 Acquisition Failed. FR-005 Partially Met (textstat used)." and **SKIP** the LIWC-specific analysis. Do NOT abort.
 - **If Available**: Load LIWC-2015. Apply to utterances. Compute scores.
 5. **Comparison (If Available)**: Re-fit CLMM using LIWC scores. Extract coefficient estimates. Compare coefficients (diff/correlation) against primary model (T029). Save comparison results to `data/processed/liwc_comparison.json`.
 6. **Deliverable**: Save scores to `data/processed/robustness_scores_liwc.parquet` (if successful) or log skip.
 - *Traceability*: Explicitly addresses **FR-005** (LIWC-2015 requirement) as a best-effort check.
- [ ] T033 [US3] **Re-fit CLMM**: Re-fit CLMM on lexicon scores.
 - *Dependency*: Requires T032b (textstat) as primary input. T032c (LIWC) is optional.
 - *Logic*:
 1. **Check**: If `data/processed/robustness_scores_textstat.parquet` exists, use it.
 2. **Optional**: If `data/processed/robustness_scores_liwc.parquet` exists, use it for a secondary run.
 3. **Fit**: Re-fit CLMM using the new lexicon-based politeness scores.
 4. **Save**: Save model object to `data/processed/robustness_model.pkl` (pickle protocol 5).
 - *Dependency*: T032b.
- [ ] T033b [US3] **Generate Predicted Scores & Correlate**: Calculate **Spearman** rank correlation of per-dialogue predicted quality scores.
 - *Logic*:
 1. **Dependency**: T033 AND T029 (Primary Results).
 2. Load `data/processed/clmm_model.pkl` (from T027a) for **primary** predictions.
 3. Load `data/processed/robustness_model.pkl` (from T033) for **robust** predictions.
 4. Generate `predicted_quality` scores for each dialogue using both models.
 5. Save per-dialogue predictions to `data/processed/robustness_predictions.csv` (columns: `dialogue_id`, `primary_predicted`, `robust_predicted`).
 6. Calculate **Spearman rank correlation** `correlation_r` between `primary_predicted_quality` and `robust_predicted_quality`.
 7. **Calculate P-value and N**: Compute the p-value and sample size (N) for the correlation.
 8. **Rationale**: Spearman is used for ordinal data consistency (Likert 1-5) to match SC-004 intent.
 9. **Verify**: Check if `correlation_r` >= 0.80. Log "SC-004 MET" or "SC-004 NOT MET".
 10. Save `correlation_r`, `p_value`, and `n` to `data/processed/robustness_summary.json` (keys: `correlation_r`, `p_value`, `n`).
 - *Note*: Explicitly generate per-dialogue predicted quality scores via CLMM prediction before correlation calculation.
 - *Dependency*: T033, T029.
- [ ] T034 [US3] **Subgroup Analysis**: Split data by age/gender.
 - *Dependency*: Requires T012 (Sample Size Verification) to have reported `subgroups_eligible`. **Also requires T020 (US1 completion)**.
 - *Logic*:
 1. **Check Columns**: If `age` or `gender` columns are missing, log "Subgroup analysis skipped: missing demographic columns" and exit.
 2. **Filter**: Exclude groups with n < 30 (as per T012), log exclusions.
 3. **Fit**: Fit separate CLMMs for valid subgroups and test interaction terms.
 4. **Output**: Save each subgroup model to `data/processed/subgroup_clmm_{group}.csv`.
 - *Deliverable*: `data/processed/subgroup_clmm_{group}.csv` files.
- [ ] T035 [US3] Apply multiplicity correction for subgroup tests.
- [ ] T037 [US3] Save all robustness results to `data/processed/robustness_results.csv`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038a [P] Update `README.md` with project overview, installation instructions, and usage examples.
- [ ] T038b [P] Update `docs/quickstart.md` with a step-by-step guide to running the full pipeline.
- [ ] T038c [P] Update `docs/data-model.md` with entity definitions and data flow diagrams.
- [ ] T039 Code cleanup and refactoring (remove debug prints, ensure type hints)
- [ ] T040 [P] Performance optimization: verify memory usage < 7GB during peak BERT inference using `memory_profiler`.
 - *Logic*:
 1. Decorate the BERT inference function in `code/01_download_and_score.py` with `@profile` from `memory_profiler`.
 2. Run the function on a full batch.
 3. Check peak memory usage from output.
 4. If > 7GB, log error "MEMORY_EXCEEDED" and suggest batch size reduction.
 - *Deliverable*: `data/processed/memory_profile.log`.
- [ ] T041 [P] Additional unit tests for edge cases (empty dialogues, NaN handling) in `tests/unit/`
- [ ] T042 [P] Configure CI workflow for full pipeline execution on GitHub Actions.
 - *Logic*: Create `.github/workflows/ci.yml` to install R, Python deps, and run the full pipeline.
- [ ] T042b [P] Execute full pipeline on GitHub Actions and capture metrics.
 - *Logic*: Run the CI workflow. Verify runtime < 6h and RAM < 7GB. Capture metrics.
 - *Dependency*: T042.
 - *Deliverable*: `data/processed/performance_metrics.json`.
- [ ] T043 [P] Generate `docs/performance_report.md` with explicit schema.
 - *Schema*: `runtime_seconds`, `peak_memory_gb`, `convergence_rate`, `status`.
 - *Logic*: Collect metrics from `data/processed/performance_metrics.json` (generated by T042b).
 - *Dependency*: T042b.
 - *Deliverable*: `docs/performance_report.md`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - **BLOCKS** all user stories.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires output from US1 (`scored_dialogues.parquet`)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires output from US1 and US2 for comparison. **Explicitly depends on T012 passing (or partial status with available fields).**

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for dataset schema validation in tests/contract/test_dataset_schema.py"
Task: "Unit test for politeness scoring logic in tests/unit/test_scoring.py"

# Launch all models for User Story 1 together:
Task: "Implement code/01_download_and_score.py to fetch HCI_P2"
Task: "Implement filtering logic to exclude dialogues missing quality_rating"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories, includes T012 verification)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3 (Only if T012 passes or partial status available)
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
- **Constraint**: All BERT inference must be CPU-only (no CUDA); use batch processing to stay under available RAM limits.
- **Constraint**: Dataset source MUST include HCI_P2, Persona-Chat, and EmpatheticDialogues. Abort only if ALL three fail.
- **Constraint**: Subgroup analysis (US3) is strictly gated by T012 (Sample Size Verification, n ≥ 30).
- **Constraint**: Robustness classifier (T032) MUST use **textstat** (open-source) as primary; LIWC-2015 is handled in T032c with a best-effort acquisition gate.
- **Constraint**: Convergence rate (SC-003) is measured by the primary run's convergence status.