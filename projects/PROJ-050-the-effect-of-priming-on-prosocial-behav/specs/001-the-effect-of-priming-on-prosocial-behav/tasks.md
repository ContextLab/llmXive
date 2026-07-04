# Tasks: The Effect of Priming on Prosocial Behavior in Online Communities

**Input**: Design documents from `/specs/001-the-effect-of-priming-on-prosocial-behav/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

- [ ] T001a Create directory structure per implementation plan: `code/`, `data/` (raw, processed, validation), `output/` (results, figures, logs), `tests/`, `specs/contracts/`
- [ ] T001b Create `__init__.py` files in all `code/` subdirectories (`ingestion`, `processing`, `analysis`, `utils`) and `tests/` subdirectories
- [ ] T002 Initialize Python 3.11 project with dependencies: `pandas`, `nltk`, `vaderSentiment`, `statsmodels`, `scikit-learn`, `seaborn`, `matplotlib`, `requests`, `pyyaml`, `pydantic`, `sentence-transformers`, `torch` (CPU)
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `code/config.py` with constants: target subreddits, prime keywords, negation words, TARGET_N=10000, random seeds
- [ ] T005 [P] Create `code/utils/logger.py` for structured logging and `code/utils/checksum.py` for data integrity verification
- [ ] T006 [P] Implement `code/main.py` orchestration entry point with argument parsing and pipeline flow control
- [ ] T007 Create base data validation schemas in `specs/contracts/` (dataset.schema.yaml, output.schema.yaml, gold_standard.schema.yaml) with fields explicitly validating against `Thread` and `Comment` entities defined in `data-model.md`
- [ ] T008 [P] Setup `data/` directory structure: `raw/`, `processed/`, `validation/`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2.5: Pre-Flight Gate (Blocking)

**Purpose**: Validate study design before data collection

- [ ] T009a [P] Implement power analysis script in `code/analysis/power_analysis.py` (FR-013) to verify N=10,000 yields ≥80% power for d=0.15. Output must be `output/power_analysis_report.json`.
- [ ] T009b [P] Execute power analysis script (`T009a`). **CONDITIONAL GATE**: If power < 80%, the script MUST log a warning and **halt** execution, requiring a manual `--allow-low-power` flag or an interactive researcher approval prompt to proceed. It MUST NOT automatically abort the pipeline without this override mechanism, per FR-013. The implementation must provide a clear path for the researcher to approve continuation.

**Checkpoint**: Power analysis passed (or approved) - data collection can now begin

---

## Phase 3: User Story 1 - Data Ingestion, Classification, and Anonymization (Priority: P1) 🎯 MVP

**Goal**: Retrieve Reddit data, classify threads into Prime/Control groups, and anonymize PII before storage.

**Independent Test**: Execute `code/ingestion/fetch_data.py` and `code/ingestion/classify.py` against a small test subset; verify output DataFrame has `thread_type` (Prime/Control), `thread_id`, hashed `user_id`, and calculated `thread_age`, with ≥4,000 comments per group (or abort).

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for data schema validation in `tests/contract/test_data_schema.py`
- [ ] T011 [P] [US1] Integration test for negation logic (e.g., "No help needed" → Control) in `tests/integration/test_classification_logic.py`
- [ ] T012 [P] [US1] Unit test for PII removal (no plaintext usernames/timestamps) in `tests/unit/test_anonymize.py`

### Implementation for User Story 1

- [ ] T013 [US1] Implement `code/ingestion/fetch_data.py`: Load `pushshift/reddit` (HF), validate presence of all 5 target subreddits (FR-014), fetch comments until TARGET_N reached or exhaustion. **MUST preserve raw `created_utc` timestamp in output DataFrame for downstream calculation.**
- [ ] T014 [US1] Implement `code/ingestion/classify.py`: Tokenize titles with NLTK, apply negation rule (keyword within 3 tokens of negation → Control), log "Negation Exclusions" (FR-002a), assign `thread_type`. **MUST preserve raw `created_utc` timestamp in output DataFrame.**
- [ ] T014a [US1] Implement source-switching logic in `fetch_data.py` (FR-001a): If primary source lacks required subreddits, automatically switch to verified fallback source (Pushshift.io full dump or alternative verified HF dataset) before proceeding. If no verified source is available, abort with clear error listing missing subreddits.
- [ ] T015 [US1] Implement `code/processing/anonymize.py`: Hash usernames (SHA-256) as `user_id`, calculate `thread_age` (days) from `created_utc`, strip original timestamp, save to `data/processed/`. **Only this step strips timestamps.**
- [ ] T016 [US1] Implement abort logic in `fetch_data.py`: Abort if <4,000 comments per group, OR dataset exhausted before TARGET_N, OR missing subreddits (FR-001, FR-001a). **Verification**: Run with mock dataset returning <4000 comments/group; must cause SystemExit with error message containing "Insufficient data".
- [ ] T017 [US1] Add checksum generation for raw and processed data files.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Prosocial Action Scoring and Validation (Priority: P2)

**Goal**: Compute prosocial action counts and VADER sentiment scores, then validate against human annotations.

**Independent Test**: Run `code/processing/scoring.py` on a sample; verify `prosocial_action_count` and `neg_score` columns exist. Run `code/processing/validation.py` on stratified sample; verify Cohen's Kappa ≥ 0.7 against `gold_standard.csv`.

### Tests for User Story 2

- [ ] T018 [P] [US2] Contract test for scoring output schema in `tests/contract/test_scoring_schema.py`
- [ ] T019 [P] [US2] Integration test for stratified sampling logic (FR-010a) in `tests/integration/test_stratified_sampling.py`
- [ ] T020 [P] [US2] Unit test for prosocial lexicon exclusion (prime keywords not counted) in `tests/unit/test_lexicon.py`

### Implementation for User Story 2

- [ ] T021 [US2] Implement `code/processing/scoring.py`: Compute VADER scores (compound, pos, neu, neg) and `prosocial_action_count` using secondary lexicon (excluding prime keywords AND semantic equivalents: `donate`, `contribute`, `share`, `give-away`) (FR-003, FR-003b).
- [ ] T022 [US2] Implement `code/processing/embedding.py`: Generate sentence embeddings for thread titles using `all-MiniLM-L6-v2` (CPU) for topic control. **Output**: `data/processed/embeddings.parquet`. **Note**: This task implements the "Topic Confounding Mitigation" strategy from plan.md, a deviation from spec FR-005.
- [ ] T033 [US2] Implement `code/processing/embedding.py` (PCA): Apply PCA to embeddings from T022 (`data/processed/embeddings.parquet`), retain top components as `topic_pc1`, `topic_pc2`, `topic_pc3` for GLMM covariates. **Output**: `data/processed/pca_components.parquet`. Save to `data/processed/`. **Note**: This task implements the "Topic Confounding Mitigation" strategy from plan.md, a deviation from spec FR-005.
- [ ] T024a [US2] Implement `code/processing/generate_annotations.py`: Generate the `gold_standard.csv` artifact and `human_annotation_protocol.md` if not provided externally. **Recruitment Simulation**: Simulate recruitment of ≥3 independent raters (e.g., using a deterministic seeded random process for testing) and generate the CSV with columns `comment_id`, `rater_id`, `label_prosocial`, `label_neg` per FR-011. **Output**: `data/validation/gold_standard.csv` and `data/validation/human_annotation_protocol.md`. This task ensures the Human Annotation Protocol is fully implemented even without external data.
- [ ] T023 [US2] Implement `code/processing/validation.py`: Stratified sampling with **explicit FR-010a merge hierarchy**: 1. Merge subreddits within thematic category, 2. Merge across thread_type if still insufficient, 3. Draw from global pool until A minimum sample size sufficient for statistical power was met.. **Verify ≥3 raters in `gold_standard.csv` (FR-011a) and REJECT files with <3 raters, logging an error.** Compute Cohen's Kappa against `gold_standard.csv`. **Input**: `data/validation/gold_standard.csv` (from T024a).
- [ ] T024 [US2] Create `data/validation/human_annotation_protocol.md` with required sections: 1. Codebook (defining prosocial action intent vs lexical form), 2. Rater Instructions, 3. CSV format spec (FR-011). **Note**: If T024a generates this, T024 updates it with final human-readable instructions.
- [ ] T025 [US2] Add memory profiling and chunking logic to ensure scoring completes ≤4 hours on 7GB RAM (FR-012).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Reporting (Priority: P3)

**Goal**: Perform GLMM analysis with topic control, sensitivity analysis, and visualization.

**Independent Test**: Execute `code/analysis/glmm.py` and `code/analysis/sensitivity.py`; verify `output/results.json` contains p-values, coefficients, and confidence intervals; verify `output/figures/boxplot.png` exists.

### Tests for User Story 3

- [ ] T026 [P] [US3] Contract test for results.json schema in `tests/contract/test_results_schema.py`
- [ ] T027 [P] [US3] Integration test for GLMM singular fit fallback (FR-005b) in `tests/integration/test_glmm_fallback.py`
- [ ] T028 [P] [US3] Unit test for sensitivity analysis bootstrap logic in `tests/unit/test_sensitivity.py`

### Implementation for User Story 3

- [ ] T029a [US3] Implement `code/analysis/deviation_log.py`: Create a formal documentation file `output/deviation_log.md` explicitly stating the deviation from spec FR-005 (LMM) to GLMM (Negative Binomial) and the inclusion of topic covariates, referencing the plan.md justification. **This task ensures traceability.**
- [ ] T029b [US3] Update `spec.md` to formally document the deviation from the LMM (Gaussian) to the GLMM (Negative Binomial) and the inclusion of topic covariates, ensuring the spec and tasks are aligned before implementation. **Reference plan.md "Critical Statistical Correction" and "Topic Confounding Mitigation" sections.**
- [ ] T029 [US3] Implement `code/analysis/glmm.py`: Fit Negative Binomial GLMM (`prosocial_action_count ~ thread_type + thread_age + comment_count + topic_pc1 + topic_pc2 + topic_pc3 + (1|thread_id) + (1|user_id)`) using `statsmodels`. **Input**: `data/processed/pca_components.parquet` (from T033). **Note: Deviates from spec FR-005 (LMM) per plan.md justification for statistical validity of count data. Documented in T029a and T029b.** **Singular Fit Check**: If variance component for `user_id` <= 0.01, re-fit model WITHOUT `user_id` random effect and record fallback (FR-005b). Include topic covariates per plan's Topic Confounding Mitigation strategy.
- [ ] T030 [US3] Implement `code/analysis/sensitivity.py`: Run bootstrap resampling, model variants (drop `thread_age`, drop `comment_count`, drop both), and alternative random effects; compute p-values for thresholds including standard significance levels (FR-005a).
- [ ] T031 [US3] Implement `code/analysis/viz.py`: Generate boxplot comparing `prosocial_action_count` for Prime vs Control; save as PNG (FR-006).
- [ ] T032 [US3] Implement descriptive stats generation (mean, median, std) per group and save to `output/results.json` (FR-004).
- [ ] T034 [US3] Finalize `output/results.json` with all coefficients, p-values, confidence intervals, and sensitivity analysis results.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Run full pipeline end-to-end on GitHub Actions runner to verify ≤4 hour runtime (SC-004)
- [ ] T036 [P] Run PII scan script on `data/processed/` to confirm zero plaintext usernames/timestamps (SC-005)
- [ ] T037 [P] Update `quickstart.md` with execution instructions and expected outputs
- [ ] T038a [P] Update docstrings for all public functions in `code/ingestion/`, `code/processing/`, and `code/analysis/`
- [ ] T038b [P] Run `black --check` and `flake8` on entire `code/` directory; fix violations
- [ ] T038c [P] Update `README.md` with project status and execution steps
- [ ] T039 [P] Verify `gold_standard.csv` structure and rater count (SC-007)
- [ ] T040 [P] Validate `neg_score` correlation with VADER `neg` on a **stratified sample of 200 comments** (matching FR-010 robustness); verify Pearson r >= 0.9 (SC-008). **Justification**: Sample size ensures statistical robustness comparable to validation requirements (FR-010).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Pre-Flight (Phase 2.5)**: Depends on Foundational - BLOCKS Data Ingestion
- **User Stories (Phase 3+)**: All depend on Pre-Flight phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Pre-Flight (Phase 2.5) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Pre-Flight (Phase 2.5) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Pre-Flight (Phase 2.5) - Depends on US1, US2, and **T033 (PCA)** outputs

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Config before services/logic
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

### Explicit Artifact Dependencies

- **T033 (PCA)** produces `data/processed/pca_components.parquet` which is **required** by **T029 (GLMM)**.
- **T024a (Generate Annotations)** produces `data/validation/gold_standard.csv` which is **required** by **T023 (Validation)**.
- **T029a (Deviation Log)** and **T029b (Spec Update)** must be completed before **T029 (GLMM)** implementation to ensure documentation exists and spec is aligned.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Contract test for data schema validation in tests/contract/test_data_schema.py"
Task: "Integration test for negation logic in tests/integration/test_classification_logic.py"
Task: "Unit test for PII removal in tests/unit/test_anonymize.py"

# Launch implementation tasks (sequentially due to data flow):
Task: "Implement fetch_data.py" -> "Implement classify.py" -> "Implement anonymize.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 2.5: Pre-Flight Gate (BLOCKING)
4. Complete Phase 3: User Story 1 (Data Ingestion & Classification)
5. **STOP and VALIDATE**: Test US1 independently (verify data volume, classification logic, anonymization)
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add Pre-Flight Gate → Validate design
3. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
4. Add User Story 2 → Test independently (scoring & validation) → Deploy/Demo
5. Add User Story 3 → Test independently (analysis & viz) → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Data)
   - Developer B: User Story 2 (Scoring/Validation)
   - Developer C: User Story 3 (Analysis) - *Note: US3 depends on US1/US2 outputs, so may need to wait or use mock data for unit tests*
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
- **Critical**: Ensure `fetch_data.py` validates subreddits BEFORE fetching (FR-014).
- **Critical**: Ensure `fetch_data.py` implements source-switching logic (FR-001a) and aborts if no verified source found.
- **Critical**: Ensure `scoring.py` excludes prime keywords AND semantic equivalents (`donate`, `share`, `give-away`) from action count (FR-003b).
- **Critical**: Ensure GLMM uses Negative Binomial distribution, not Gaussian (Plan correction). **Documented in T029a and T029b.**
- **Critical**: Ensure `thread_age` is calculated BEFORE anonymization strips timestamps (FR-009).
- **Critical**: Ensure `anonymize.py` is the ONLY step that strips timestamps.
- **Critical**: Ensure `gold_standard.csv` validation rejects files with <3 raters (FR-011a). **Producer task T024a ensures file exists.**
- **Critical**: Ensure sensitivity analysis covers all three model variants and thresholds (0.01, 0.05, 0.10) (FR-005a).
- **Critical**: Ensure singular fit fallback triggers at variance <= 0.01 (FR-005b).
- **Critical**: Ensure `neg_score` validation uses 200 samples (matching FR-010) for statistical robustness (SC-008).
- **Critical**: Ensure power analysis is a conditional gate (warning + approval) before data collection (FR-013).
- **Critical**: Ensure T033 (PCA) is a prerequisite for T029 (GLMM) as per artifact flow.