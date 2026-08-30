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

## Phase 0: Research & Pilot (New - Pre-Pipeline)

**Purpose**: Execute Plan Phase 0 requirements (Pilot, MDE, Proxy Validation) BEFORE the main data pipeline.

- [ ] T011a [P] [Research] **Download Raw Sample for Pilot**: Download a small, raw subset of HCI_P2 for pilot analysis.
 - *Logic*:
 1. **Source**: Download `HuggingFaceH4/hci_p2` from HuggingFace.
 2. **Sample**: Extract a small representative subset (e.g., a fixed number of dialogues) using a fixed seed.
 3. **Store**: Save raw sample to `data/raw/pilot_sample/`.
 4. **Constraint**: Do NOT apply filtering or schema transformation yet. This is raw data for the pilot.
 - *Deliverable*: `data/raw/pilot_sample/`.
- [ ] T011b [P] [Research] **Initialize research.md**: Create `research.md` with project metadata and section headers.
 - *Logic*:
 1. **Create `research.md` if it does not exist**.
 2. Add section headers: 'Pilot_Results', 'MDE_Estimation', 'Proxy_Validation'.
 - *Deliverable*: `research.md`.
- [ ] T011b1 [P] [Research] **Data Sampling**: Extract a representative sample from the raw pilot data for pilot analysis.
 - *Logic*:
 1. **Dependency**: T011a.
 2. Load raw data from `data/raw/pilot_sample/`.
 3. Sample a representative subset of rows using a fixed seed.
 4. Save to `data/processed/pilot_sample.parquet`.
 - *Deliverable*: `data/processed/pilot_sample.parquet`.
- [ ] T011b2 [P] [Research] **Pilot Model Fitting**: Fit a simplified model on the sample to estimate effect size.
 - *Logic*:
 1. **Dependency**: T011b1.
 2. Fit a basic ordinal regression on the sample.
 3. Save model object to `data/processed/pilot_model.pkl`.
 - *Deliverable*: `data/processed/pilot_model.pkl`.
- [ ] T011b3 [P] [Research] **MDE Calculation & Output**: Calculate Minimum Detectable Effect (MDE) and generate report.
 - *Logic*:
 1. **Dependency**: T011b2.
 2. Calculate MDE based on pilot results and full sample size.
 3. Generate `data/processed/pilot_mde_results.json` with fields: `minimum_detectable_effect`, `power`, `sample_size`.
 - *Deliverable*: `data/processed/pilot_mde_results.json`.
- [ ] T011c [P] [Research] Update `research.md` with MDE estimation results.
 - *Logic*:
 1. **Dependency**: T011b3, T011b.
 2. Read `data/processed/pilot_mde_results.json` and append section 'MDE_Estimation' to `research.md`.

**Checkpoint**: Research phase complete - Main pipeline can now begin

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create project directory structure: `data/raw`, `data/processed`, `code`, `code/utils`, `tests`, `tests/contract`, `tests/unit`, `tests/integration`, `docs`, `state`.
- [ ] T001b [P] Initialize `.gitkeep` files in data directories and create `.gitignore` to exclude `data/raw/*`, `data/processed/*`, `__pycache__`, and model caches.
- [X] T002 Initialize Python project with `requirements.txt` (transformers, datasets, statsmodels, pandas, scikit-learn, numpy, pyyaml, tqdm, rpy2, textstat, evalue, liwc)
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

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Politeness Scoring (Priority: P1) 🎯 MVP

**Goal**: Download **HCI_P2** dataset. Filter for completeness, and compute mean politeness scores per conversation using `jfiedler/politeness-bert` on CPU. (Note: Persona-Chat and EmpatheticDialogues are attempted only if HCI_P2 fails the stop condition).

**Independent Test**: Run `code/01_download_and_score.py` on a sample of dialogues; verify `data/processed/scored_dialogues.parquet` exists with `politeness_score` and `quality_rating` columns, and that excluded dialogues are logged.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T013 [P] [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py`
- [X] T014 [P] [US1] Unit test for politeness scoring logic (batched inference) in `tests/unit/test_scoring.py`

### Implementation for User Story 1

- [X] T015 [US1] Implement `code/01_download_and_score.py` to fetch **HCI_P2**.
 - *Logic*:
 1. **Source**: Download `HuggingFaceH4/hci_p2` from HuggingFace (Verify exact ID in Phase 0).
 2. **Verify**: Confirm presence of `quality_rating`, `user_id`, `dialogue_id`.
 3. **Store**: Save raw data in `data/raw/hci_p2/` with checksums.
 4. **Output**: Generate `data/raw/hci_p2/validation_status.json` with `is_valid: true/false`.
 - *Deliverable*: Raw data stored in `data/raw/hci_p2/` and validation status.
- [ ] T015a [US1] **HCI_P2 Validation**: Verify HCI_P2 validity for downstream tasks.
 - *Logic*:
 1. **Dependency**: T015.
 2. Read `data/raw/hci_p2/validation_status.json`.
 3. If `is_valid` is true, mark as `HCI_P2_VALID`.
 4. If `is_valid` is false, mark as `HCI_P2_INVALID`.
 - *Deliverable*: `HCI_P2_VALID` or `HCI_P2_INVALID` flag.
- [ ] T015b_trigger [US1] **Fallback Trigger**: Determine if secondary datasets should be attempted.
 - *Logic*:
 1. **Dependency**: T015a.
 2. If `HCI_P2_VALID`, set `SKIP_SECONDARY=true`.
 3. If `HCI_P2_INVALID`, set `SKIP_SECONDARY=false`.
 - *Deliverable*: `SKIP_SECONDARY` flag.
- [ ] T015b [US1] **Conditional (Fallback)**: Download Persona-Chat dataset (Only if HCI_P2 is invalid).
 - *Logic*:
 1. **Dependency**: T015b_trigger.
 2. **Skip Condition**: If `SKIP_SECONDARY` is true, log "SKIPPED: HCI_P2 is valid" and exit.
 3. **Source**: Attempt to fetch `HuggingFaceM4/Persona-Chat`.
 4. **Pre-flight Check**: List metadata to verify presence of `quality_rating`.
 5. **Stop Condition**: If `quality_rating` is missing, log "SKIPPED: Field missing per Plan Phase 0" and exit gracefully.
 6. **Store**: If fields present, save raw data in `data/raw/persona_chat/` with checksums.
 - *Deliverable*: Raw data stored in `data/raw/persona_chat/` OR log of skipped download.
- [ ] T015c [US1] **Conditional (Fallback)**: Download EmpatheticDialogues dataset (Only if HCI_P2 is invalid).
 - *Logic*:
 1. **Dependency**: T015b_trigger.
 2. **Skip Condition**: If `SKIP_SECONDARY` is true, log "SKIPPED: HCI_P2 is valid" and exit.
 3. **Source**: Attempt to fetch `HuggingFaceM4/EmpatheticDialogues`.
 4. **Pre-flight Check**: List metadata to verify presence of `quality_rating`.
 5. **Stop Condition**: If `quality_rating` is missing, log "SKIPPED: Field missing per Plan Phase 0" and exit gracefully.
 6. **Store**: If fields present, save raw data in `data/raw/empathetic_dialogues/` with checksums.
 - *Deliverable*: Raw data stored in `data/raw/empathetic_dialogues/` OR log of skipped download.
- [ ] T019 [US1] Implement filtering logic to exclude dialogues missing `quality_rating` or chatbot utterances (log counts).
 - *Logic*:
 1. **Dependency**: T015, T015b, T015c.
 2. Filter **all available** datasets for completeness.
 3. Log counts of excluded dialogues.
 - *Deliverable*: Filtered raw datasets in `data/raw/filtered/`.
- [ ] T018 [US1] Implement **Schema Definition, Transformation, and Merge** for all available datasets.
 - *Logic*:
 1. **Dependency**: T019.
 2. Define the target schema for all datasets (user_id, dialogue_id, quality_rating, age, gender, utterances, source_dataset).
 3. Transform the filtered datasets to match this schema.
 4. Merge into a single file.
 5. Save as `data/processed/merged_dialogues.parquet`.
 - *Deliverable*: `data/processed/merged_dialogues.parquet`.
- [ ] T020 [US1] Implement **Politeness Scoring** (Load, Inference, Error Handling).
 - *Logic*:
 1. **Dependency**: T018.
 2. Load `jfiedler/politeness-bert` (Revision: `main`, Cache: `data/models`).
 3. Verify model file size ≤ 100MB. **Proceed with batch processing** if larger (do not abort).
 4. Iterate through utterances in batches with dynamic batch sizing.
 5. Compute politeness scores; assign NaN to failures and log counts.
 6. Compute `mean_politeness_score` per dialogue.
 7. **Standardize Globally**: Calculate the global mean and standard deviation of all `mean_politeness_score` values across the entire merged dataset. Apply z-scoring using these global statistics to produce `standardized_politeness_score`.
 8. Save to `data/processed/scored_dialogues.parquet`.
 - *Note*: Input is all available processed datasets.
 - *Deliverable*: `data/processed/scored_dialogues.parquet`.
- [ ] T021 [US1] Save processed data to `data/processed/scored_dialogues.parquet` and raw logs to `data/raw/exclusions.log`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: Data Verification Gate (Pre-US3)

**Purpose**: Validate sample sizes for subgroup analysis before attempting US3. This task must pass for US3 to proceed.

- [ ] T012 [P] [Gate] **Sample Size Verification** for Subgroups and Primary Analysis.
 - *Logic*:
 1. **Dependency**: T018 (Merge).
 2. Load the **merged** dataset (`data/processed/merged_dialogues.parquet`).
 3. **Check Completeness**: Verify that ≥ 80% of dialogues have `age` and `gender` metadata. If < 80%, log critical failure and halt US3.
 4. **Check Subgroups**: Count dialogues per `age` group and `gender` group.
 5. **Gate Condition**: If ANY subgroup (e.g., Male, Female, Age 18-25) has n < 30, log that US3 will be skipped for that specific group. **Do NOT** halt the pipeline for the main analysis.
 6. Generate `data/processed/validation_report.json` with schema:
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
 "gate_status": "passed" | "failed_80pct"
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
 4. **Record Status**: Save `project_status.json` with fields: `convergence_status` ("success" | "failed"), `model_type` ("clmm").
 5. **Save Results**: Save results (CLMM only) to `data/processed/clmm_primary_results.csv` with coefficients, SEs, p-values, CI, and convergence metrics.
 - *Note*: This task ONLY fits the primary model. No fallback logic here.
 - *Deliverable*: `data/processed/clmm_primary_results.csv` and `data/processed/project_status.json`.
- [ ] T027b [US2] **Evaluate Convergence & Fallback**: Check convergence rate and execute fallback if needed.
 - *Logic*:
 1. **Dependency**: T027a.
 2. Read `project_status.json` from T027a.
 3. **Measure SC-003**: Evaluate if convergence rate meets ≥ 95%. If not, log that SC-003 is **NOT MET** for the primary model.
 4. **Fallback Strategy**: If convergence < 95%, **DO NOT halt**. Instead, attempt fallback to fixed-effects ordinal regression (remove random effects) and log diagnostic.
 5. **Record Status**: Update `project_status.json` with fields: `status` ("success" | "fallback_used"), `sc003_met` (boolean), `sc003_note` (if failed, explain fallback).
 6. **Save Results**: If fallback used, save results to `data/processed/clmm_fallback_results.csv`.
 - *Note*: This task handles the fallback logic based on T027a's result.
 - *Deliverable*: Updated `data/processed/project_status.json` and fallback results if applicable.
- [ ] T028 [US2] Implement Benjamini-Hochberg correction for p-values across fixed effects.
- [ ] T029 [US2] **Consolidate and Save Results**: Save final results to `data/processed/clmm_results.csv`.
 - *Logic*:
 1. **Dependency**: T028, T027b.
 2. Consolidate results from T027a/T027b.
 3. Apply corrections.
 4. Save to `data/processed/clmm_results.csv`.
 - *Note*: This task ensures the final file is written after all corrections.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 6: User Story 3 - Robustness and Subgroup Analysis (Priority: P3)

**Goal**: Validate findings with the **textstat (politeness/afinn)** classifier (per Constitution/Plan) and conduct subgroup analyses by age/gender (n ≥ 30 guard).

**Independent Test**: Run `code/03_robustness_analysis.py`; verify `data/processed/robustness_results.csv` exists, correlation (r ≥ 0.80) is calculated, and subgroup exclusions are logged.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US3] Unit test for lexicon-based scoring logic in `tests/unit/test_lexicon_scoring.py`
- [X] T031 [P] [US3] Integration test for subgroup filtering logic (n ≥ 30) in `tests/integration/test_subgroup.py`

### Implementation for User Story 3

- [ ] T032 [US3] **Robustness Classifier (Primary)**: Implement `code/03_robustness_analysis.py` to re-score dialogues using **textstat**.
 - *Logic*:
 1. **Dependency**: T021 (Completion of US1). Load `scored_dialogues.parquet`.
 2. **Primary**: Use **textstat (politeness/afinn lexicon)** as the primary robustness tool (Constitution/Plan compliant).
 3. **Rationale**: Explicitly exclude LIWC-2015 due to proprietary licensing constraints (Constitution Principle II). This satisfies **FR-005** (Robustness) using the approved open-source alternative.
 4. Log the classifier used.
 - *Dependency*: T021.
 - *Traceability*: Explicitly satisfies **FR-005** (Robustness) using the approved open-source alternative.
 - *Note*: textstat is the primary requirement per Plan/Constitution.
- [ ] T032b [US3] **textstat Implementation**: Ensure textstat dictionary is loaded and applied.
 - *Logic*:
 1. **Dependency**: T032.
 2. Load textstat `politeness` or `afinn` lexicon.
 3. Apply to utterances.
 - *Deliverable*: textstat-based politeness scores.
- [ ] T033 [US3] **Re-fit CLMM**: Re-fit CLMM on lexicon scores.
 - *Logic*:
 1. **Dependency**: T032b.
 2. Re-fit CLMM using the new lexicon-based politeness scores.
 3. Save model object to `data/processed/robustness_model.pkl`.
 - *Dependency*: T032b.
- [ ] T033b [US3] **Generate Predicted Scores & Correlate**: Calculate **Spearman** rank correlation of per-dialogue predicted quality scores.
 - *Logic*:
 1. **Dependency**: T033 AND T029 (Primary Results).
 2. Generate `predicted_quality` scores for each dialogue using the primary CLMM (expected value of ordinal outcome) and the robust CLMM.
 3. Save per-dialogue predictions to `data/processed/robustness_predictions.csv` (columns: `dialogue_id`, `primary_predicted`, `robust_predicted`).
 4. Calculate **Spearman rank correlation** `correlation_r` between `primary_predicted_quality` and `robust_predicted_quality`.
 5. **Rationale**: Spearman is used for ordinal data consistency (Likert 1-5) to match SC-004 intent.
 6. **Verify**: Check if `correlation_r` >= 0.80. Log "SC-004 MET" or "SC-004 NOT MET".
 7. Save `correlation_r` to `data/processed/robustness_summary.json` (key: `correlation_r`).
 - *Note*: Explicitly generate per-dialogue predicted quality scores via CLMM prediction before correlation calculation.
 - *Dependency*: T033, T029.
- [ ] T034 [US3] **Subgroup Analysis**: Split data by age/gender.
 - *Dependency*: Requires T012 (Sample Size Verification) to have reported `subgroups_eligible`. **Also requires T021 (US1 completion)**.
 - *Logic*:
 1. **Check Columns**: If `age` or `gender` columns are missing, log "Subgroup analysis skipped: missing demographic columns" and exit.
 2. **Filter**: Exclude groups with n < 30 (as per T012), log exclusions.
 3. **Fit**: Fit separate CLMMs for valid subgroups and test interaction terms.
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
- [ ] T040 Performance optimization: verify memory usage < 7GB during peak BERT inference
- [ ] T041 [P] Additional unit tests for edge cases (empty dialogues, NaN handling) in `tests/unit/`
- [ ] T042 [P] Configure CI workflow for full pipeline execution on GitHub Actions.
 - *Logic*: Create `.github/workflows/ci.yml` to install R, Python deps, and run the full pipeline.
- [ ] T042b [P] Execute full pipeline on GitHub Actions and capture metrics.
 - *Logic*: Run the CI workflow. Verify runtime < 6h and RAM < 7GB. Capture metrics.
 - *Dependency*: T042.
- [ ] T043 [P] Generate `docs/performance_report.md` with explicit schema.
 - *Schema*: `runtime_seconds`, `peak_memory_gb`, `convergence_rate`, `status`.
 - *Logic*: Collect metrics from T042b runs.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - **BLOCKS** all user stories.
- **Research (Phase 0)**: Depends on Foundational (Phase 2) - Must complete before US1.
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
3. Complete Phase 0: Research & Pilot
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

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
- **Constraint**: Dataset source MUST be HCI_P2 (primary) and Persona-Chat/EmpatheticDialogues (conditional on Plan stop conditions).
- **Constraint**: Subgroup analysis (US3) is strictly gated by T012 (Sample Size Verification, n ≥ 30).
- **Constraint**: Robustness classifier (T032) MUST use **textstat** (open-source) as primary; LIWC-2015 is explicitly excluded per Constitution/Plan.
- **Constraint**: Convergence rate (SC-003) must be measured via sensitivity analysis (T027b); no fallback halting allowed.