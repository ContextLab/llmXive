# Tasks: llmXive follow-up: extending "Trust-Region Behavior Blending for On-Policy Distillation"

**Input**: Design documents from `/specs/001-llmxive-trb-diversity-profile/`
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

<!--
 ============================================================================
 IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

 The /speckit-tasks command MUST replace these with actual tasks based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so each story can:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-976-llmxive-follow-up-extending-trust-region/`)
- [X] T002 Initialize Python project with dependencies (`pandas`, `scikit-learn`, `spacy`, `numpy`, `jsonlines`, `pyyaml`, `pytest`) in `requirements.txt`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` with paths, random seeds, and hyperparameter defaults
- [X] T005a [P] Create `code/utils/data_loader.py` to fetch `tr-books-tokenized` and `Tr-beir-formatted` from HuggingFace with checksum verification
- [X] T005b [P] Record fetched dataset checksums to `state/projects/PROJ-976-llmxive-follow-up-extending-trust-region.yaml` under `artifact_hashes` (Constitution Principle III)
- [ ] T006a [P] **Amend spec.md**: Update FR-002, FR-004, FR-007, SC-002, SC-006 to explicitly reflect the proxy strategy (relevance scores/text length) instead of ground-truth sweep logs, defining "proxy collapse" as "low relevance" and "proxy stability" as "relevance variance".
- [ ] T006b [P] **Amend data-model.md**: Update `TrainingInstance` schema to link profiles to proxy targets instead of `optimal_epsilon_0`/`collapse_label`.
- [ ] T007 Create YAML contracts for feature matrices in `specs/001-llmxive-trb-diversity-profile/contracts/dataset.schema.yaml`
- [ ] T008 Create YAML contracts for analysis results in `specs/001-llmxive-trb-diversity-profile/contracts/model_output.schema.yaml`
- [ ] T009 Setup directory structure for `data/raw/`, `data/processed/`, and `data/results/`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Static Diversity Profile Computation (Priority: P1) 🎯 MVP

**Goal**: Compute lexical and syntactic metrics on teacher outputs (Book Corpus & BEIR) to generate feature vectors without GPU.

**Independent Test**: Run `code/pipelines/extract_features.py` on a sample of teacher responses; verify output JSON contains valid `distinct_4_ratio`, `ngram_entropy`, and `syntactic_variation_score` with zero GPU usage.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for distinct-4 ratio calculation in `tests/unit/test_lexical.py`
- [X] T011 [P] [US1] Unit test for parse tree depth variance in `tests/unit/test_syntactic.py`
- [X] T012 [P] [US1] Edge case test: empty string handling in `tests/unit/test_edge_cases.py`

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement `code/metrics/lexical.py`: distinct-4 ratio and n-gram entropy functions
- [X] T014 [P] [US1] Implement `code/metrics/syntactic.py`: parse tree depth variance using `en_core_web_sm` (CPU-only)
- [X] T015 [US1] Implement fallback logic for parse failures (return NaN + log warning) in `code/metrics/syntactic.py`
- [X] T016 [US1] Implement `code/pipelines/extract_features.py`: batch processing (batch size of a moderate magnitude) to Stay within reasonable RAM limits.
- [ ] T017 [US1] Integrate `extract_features.py` with `data_loader.py` to process both Book Corpus and BEIR datasets
- [ ] T018a [US1] Fetch a small, verified code dataset (e.g., `codeparrot/github-code` sample) for FR-008 validation <!-- ATOMIZE: requested -->
- [ ] T018b [US1] Validate `FR-008`: Correlation check of `parse tree depth variance` vs code diversity (token-level entropy) on the fetched code sample; fallback to token-level entropy if correlation < 0.3. **If fallback is triggered, update data-model.md and spec.md to reflect the new metric.** <!-- FAILED: unspecified -->
- [ ] T019 [US1] Save feature matrices to `data/processed/` with checksums

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Proxy Correlation Analysis (Priority: P2)

**Goal**: Correlate diversity profiles with available proxy targets (BEIR relevance scores, Book Corpus text length) since ground-truth collapse labels are missing.

**Independent Test**: Train a simple Ridge regression on Book Corpus features vs. text length; verify non-trivial correlation (MAE < threshold) on held-out split.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [US2] Unit test for correlation coefficient calculation in `tests/unit/test_correlations.py`

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement `code/pipelines/analyze_correlations.py`: load source (Book Corpus) features and proxy targets (`text_length` column)
- [ ] T022 [US2] Implement correlation analysis (Pearson/Spearman) between diversity metrics and proxy targets (relevance scores for BEIR, text length for Book Corpus)
- [ ] T023 [US2] **Document Scope Gap**: Write `data/results/blocking_gap_report.md` with sections: Gap Description, Impact on FR-002/004/007, Proxy Strategy, and Confirmation of Valid Proxy Targets. **This task must confirm valid proxy targets exist (p-value < 0.05, |correlation| > 0.2) before T024-T028 can proceed.**
- [ ] T024 [US2] Compute baseline performance: correlation using mean proxy value vs. diversity-based ranking (satisfies SC-001)
- [ ] T025a [US2] **Implement Permutation Test**: Implement permutation test function in `code/utils/stats.py` to test correlation against the *proxy* null distribution (shuffling relevance scores/text length) with permutations.
- [ ] T026 [US2] **Measure FPR on Proxy Binary Classes**: Calculate False Positive Rate for predicting 'low relevance' (proxy collapse) vs 'high relevance' on the source dataset. **CRITICAL**: This task explicitly acknowledges that SC-002 (FPR for 'collapse prediction') cannot be satisfied due to missing ground truth. The task must record the proxy FPR and add a specific entry to `blocking_gap_report.md` stating: "SC-002 (Collapse FPR) unmeasurable; Proxy FPR reported as substitute."
- [ ] T027 [US2] Record source performance metrics (correlation coefficients) to `data/results/source_metrics.json`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generalization Validation (Priority: P3)

**Goal**: Apply source-domain correlation patterns to target-domain (BEIR) to verify if static diversity profiles generalize across domains.

**Independent Test**: Apply Book Corpus correlation coefficients to BEIR features; verify correlation with BEIR proxy targets is within acceptable generalization gap (SC-005).

**⚠️ CRITICAL**: Phase 5 tasks depend on T023 confirming valid proxy targets exist. If T023 reports 'No valid proxy', halt Phase 5.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Integration test for cross-dataset generalization in `tests/integration/test_generalization.py`

### Implementation for User Story 3

- [ ] T029 [P] [US3] Load target (BEIR) feature matrix and proxy targets (`relevance_score` column) in `code/pipelines/analyze_correlations.py` (Output of T017 and T019).
- [ ] T030 [US3] **Apply Source Logic & Run Permutation Test**: Apply source-domain correlation logic to target data without re-training (satisfies FR-005). **Must call the permutation test function implemented in T025a to validate the target correlation against the null distribution (satisfies FR-006 and SC-004).** Calculate generalization gap (Source Performance vs. Target Performance) and record to `data/results/generalization_report.json`.
- [ ] T033 [US3] **Validate Independent Stability Forecast**: Validate FR-007 by comparing predicted 'proxy stability' (variance of relevance scores) against observed variance in target proxy data.
- [ ] T034 [US3] **Measure Forecast Accuracy for Proxy Stability**: Calculate accuracy of forecasting 'proxy stability' (variance of relevance scores) against observed values, satisfying the **amended SC-006** which defines the target as proxy stability.
- [ ] T035 [US3] Generate final `research.md` update with all metrics, blocking gaps, and generalization findings

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates: Add `quickstart.md` with steps to run full pipeline
- [ ] T037 Code cleanup and refactoring of `code/metrics/` modules
- [ ] T038 Performance optimization: Ensure total runtime < 6 hours on CPU-only runner
- [ ] T039 [P] Additional unit tests for data loading and schema validation in `tests/unit/`
- [ ] T040 Run `quickstart.md` validation to ensure end-to-end reproducibility
- [ ] T041 Update `state/` timestamps upon artifact generation (Constitution Principle V)

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (T019)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data output (T019) and US2 logic (T023 confirmation)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Helpers before pipelines
- Pipelines before integration
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
Task: "Unit test for distinct-4 ratio calculation in tests/unit/test_lexical.py"
Task: "Unit test for parse tree depth variance in tests/unit/test_syntactic.py"

# Launch all models for User Story 1 together:
Task: "Implement code/metrics/lexical.py: distinct-4 ratio and n-gram entropy functions"
Task: "Implement code/metrics/syntactic.py: parse tree depth variance using en_core_web_sm"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (Feature extraction works, CPU-only)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Proxy analysis)
4. Add User Story 3 → Test independently → Deploy/Demo (Generalization)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Metrics & Extraction)
 - Developer B: User Story 2 (Source Correlation)
 - Developer C: User Story 3 (Target Generalization)
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
- **Critical Constraint**: All tasks must run on CPU-only CI with limited cores and constrained memory.. No GPU, no 8-bit models, no large LLMs.
- **Data Constraint**: Use only verified datasets (`tr-books-tokenized`, `Tr-beir-formatted`) from HuggingFace. Do not fabricate data.
- **Scope Constraint**: Explicitly acknowledge missing ground-truth sweep logs; do not attempt to train a collapse predictor. Use proxy correlation analysis instead.
- **Proxy Targets**: BEIR uses `relevance_score`, Book Corpus uses `text_length` as proxy targets for analysis.
- **Blocking Condition**: If T023 (Scope Gap Report) confirms no valid proxy exists, Phase 5 (Generalization) is halted.