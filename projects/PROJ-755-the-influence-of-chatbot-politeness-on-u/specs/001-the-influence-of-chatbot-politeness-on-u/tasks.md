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

- [ ] T001a [P] Create project directory structure: `data/raw`, `data/processed`, `code`, `code/utils`, `tests`, `tests/contract`, `tests/unit`, `tests/integration`, `docs`, `state`.
- [ ] T001b [P] Initialize `.gitkeep` files in data directories and create `.gitignore` to exclude `data/raw/*`, `data/processed/*`, `__pycache__`, and model caches.
- [X] T002 Initialize Python project with `requirements.txt` (transformers, datasets, statsmodels, pandas, scikit-learn, numpy, pyyaml, tqdm, rpy2, textstat, evalue)
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

**Goal**: Download **HCI_P2** as the **PRIMARY** input per Plan Summary and FR-001 (narrowed scope). Filter for completeness, and compute mean politeness scores per conversation using `jfiedler/politeness-bert` on CPU.

**Independent Test**: Run `code/01_download_and_score.py` on a sample of dialogues; verify `data/processed/scored_dialogues.parquet` exists with `politeness_score` and `quality_rating` columns, and that excluded dialogues are logged.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T013 [P] [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py`
- [X] T014 [P] [US1] Unit test for politeness scoring logic (batched inference) in `tests/unit/test_scoring.py`

### Implementation for User Story 1

- [X] T015 [US1] Implement `code/01_download_and_score.py` to fetch **HCI_P2** as the **PRIMARY** input per Plan Summary.
 - *Logic*:
 1. Download `HCI_P2` from HuggingFace.
 2. Verify presence of `quality_rating`, `user_id`, `dialogue_id`.
 3. Store raw data in `data/raw/hci_p2/` with checksums.
 - *Deliverable*: Raw data stored in `data/raw/hci_p2/`.
- [ ] T012 [US1] [VERIFICATION GATE] **Sample Size Verification** for Subgroups and Primary Analysis.
 - *Logic*:
 1. **Dependency**: T015.
 2. Load the raw HCI_P2 dataset.
 3. **Check Total Sample Size**: If total n < 100 (minimum for CLMM), log "STOP: Insufficient data for primary analysis" and halt pipeline.
 4. **Check Subgroups**: Count dialogues per `age` group and `gender` group.
 5. **Gate Condition**: If ANY subgroup (e.g., Male, Female, Age 18-25) has n < 30, log that US3 (subgroup analysis) will be skipped for that specific group.
 6. **Do NOT** skip based on column existence. Only skip if n < 30.
 7. Generate `data/raw/validation_report.json` with schema:
 ```json
 {
 "status": "full" | "partial" | "missing_demographics",
 "total_sample_size": 500,
 "primary_analysis_valid": true,
 "missing_fields": [],
 "subgroup_counts": { "male": 500, "female": 480, "age_18_25": 200,... },
 "subgroups_eligible": ["male", "female", "age_18_25"],
 "subgroups_excluded": []
 }
 ```
 - *Deliverable*: `data/raw/validation_report.json`.
 - *Note*: This task gates US3. It must run after data download (T015) but before merge/score (T018).
- [ ] T011b [US1] [Pilot] Run pilot on **first 1000 rows of the raw dataset** to estimate effect size and calculate Minimum Detectable Effect (MDE).
 - *Logic*:
 1. **Dependency**: T015.
 2. Execute pilot analysis on the first 1000 rows of the raw dataset. Calculate MDE for the planned sample size.
 3. **Output**: Generate `data/processed/pilot_mde_results.json` with fields: `minimum_detectable_effect`, `power`, `sample_size`.
- [ ] T011c [US1] Update `research.md` with MDE estimation results.
 - *Logic*:
 1. **Dependency**: T011b.
 2. **Create `research.md` if it does not exist**.
 3. Read `data/processed/pilot_mde_results.json` and append section 'MDE_Estimation' to `research.md`.
- [ ] T019 [US1] Implement filtering logic to exclude dialogues missing `quality_rating` or chatbot utterances (log counts).
 - *Logic*:
 1. **Dependency**: T015.
 2. Filter dataset for completeness.
 3. Log counts of excluded dialogues.
 - *Deliverable*: Filtered raw dataset in `data/raw/filtered/`.
- [ ] T018 [US1] Implement **Schema Definition, Transformation, and Merge** for HCI_P2.
 - *Logic*:
 1. **Dependency**: T019.
 2. Define the target schema for HCI_P2 (user_id, dialogue_id, quality_rating, age, gender, utterances).
 3. Transform the filtered dataset to match this schema.
 4. Save as `data/processed/merged_dialogues.parquet`.
 5. **Note**: Since source is single dataset, 'Merge' is effectively a transformation and save.
 - *Deliverable*: `data/processed/merged_dialogues.parquet`.
- [ ] T020 [US1] Implement **Politeness Scoring** (Load, Inference, Error Handling).
 - *Logic*:
 1. **Dependency**: T018.
 2. Load `jfiedler/politeness-bert` (CPU-only).
 3. Verify model file size ≤ 100MB.
 4. Iterate through utterances in batches with dynamic batch sizing.
 5. Compute politeness scores; assign NaN to failures and log counts.
 6. Compute `mean_politeness_score` per dialogue and z-score standardize.
 7. Save to `data/processed/scored_dialogues.parquet`.
 - *Deliverable*: `data/processed/scored_dialogues.parquet`.
- [ ] T021 [US1] Save processed data to `data/processed/scored_dialogues.parquet` and raw logs to `data/raw/exclusions.log`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Cumulative Link Mixed-Effects Analysis (Priority: P2)

**Goal**: Fit a CLMM testing the association between politeness and quality ratings, controlling for length and user random effects, with multiple-comparison correction.

**Independent Test**: Run `code/02_fit_clmm.py` on `scored_dialogues.parquet`; verify `data/processed/clmm_results.csv` contains coefficients, p-values, and that convergence warnings are logged if fallback occurs.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US2] Unit test for VIF calculation and collinearity check in `tests/unit/test_collinearity.py`
- [X] T024 [P] [US2] Integration test for CLMM execution and result schema validation in `tests/integration/test_clmm.py`

### Implementation for User Story 2

- [X] T025 [US2] Implement `code/02_fit_clmm.py` to load `scored_dialogues.parquet`
- [ ] T026 [US2] Implement VIF check for `politeness` and `conversation_length`; log warning and drop variable if VIF ≥ 5.
- [ ] T027 [US2] Implement CLMM fitting via `rpy2` (formula: `quality_rating ~ politeness + conversation_length + (1|user_id)`) with `lme4`.
- [ ] T027a [US2] **Extract Convergence Status**: Calculate convergence status for each fitted model.
 - *Logic*:
 1. **Dependency**: T027.
 2. Extract convergence flag from the model object.
 3. Return a list of convergence statuses.
 - *Deliverable*: List of convergence statuses.
- [ ] T027b [US2] **Aggregate Convergence Rate**: Calculate and log the **CLMM convergence rate**.
 - *Logic*:
 1. **Dependency**: T027a.
 2. Calculate convergence rate (converged / total).
 3. **Report**: If convergence ≥ 95%, log "SC-003 MET". If convergence < 95%, log "SC-003 NOT MET" and record the specific rate.
 4. **Do NOT** satisfy SC-003 with a fallback. If convergence < 95%, the project fails SC-003.
 - *Note*: This task does NOT execute the fallback. It only reports the status.
 - *Dependency*: T027a.
- [ ] T027c [US2] **Fallback Execution**: If T027b reports convergence < 95%, execute fallback to fixed-effects ordinal regression.
 - *Logic*:
 1. **Dependency**: T027b.
 2. If convergence < 95%, re-fit model using `statsmodels` (OrdinalGEE or `statsmodels.miscmodels.ordinal_model`) with formula `quality_rating ~ politeness + conversation_length`.
 3. Log diagnostic: "Fallback executed due to low CLMM convergence".
 - *Note*: This task is for robustness, but does NOT satisfy SC-003.
 - *Dependency*: T027b.
- [ ] T027d [US2] **Record Project Status**: Save convergence status and outcome to `data/processed/project_status.json`.
 - *Logic*:
 1. **Dependency**: T027b (Reporting) AND T027c (Fallback, if triggered).
 2. Create `project_status.json` with fields: `convergence_rate`, `status` ("success" or "fallback_executed"), `sc003_met` (boolean).
 3. This task runs regardless of whether fallback was needed, ensuring the success criterion is always measured.
 - *Deliverable*: `data/processed/project_status.json`.
- [ ] T028 [US2] Implement Benjamini-Hochberg correction for p-values across fixed effects.
- [ ] T029 [US2] Save results to `data/processed/clmm_results.csv` with coefficients, SEs, p-values, CI, and convergence metrics.
 - *Logic*:
 1. **Dependency**: T027d (Status Recording).
 2. Save results (either from primary CLMM or fallback) to `data/processed/clmm_results.csv`.
 - *Note*: This task consolidates the logic previously split between T028 and T028b into a single coherent flow.
 - *Dependency*: T027d.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness and Subgroup Analysis (Priority: P3)

**Goal**: Validate findings with an **open-source lexicon** (per Plan Phase 0, Step 4) and conduct subgroup analyses by age/gender (n ≥ 30 guard).

**Independent Test**: Run `code/03_robustness_analysis.py`; verify `data/processed/robustness_results.csv` exists, correlation (r ≥ 0.80) is calculated, and subgroup exclusions are logged.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US3] Unit test for lexicon-based scoring logic in `tests/unit/test_lexicon_scoring.py`
- [X] T031 [P] [US3] Integration test for subgroup filtering logic (n ≥ 30) in `tests/integration/test_subgroup.py`

### Implementation for User Story 3

- [ ] T032 [US3] **Robustness Classifier**: Implement `code/03_robustness_analysis.py` to re-score dialogues.
 - *Logic*:
 1. **Dependency: T021** (Completion of US1). Load `scored_dialogues.parquet`.
 2. **Primary**: Attempt to use **LIWC-2015** Politeness Dictionary if license is available.
 3. **Fallback**: If license is missing, automatically use `textstat` (open-source lexicon) as per Plan Phase 0, Step 4. Log the classifier used.
 4. **Do NOT** fail hard on missing license.
 - *Dependency*: T021.
 - *Traceability*: Explicitly satisfies **FR-005** (Robustness) and **SC-004** (Effect size consistency).
- [ ] T033 [US3] **Re-fit CLMM**: Re-fit CLMM on lexicon scores.
 - *Logic*:
 1. **Dependency: T032**.
 2. Re-fit CLMM using the new lexicon-based politeness scores.
 3. Save model object to `data/processed/robustness_model.pkl`.
 - *Dependency*: T032.
- [ ] T033b [US3] **Generate Predicted Scores & Correlate**: Calculate correlation of per-dialogue predicted quality scores.
 - *Logic*:
 1. **Dependency: T033**.
 2. Generate `predicted_quality` scores for each dialogue using the primary CLMM (expected value of ordinal outcome) and the robust CLMM.
 3. Calculate Pearson correlation `correlation_r` between `primary_predicted_quality` and `robust_predicted_quality`.
 4. Save `correlation_r` to `data/processed/robustness_results.csv` at **row 0, column `correlation_r`**.
 5. Verify r ≥ 0.80 per SC-004.
 - *Note*: Explicitly generate per-dialogue predicted quality scores via CLMM prediction before correlation calculation.
 - *Dependency*: T033.
- [ ] T034 [US3] **Subgroup Analysis**: Split data by age/gender.
 - *Dependency*: Requires T012 (Sample Size Verification) to have reported `subgroups_eligible`.
 - *Logic*:
 1. **Check Columns**: If `age` or `gender` columns are missing, log "Subgroup analysis skipped: missing demographic columns" and exit.
 2. **Filter**: Exclude groups with n < 30 (as per T012), log exclusions.
 3. **Fit**: Fit separate CLMMs for valid subgroups and test interaction terms.
- [ ] T035 [US3] Apply multiplicity correction for subgroup tests.
- [ ] T037 [US3] Save all robustness results to `data/processed/robustness_results.csv`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

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
- **Constraint**: Dataset source MUST be HCI_P2 only (per Plan Summary).
- **Constraint**: Subgroup analysis (US3) is strictly gated by T012 (Sample Size Verification, n ≥ 30).
- **Constraint**: Robustness classifier (T032) must fallback to `textstat` if LIWC license is missing; do not fail hard.
- **Constraint**: Convergence rate (SC-003) must be reported accurately; fallback does not satisfy the success criterion.