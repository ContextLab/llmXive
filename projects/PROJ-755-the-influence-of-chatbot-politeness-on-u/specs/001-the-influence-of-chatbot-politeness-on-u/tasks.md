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
- [ ] T010 [P] [Setup] Setup environment configuration management (`.env` template for `HF_TOKEN` if needed).
 - *Logic*: Create `.env.example` with `HF_TOKEN=` placeholder. Document in `README.md` that this is for local development only and that CI secrets must be injected via GitHub Actions environment variables to ensure reproducibility on fresh runners per Constitution Principle I.

**Checkpoint**: Setup ready - Foundational phase can now begin

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure and validation that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. These tasks verify the data exists and meets schema requirements.

- [ ] T009 [P] Create `contracts/output.schema.yaml` defining CLMM results structure
- [ ] T011 [P] [Foundational] Implement `code/utils/schema_validator.py` to validate dataset schemas against `contracts/dataset.schema.yaml`
- [ ] T011b [P] [Foundational] Perform Power & Sample Size Estimation and update `research.md`.
 - *Logic*: Run pilot on sample data to estimate effect size.
 - *Output*: Append section 'MDE_Estimation' to `research.md` with fields: `minimum_detectable_effect`, `power`, `sample_size`.
- [ ] T012 [P] [Foundational] **VERIFICATION GATE**: Validate presence of `quality_rating`, `user_id`, `age`, and `gender` fields in the merged dataset.
 - *Logic*:
 1. Check `quality_rating` and `user_id`: If missing in HCI_P2, **log critical error** ('CRITICAL: Missing required fields') and **exit with code 1**.
 2. Check `age` and `gender`: If missing, **do not halt**. Generate `data/raw/validation_report.json` with `status: partial` and `missing_fields: ['age', 'gender']`. Proceed to US1 and US2.
 3. If `age`/`gender` missing, log that US3 (subgroup analysis) will be skipped per FR-006.
 - *Deliverable*: `data/raw/validation_report.json` (if partial) or `data/raw/validation_report.json` with `status: full`.
 - *Note*: This task gates ALL user stories (US1, US2, US3). It must run before any download or scoring logic.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Politeness Scoring (Priority: P1) 🎯 MVP

**Goal**: Download **HCI_P2** dataset as the primary source (per Plan Phase 0), filter for completeness, and compute mean politeness scores per conversation using `jfiedler/politeness-bert` on CPU. Download Persona-Chat and EmpatheticDialogues ONLY if HCI_P2 lacks required fields. Store all datasets separately as per FR-001.

**Independent Test**: Run `code/01_download_and_score.py` on a sample of dialogues; verify `data/processed/scored_dialogues.parquet` exists with `politeness_score` and `quality_rating` columns, and that excluded dialogues are logged.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T013 [P] [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py`
- [X] T014 [P] [US1] Unit test for politeness scoring logic (batched inference) in `tests/unit/test_scoring.py`

### Implementation for User Story 1

- [ ] T015 [US1] Implement `code/01_download_and_score.py` to fetch **HCI_P2** as the **primary input** per Plan Phase 0.
 - *Logic*:
 1. Attempt to download **HCI_P2** first.
 2. Verify presence of `quality_rating`, `user_id`, `dialogue_id`.
 3. **Dependency: T012**. Check `data/raw/validation_report.json`.
 4. **If HCI_P2 lacks `quality_rating` (status: partial/missing)**, attempt to fetch **Persona-Chat** and **EmpatheticDialogues** as fallback sources per FR-001.
 5. If all sources lack `quality_rating`, abort with critical error.
 - *Deliverable*: Raw data stored in `data/raw/hci_p2/` with checksums (and fallbacks if triggered).
- [ ] T016 [US1] Implement **conditional** merging logic to combine available datasets into a unified DataFrame ONLY if HCI_P2 lacks required fields.
 - *Logic*:
 1. **Dependency: T012**. Check `data/raw/validation_report.json`.
 2. If `status: full`, **DO NOT MERGE**. Use HCI_P2 only.
 3. If `status: partial` or missing, merge available fallback datasets (Persona-Chat, EmpatheticDialogues) into `data/processed/merged_dialogues.parquet`.
 4. Preserve `user_id`, `dialogue_id`, `quality_rating`, `age`, `gender`.
 - *Deliverable*: `data/processed/merged_dialogues.parquet` (if merge occurs) or `data/processed/scored_dialogues.parquet` (if HCI_P2 only).
- [ ] T017 [US1] Implement filtering logic to exclude dialogues missing `quality_rating` or chatbot utterances (log counts).
- [ ] T018 [US1] Implement batched inference using `jfiedler/politeness-bert` (CPU-only, `torch.no_grad()`, max_memory management) to score utterances.
 - *Error Handling*: Implement try-except for `ModelLoadingError` and `MemoryError`, log specific error codes, and fallback to `batch_size=1`.
- [ ] T019 [US1] Implement aggregation logic to compute `mean_politeness_score` per dialogue and z-score standardization.
- [ ] T020 [US1] Save processed data to `data/processed/scored_dialogues.parquet` and raw logs to `data/raw/exclusions.log`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Cumulative Link Mixed-Effects Analysis (Priority: P2)

**Goal**: Fit a CLMM testing the association between politeness and quality ratings, controlling for length and user random effects, with multiple-comparison correction.

**Independent Test**: Run `code/02_fit_clmm.py` on `scored_dialogues.parquet`; verify `data/processed/clmm_results.csv` contains coefficients, p-values, and that convergence warnings are logged if fallback occurs.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Unit test for VIF calculation and collinearity check in `tests/unit/test_collinearity.py`
- [X] T022 [P] [US2] Integration test for CLMM execution and result schema validation in `tests/integration/test_clmm.py`

### Implementation for User Story 2

- [X] T023 [US2] Implement `code/02_fit_clmm.py` to load `scored_dialogues.parquet`
- [ ] T024 [US2] Implement VIF check for `politeness` and `conversation_length`; log warning and drop variable if VIF ≥ 5.
- [ ] T025 [US2] Implement CLMM fitting via `rpy2` (formula: `quality_rating ~ politeness + conversation_length + (1|user_id)`) with `lme4`.
- [ ] T026 [US2] **Convergence Tracking & Fallback**: Calculate and log the **CLMM convergence rate** (number of converged models / total attempts) to verify **SC-003**.
 - *Logic*:
 1. Execute CLMM fitting (T025).
 2. Calculate convergence rate.
 3. **Report**: If convergence ≥ 95%, log "SC-003 MET". If convergence < 95%, log "SC-003 NOT MET" and record the specific rate.
 4. **Fallback**: IF convergence < 95%, execute fallback to fixed-effects ordinal regression and log diagnostic.
 - *Note*: The fallback is a remediation step triggered ONLY when SC-003 is NOT met. It does not satisfy SC-003.
 - *Dependency*: T026 must complete before T028.
- [ ] T027 [US2] Implement Benjamini-Hochberg correction for p-values across fixed effects.
- [ ] T028 [US2] Save results to `data/processed/clmm_results.csv` with coefficients, SEs, p-values, CI, and convergence metrics.
 - *Logic*:
 1. **Dependency**: T026 (Convergence Check).
 2. If T026 triggered fallback, **re-fit** the model using fixed-effects ordinal regression logic as defined in T026.
 3. Save results (either from primary CLMM or fallback) to `data/processed/clmm_results.csv`.
 - *Note*: This task consolidates the logic previously split between T028 and T028b into a single coherent flow.
 - *Dependency*: T026 (including any fallback execution).
- [ ] T028b [US2] **REMOVED**: Logic consolidated into T028.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness and Subgroup Analysis (Priority: P3)

**Goal**: Validate findings with an **open-source lexicon-based classifier** (`textstat`/`politeness` per Plan Phase 0 Step 4) and conduct subgroup analyses by age/gender (n ≥ 30 guard).

**Independent Test**: Run `code/03_robustness_analysis.py`; verify `data/processed/robustness_results.csv` exists, correlation (r ≥ 0.80) is calculated, and subgroup exclusions are logged.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US3] Unit test for lexicon-based scoring logic in `tests/unit/test_lexicon_scoring.py`
- [X] T031 [P] [US3] Integration test for subgroup filtering logic (n ≥ 30) in `tests/integration/test_subgroup.py`

### Implementation for User Story 3

- [ ] T032 [US3] **Robustness Classifier**: Implement `code/03_robustness_analysis.py` to re-score dialogues.
 - *Logic*:
 1. **Dependency: T015**. Load `scored_dialogues.parquet`.
 2. **Primary**: Use `textstat` (Bing/Afinn) as the robustness classifier per Plan Phase 0 Step 4 to satisfy **FR-005** and **SC-004**.
 3. **Optional**: If LIWC-2015 is available (manual license), use it instead and log the switch.
 4. Log the classifier used.
 - *Dependency*: T015.
 - *Traceability*: Explicitly satisfies **FR-005** and **SC-004** even when using fallback `textstat`.
- [ ] T033 [US3] Re-fit CLMM on lexicon scores and compute **Pearson correlation of per-dialogue predicted quality scores** between the primary model and the robustness model.
 - *Metric*: Calculate `correlation_r` between `primary_model.predicted_quality` and `robust_model.predicted_quality`.
 - *Output*: Save `correlation_r` to `data/processed/robustness_results.csv` at **row 0, column `correlation_r`**.
 - *Target*: Verify r ≥ 0.80 per SC-004.
 - *Note*: Explicitly generate per-dialogue predicted quality scores via CLMM prediction before correlation calculation. **Save the calculated `correlation_r` value to the output file.**
- [ ] T034 [US3] **Subgroup Analysis**: Split data by age/gender.
 - *Dependency*: Requires T012 (Demographic Verification) to have reported `status: full` or `partial` with available fields.
 - *Logic*: Exclude groups with n < 30, log exclusions. Fit separate CLMMs for valid subgroups and test interaction terms.
- [ ] T035 [US3] Apply multiplicity correction for subgroup tests.
- [ ] T037 [US3] Save all robustness results to `data/processed/robustness_results.csv`.
- [ ] T032a [US3] **REMOVED**: LIWC acquisition logic removed; `textstat` is now the primary robustness classifier.
- [ ] T036 [US3] **REMOVED**: E-value calculation removed (no FR-008 in Spec).
- [ ] T036a [US3] **REMOVED**: Spec amendment for E-values removed.
- [ ] T036b [US3] **REMOVED**: E-value report removed.

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
- [ ] T042 [P] Run `quickstart.md` validation to ensure full pipeline executes on **fresh GitHub Actions runner** with **pinned seeds** within 6 hours.
- [ ] T043 [P] Generate `docs/performance_report.md` with explicit schema.
 - *Schema*: `runtime_seconds`, `peak_memory_gb`, `convergence_rate`, `status`.
 - *Logic*: Collect metrics from T040 and T042 runs.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - **BLOCKS** all user stories. Includes T012 (Demographic Verification) which gates US3.
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
Task: "Implement code/01_download_and_score.py to fetch HCI_P2 (primary) and fallbacks"
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
- **Constraint**: Dataset source MUST prioritize HCI_P2 as per Plan; Persona-Chat and EmpatheticDialogues are fallbacks only.
- **Constraint**: Subgroup analysis (US3) is strictly gated by T012 (Demographic Verification).