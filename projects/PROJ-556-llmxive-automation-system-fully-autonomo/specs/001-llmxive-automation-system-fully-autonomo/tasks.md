# Tasks: llmXive Automation System (001-gene-regulation)

**Input**: Design documents from `/specs/001-gene-regulation/`
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

- [X] T001 Create project structure per implementation plan
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pandas, scikit-learn, sentence-transformers, datasets, scipy, statsmodels, pyyaml, pytest)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `data/`, `code/`, `lit_search/`, `src/`, `tests/` directory structure
- [ ] T005 [P] Implement `src/utils/seed.py` for deterministic seed management (global seed setting)
- [ ] T006 [P] Create `src/config/arch_configs.yaml` defining structural parameters (context window, model size, retrieval toggle)
- [ ] T007 Create base schema contracts in `contracts/` (hypothesis.schema.yaml, execution_log.schema.yaml, dataset_schema.schema.yaml)
- [ ] T008 Implement `src/utils/data_loader.py` skeleton for dataset ingestion & sampling
- [ ] T009 Setup environment configuration management for CPU-only constraints
- [ ] T010 [P] Implement `src/utils/corpus_builder.py` to fetch and index post-cutoff literature using `all-MiniLM-L6-v2` (CPU-tractable)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Automated Hypothesis Generation and Novelty Scoring (Priority: P1) 🎯 MVP

**Goal**: Ingest datasets, generate hypotheses via LLM, and compute novelty scores against a literature corpus.

**Independent Test**: The system can be tested by running the pipeline on a single, small UCI dataset with a fixed seed. The test passes if it outputs a CSV containing the generated hypotheses and their corresponding novelty scores derived from semantic similarity., without requiring code execution or human intervention.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T011 [P] [US1] Contract test for hypothesis schema validation in `tests/contract/test_hypothesis_schema.py`
- [ ] T012 [P] [US1] Integration test for pipeline smoke run on `uci_breast_cancer.csv` in `tests/integration/test_smoke_pipeline.py`

### Implementation for User Story 1

- [ ] T013 [US1] Implement `src/agents/brainstorm.py` to generate hypotheses using CPU-tractable LLM (distilled model or API) with configurable temperature
- [ ] T014 [US1] Implement `src/agents/scorer.py` to compute cosine similarity against the frozen literature index; include logic to handle empty corpus (default score 0.5, flag 'non_novel'). **Depends on T010 completion.**
- [ ] T015 [P] [US1] Implement static plausibility check in `src/agents/scorer.py` to verify variable existence against dataset schema and logical plausibility (e.g., preventing "correlate X with itself") as mandated by FR-010
- [ ] T015b [US1] Implement explicit variable existence validation in `src/agents/scorer.py` to ensure all variables in generated hypotheses exist in the dataset schema, enabling SC-001 measurement of hallucinated citations. **Depends on T008 and T007.**
- [ ] T016 [P] [US1] Create and populate `data/manual_hypotheses.csv` with human-authored hypotheses to serve as input for the human baseline task
- [ ] T017 [US1] Implement "Human Baseline" generator (FR-008): read 5 manual hypotheses from `data/manual_hypotheses.csv`, score them using the same novelty metric, and append results to `results.csv`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Reproducibility Validation via Code Execution (Priority: P2)

**Goal**: Generate executable Python code for hypotheses, execute in sandbox, and log outcomes.

**Independent Test**: The system can be tested by taking a single hypothesis, generating the corresponding code, and executing it in a sandboxed container. The test passes if the system correctly categorizes the result as "Pass" or "Fail" and logs the specific error type.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for execution log schema in `tests/contract/test_execution_log_schema.py`
- [ ] T019 [P] [US2] Integration test for code execution sandbox with timeout and error capture in `tests/integration/test_executor.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement `src/agents/coder.py` to generate Python scripts using standard libraries (pandas, scipy, sklearn)
- [ ] T021 [P] [US2] Implement pre-execution static analysis in `src/core/executor.py` (FR-010) to verify variable existence and logical plausibility. **Depends on T007, T008.**
- [ ] T022 [US2] Implement `src/core/executor.py` with a configurable timeout, `MemoryError` retry logic (sample data), and error categorization
- [ ] T023 [US2] Implement "Turing Verifier" logic in `src/core/executor.py` to detect non-deterministic outputs via repeated runs (3x)
- [ ] T024 [US2] Add logging for all execution outcomes (Pass, Fail, DependencyError, RuntimeError, NonDeterministic, ResourceExceeded)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Structural Correlation and Statistical Analysis (Priority: P3)

**Goal**: Aggregate results, perform statistical regression, and correlate ArchConfig variations with failure rates.

**Independent Test**: The system can be tested by providing a pre-generated CSV of results containing columns for `model_config`, `novelty_score`, and `reproducibility_status`.. The test passes if the system outputs a summary report containing p-values and correlation coefficients.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Contract test for statistical output schema in `tests/contract/test_stats_schema.py`
- [ ] T026 [P] [US3] Integration test for mixed-effects modeling on synthetic data in `tests/integration/test_stats_pipeline.py`

### Implementation for User Story 3

- [ ] T027 [P] [US3] Implement `src/core/stats.py` with Shapiro-Wilk normality check and fallback to non-parametric methods (Kruskal-Wallis)
- [ ] T028 [US3] Implement Linear Mixed-Effects Models (LMM) in `src/core/stats.py` with random intercepts per dataset and fixed effects for ArchConfig
- [ ] T029 [US3] Implement Benjamini-Hochberg FDR correction for multiple comparisons as mandated by plan.md (replacing Bonferroni) to control false discovery rate
- [ ] T030 [US3] Implement sensitivity analysis module (FR-009) to vary embedding models/thresholds and report correlation shifts
- [ ] T031 [US3] **Aggregate Metrics**: Compute SC-002 (Reproducibility Failure Rate) from execution logs and SC-003 (Statistical Significance) from LMM results; write to `data/aggregated_metrics.json`
- [ ] T032 [US3] Generate final report with p-values, confidence intervals, and explicit "No significant correlation found" statements where applicable

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Manual Annotation & Validation (Priority: P4)

**Goal**: Validate novelty scorer accuracy via human annotation and ensure contract compliance.

**Independent Test**: Select a representative sample of hypotheses, employ two independent annotators, and compute Cohen's Kappa to verify false-positive rate.

### Implementation for User Story 4

- [ ] T033 [US4] Implement manual annotation workflow script: select a representative subset of hypotheses via stratified random sampling (proportional allocation per dataset) from the full pipeline results and output to `data/annotation_queue.jsonl` with schema: `{hypothesis_id, dataset_id, source_text}`
- [ ] T034 [US4] Implement Cohen's Kappa calculator in `src/utils/metrics.py` to compare annotator agreement
- [ ] T035 [US4] Run single-dataset smoke test: execute `python -m src.cli.main --smoke-test --dataset uci_breast_cancer` and verify `runtime_log.json` shows CPU seconds within limits (SC-005). **Note: Spec defines single dataset for validation.**
- [ ] T036 [US4] Validate all outputs against `contracts/*.schema.yaml` and checksum raw data

---

## Phase 7: Philosophical & Architectural Safeguards (Priority: P5)

**Goal**: Implement advanced validation layers (Lovelace, Turing, Feedback, etc.) to ensure system robustness and detect epistemic drift.

- [ ] T037 [P] [US5] Implement "Lovelace Distinction" check in `src/agents/origin_tracker.py` to verify hypotheses are not mere rephrasings of training data. **Depends on T013, T014.**
- [ ] T038 [P] [US5] Implement "Turing Verifier" extended check in `src/agents/origin_tracker.py` to detect non-deterministic outputs and logical inconsistencies across runs. **Depends on T022, T023.**
- [ ] T039 [P] [US5] Implement "Feedback Monitor" in `src/agents/feedback_monitor.py` to detect epistemic drift by tracking the semantic distance of generated hypotheses over time. **Depends on T013, T014.**
- [ ] T040 [P] [US5] Implement "Dyson Scaling" check in `src/agents/scaling_analyzer.py` to evaluate performance degradation with increasing dataset complexity. **Depends on T013.**
- [ ] T041 [P] [US5] Implement "West Scaling Analysis" in `src/agents/scaling_analyzer.py` to correlate model size with novelty scores. **Depends on T031.**
- [ ] T042 [P] [US5] Implement "Wolfram Empirical Mining" in `src/agents/mining_agent.py` to identify patterns in failure modes. **Depends on T013-T032.**
- [ ] T043 [P] [US5] Implement "Exaptation Detector" in `src/agents/exaptation_detector.py` to find unexpected utility in generated hypotheses. **Depends on T013, T014.**

**Checkpoint**: Advanced validation layers complete.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T044 [P] Documentation updates in `docs/` and `quickstart.md`
- [ ] T045 Code cleanup and refactoring
- [ ] T046 Performance optimization for CPU-only constraints
- [ ] T047 Additional unit tests in `tests/unit/`
- [ ] T048 Security hardening (dependency pinning, sandbox isolation verification)
- [ ] T049 Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Manual Annotation (Phase 6)**: Depends on US1 and US2 completion
- **Philosophical Safeguards (Phase 7)**: Depends on US1, US2, US3 completion
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Contracts before services
- Services before endpoints
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
Task: "Contract test for hypothesis schema validation in tests/contract/test_hypothesis_schema.py"
Task: "Integration test for pipeline smoke run on uci_breast_cancer.csv in tests/integration/test_smoke_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement src/agents/brainstorm.py"
Task: "Implement src/agents/scorer.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Hypothesis Gen + Novelty)
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
 - Developer A: User Story 1 (Hypothesis/Novelty)
 - Developer B: User Story 2 (Code Execution)
 - Developer C: User Story 3 (Stats/Research Integration)
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
- **Critical Constraint**: All LLM inference and data processing MUST be CPU-tractable (no CUDA, no 8-bit quantization, no large model fine-tuning).
- **Critical Constraint**: All data must be real (UCI/HuggingFace) and results must be measured, never synthesized or faked.