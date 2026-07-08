# Tasks: The Impact of Linguistic Complexity on Trust in AI-Generated Text

**Input**: Design documents from `/specs/001-linguistic-complexity-trust/`
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

- [ ] T001a [P] Create directory structure: `code/`, `data/raw/`, `data/processed/`, `data/outputs/figures/`, `tests/unit/`, `tests/integration/`, `tests/contract/` in `projects/PROJ-521-the-impact-of-linguistic-complexity-on-t/`
- [ ] T001b [P] Initialize `README.md` with installation instructions and project overview in `projects/PROJ-521-the-impact-of-linguistic-complexity-on-t/`
- [X] T002 [P] Initialize Python 3.11 project with `transformers`, `torch`, `scikit-learn`, `statsmodels`, `pandas`, `numpy`, `seaborn`, `textstat`, `nltk`, `datasets`, `requests` in `projects/PROJ-521-the-impact-of-linguistic-complexity-on-t/code/requirements.txt`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools in `projects/PROJ-521-the-impact-of-linguistic-complexity-on-t/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/utils.py` with: random seed pinning function, MTLD calculation logic (validating against standard definition), Flesch-Kincaid calculation (using `textstat`), and average sentence length calculator
- [ ] T005 [P] Create `contracts/text_sample.schema.yaml`, `contracts/participant_response.schema.yaml`, and `contracts/analysis_result.schema.yaml` in `specs/001-the-impact-of-linguistic-complexity-on-t/contracts/`
- [ ] T006 [P] Implement `tests/contract/test_schemas.py` to validate JSON/CSV data against the YAML schemas defined in T005
- [~] T007 [P] Create `state/projects/PROJ-521-the-impact-of-linguistic-complexity-on-t.yaml` with initial empty state and checksum tracking for `data/`
- [~] T008 [P] Setup directory structure: `data/raw/`, `data/processed/`, `data/outputs/figures/`, `tests/unit/`, `tests/integration/` in `projects/PROJ-521-the-impact-of-linguistic-complexity-on-t/`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Generation and Metric Computation (Priority: P1) 🎯 MVP

**Goal**: Generate AI text samples with controlled linguistic complexity and compute objective metrics (Flesch-Kincaid, MTLD, sentence length) to create a validated dataset.

**Independent Test**: Can be fully tested by running the generation script on a local sample of Wikipedia articles, verifying that the output CSV contains valid text, computed complexity scores, and that the scores vary across the generated samples.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T009 [P] [US1] Unit test for `code/utils.py` metrics (FK, MTLD, Sentence Length) in `tests/unit/test_metrics.py`
- [~] T010 [P] [US1] Contract test for `generated_text.csv` schema validation in `tests/contract/test_schemas.py`

### Implementation for User Story 1

- [~] T011 [US1] Implement `code/generate_text.py`: Load Wikipedia subset via `datasets.load_dataset('wikipedia')` (sampled for CPU feasibility, target N=500 samples using stratified sampling by sentence length to ensure variance), iterate with prompt variations to generate text samples using Gemma-2B (CPU-only, default precision, no quantization flags). **Depends on T004**.
- [~] T012 [US1] In `code/generate_text.py`: Compute Flesch-Kincaid, MTLD, and average sentence length for every generated sample using `code/utils.py` functions.
- [~] T013 [US1] In `code/generate_text.py`: Save results to `data/raw/generated_text.csv` with columns: `text_id`, `raw_text`, `source_id`, `flesch_kincaid`, `mtld`, `avg_sentence_length`. Include validation logic to ensure the Flesch-Kincaid range spans at least 5.0 to 12.0 (SC-001); if range is too narrow, re-sample prompts with a maximum of 3 retry attempts using specific prompt variation strategies. **If 3 retries fail, exit with code 1 and log "ERROR: Could not achieve FK variance 5.0-12.0 after 3 retries."**
- [ ] T013.1 [US1] Document the failure strategy for T013 in `docs/failure_modes.md` (if created) or `README.md` section "Error Handling".
- [~] T014 [US1] Add checksum generation for `data/raw/generated_text.csv` and update `state/projects/PROJ-521-the-impact-of-linguistic-complexity-on-t.yaml` upon completion.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Participant Trust Rating Collection (Priority: P2)

**Goal**: Recruit human participants via Prolific to read AI-labeled text samples and provide Likert trust ratings to capture the dependent variable.

**Independent Test**: Can be fully tested by simulating the survey interface with 10 dummy participants (or a small pilot) and verifying that the resulting dataset links participant IDs, text IDs, and trust scores (1-5) without data loss.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T016 [P] [US2] Contract test for `trust_responses.csv` schema validation in `tests/contract/test_schemas.py` **(Depends on T020 completion)** <!-- ATOMIZE: requested -->

### Implementation for User Story 2

- [~] T017 [US2] Implement `code/collect_trust.py`: Create a Prolific-compatible survey interface (HTML template or hosted form link) that presents text samples from `data/raw/generated_text.csv` labeled as "AI-Generated". <!-- ATOMIZE: requested -->
- [ ] T017.1 [US2] In `code/collect_trust.py`: Implement logic to assign a random subset of samples (e.g., a small number) to each participant to ensure the within-subjects design (plan.md requirement).
- [~] T018 [US2] In `code/collect_trust.py`: Implement Prolific API integration to create a study, distribute the survey link, and fetch raw response data. Implement attention check logic (e.g., a specific item requiring "Strongly Disagree") and flag participants who fail. <!-- ATOMIZE: requested -->
- [ ] T018.1 [US2] In `code/collect_trust.py`: Implement randomization and balancing logic to ensure each participant sees a representative subset of generated text samples (stratified by complexity metric) as required by the within-subjects design.
- [ ] T018.2 [US2] Create `code/prolific_client.py` with explicit function signatures `create_study()`, `fetch_responses()`, and a mock interface for testing without API keys.
- [~] T019 [US2] In `code/collect_trust.py`: Process raw Prolific responses to extract `participant_id`, `text_sample_id`, `trust_rating` (1-5), and `attention_check_status`.
- [~] T020 [US2] Save raw responses to `data/raw/trust_responses.csv`.
- [~] T021 [US2] Implement data cleaning logic in `code/collect_trust.py` (or separate script) to filter out participants who failed attention checks or straight-lined (all 1s or all 5s), saving the result to `data/processed/cleaned_responses.csv`.
- [~] T022 [US2] Verify that `data/processed/cleaned_responses.csv` meets the target N ≥ 100 valid responses (SC-002); if insufficient, exit with code 1 and log a specific message: "ERROR: Insufficient sample size. N={current_n} < 100 required for power analysis." **Blocks Phase 5**.
- [ ] T022.1 [US2] Create `code/validate_sample_size.py` that outputs a JSON report to `data/outputs/validation_report.json` containing the current N, threshold, and status before exiting.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Visualization (Priority: P3)

**Goal**: Run separate univariate linear regressions with quadratic terms for each metric, apply Bonferroni correction, perform post-hoc power analysis, and generate visualizations to validate the inverted-U hypothesis.

**Independent Test**: Can be tested by running the analysis script on a mock dataset where the relationship is known, verifying that the regression coefficient for the quadratic term is significant and negative.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T023 [P] [US3] Unit test for regression coefficient calculation and Bonferroni logic in `tests/unit/test_analysis.py`

### Implementation for User Story 3

- [~] T024 [US3] Implement `code/analyze.py`: Load `data/processed/cleaned_responses.csv` and `data/raw/generated_text.csv`, merge on `text_sample_id` to create `data/processed/analysis_inputs.csv`. **Depends on T021**. **Note: This task does NOT generate `pca_factors.csv`; no PCA is performed.**
- [~] T025 [US3] In `code/analyze.py`: Perform separate univariate linear regression analyses (one per complexity metric: FK, MTLD, Sentence Length) including a quadratic term (metric²) to test for non-linear relationships (FR-005). Do NOT use PCA or Mixed-Effects models.
- [~] T026 [US3] In `code/analyze.py`: Apply Bonferroni correction (FR-006) by calculating adjusted alpha = 0.05 / k (where k is the number of models tested) and explicitly logging: "Bonferroni correction applied: alpha = 0.05 / k = {adjusted_alpha}".
- [~] T027 [US3] In `code/analyze.py`: Perform post-hoc power analysis (FR-007) using `statsmodels.stats.power.FTestPower.solve_power` to calculate the minimum detectable effect size (f²) for the quadratic term given N ≥ 100. Verify if the calculated f² ≤ 0.15 at power ≥ 0.80 (SC-006) and log a clear PASS/FAIL status. Save results to `data/outputs/power_analysis.log`.
- [~] T028 [US3] In `code/analyze.py`: Implement robust ordinal logistic regression as a sensitivity check (FR-008) to validate the interval-scale assumption of Likert data, comparing qualitative conclusions with the linear model.
- [~] T029 [US3] In `code/analyze.py`: Generate visualizations (Trust vs. Complexity fitted curves with confidence intervals) using `seaborn` and save to `data/outputs/figures/`.
- [~] T030 [US3] Save final regression results (coefficients, p-values, R-squared, Bonferroni adjusted p-values, power analysis results) to `data/outputs/regression_results.json`.
- [~] T031 [US3] Verify that the regression model converges (no NaN/Inf) for at least one metric (SC-004) and that the quadratic term significance (p < 0.05) is reported (SC-003).
- [~] T032 [US3] Verify sensitivity consistency (SC-005) by checking if the sign and significance of the quadratic term remain consistent when using alternative metrics (e.g., Sentence Length vs. MTLD).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T033a [P] Update `README.md` with installation instructions, usage examples, and environment setup in `projects/PROJ-521-the-impact-of-linguistic-complexity-on-t/`
- [~] T033b [P] Add API documentation for `code/utils.py` and `code/analyze.py` in `docs/`
- [~] T034 Code cleanup and refactoring in `code/`
- [~] T035 [P] Run `quickstart.md` validation to ensure the entire pipeline executes correctly on CI <!-- FAILED: unspecified -->
- [~] T036 [P] Run integration test `tests/integration/test_pipeline.py` covering the full flow: Generate -> Collect -> Analyze

---

## Plan Reconciliation Tasks (Addressing Plan vs. Spec Conflicts)

- [ ] T024.5 [P] Update `plan.md` Summary and Technical Context to explicitly state "Univariate Linear Regression" and "Bonferroni Correction", removing all references to "PCA", "Mixed-Effects", and "FDR".
- [ ] T026.5 [P] Update `plan.md` Constitution Check table to reflect that Principle VII is satisfied via univariate analysis, not PCA.
- [ ] T028.5 [P] Update `plan.md` to include the Ordinal Logistic Regression sensitivity check in the Technical Context.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **Produces** `data/raw/generated_text.csv`.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2). **Consumes** `data/raw/generated_text.csv` (for text content) to generate trust ratings. **Produces** `data/processed/cleaned_responses.csv`.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2). **Consumes** `data/raw/generated_text.csv` AND `data/processed/cleaned_responses.csv` to perform analysis.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before services/scripts
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for code/utils.py metrics"
Task: "Contract test for generated_text.csv schema validation"

# Launch all models for User Story 1 together:
Task: "Implement code/generate_text.py: Load data and generate samples"
Task: "Implement code/generate_text.py: Compute metrics and save CSV"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify variance in complexity scores)
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
 - Developer A: User Story 1 (Data Generation)
 - Developer B: User Story 2 (Survey Simulation)
 - Developer C: User Story 3 (Analysis)
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
- **Constraint Check**: All tasks must run on CPU-only CI (limited cores, constrained RAM). Gemma-2B must be loaded without quantization flags (`load_in_8bit` forbidden). Data must be real (Wikipedia) or simulated with valid structure, never random noise.
- **Methodology Check**: Analysis MUST use separate univariate regressions (FR-005) and Bonferroni correction (FR-006) as specified, NOT PCA/Mixed-Effects or FDR.
