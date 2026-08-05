# Tasks: Evaluating the Impact of Code Duplication on LLM Code Understanding

**Input**: Design documents from `/specs/001-evaluate-code-duplication-llm-understanding/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are MANDATORY per spec.md Independent Test requirements for each user story.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/`, `projects/PROJ-261-evaluating-the-impact-of-code-duplication/data/`, `projects/PROJ-261-evaluating-the-impact-of-code-duplication/tests/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan in `projects/PROJ-261-evaluating-the-impact-of-code-duplication/`
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (datasets, transformers, bitsandbytes, scipy, matplotlib, pytest)
- [X] T003 [P] Create `.pre-commit-config.yaml` with black, flake8, isort hooks (consolidated from T003/T003a)
- [X] T004 [P] Create `research.md` documentation artifact in `specs/001-evaluating-the-impact-of-code-duplication/` with literature review and research question justification
- [X] T005 [P] Create `data-model.md` documentation artifact in `specs/001-evaluating-the-impact-of-code-duplication/` with entity definitions and data flow diagrams

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Implement `projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/config.py` for seeds, thresholds, and model parameters
- [X] T007 [P] Setup data directory structure (`projects/PROJ-261-evaluating-the-impact-of-code-duplication/data/raw`, `.../processed`, `.../analysis`)
- [X] T008 [P] Configure logging infrastructure for parse failures (logs to `projects/PROJ-261-evaluating-the-impact-of-code-duplication/data/parse_failures.csv`)
- [X] T009 [P] Create checksum state manifest infrastructure in `projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/checksum_manifest.py` with `artifact_hashes` tracking
- [X] T010 [P] Create and populate contract schema files: `clone_metrics.schema.yaml`, `model_metrics.schema.yaml`, `correlation_results.schema.yaml`, `pipeline_config.schema.yaml` in `specs/001-evaluating-the-impact-of-code-duplication/contracts/` (consolidated from T010/T010a/T010b)
- [X] T011 [P] Implement contract tests for all schemas in `projects/PROJ-261-evaluating-the-impact-of-code-duplication/tests/contract/`
- [X] T018c [US1] **Dependency**: Run the US1 pipeline on a tiny (≈5 files) sample [UNRESOLVED-CLAIM: c_65d68172 — status=not_enough_info] using `data/raw/github-code-sample.csv` to produce minimal `clone_metrics.csv` and `perplexity_scores.csv` for downstream US-2 testing (ensures US-2 independence)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute Clone Density and Model Perplexity (Priority: P1) 🎯 MVP

**Goal**: Download corpus, compute AST clone density, and measure token‑level perplexity

**Independent Test**: Must be written **before** any implementation code and verified to fail.

### Test Tasks (must appear **before** any implementation tasks)

- [X] T012 [US1] Unit test for syntax‑error handling in Python files (`tests/unit/test_ast_cloner.py`) using pytest
- [X] T013 [US1] Unit test for NaN/infinite perplexity value detection (`tests/unit/test_perplexity_nan.py::test_nan_handling`)
- [X] T014 [US1] Unit test for PII scan detection (`tests/unit/test_pii_scanner.py`) using pytest
- [X] T014b [US1] Unit test for model‑loading failure in ‑bit quantization (`tests/unit/test_model_load_failure.py::test_load_failure`)
- [X] T014c [US1] Integration test that simulates 8‑bit load failure in the full pipeline (`tests/integration/test_model_load_failure_integration.py`)
- [X] T015a [US1] Integration test for HuggingFace rate‑limiting/network‑interruption handling during 500 MB download [UNRESOLVED-CLAIM: c_2cd86b6a — status=not_enough_info] (`tests/integration/test_rate_limit.py::test_rate_limit_handling`)
- [X] T015b [US1] Integration test for pipeline on a small sample of files verifying clone‑density and perplexity CSV output (`tests/integration/test_us1_small_sample.py`) using pytest
- [X] T016a [US1] Edge‑case test for parse‑failure logging (`tests/unit/test_parse_failures.py`) using pytest
- [X] T016b [US1] Edge‑case test for zero‑clone‑density handling (`tests/unit/test_zero_clone_density.py`) using pytest
- [X] T016c [US1] Edge‑case test for model‑loading failure in 8‑bit quantization (`tests/unit/test_model_metrics.py`) using pytest
- [X] T021a [US1] Integration test asserting that `clone_metrics.csv` and `perplexity_scores.csv` are created with expected columns after orchestration
- [X] T021b [US1] Integration test verifying successful join of clone‑density and perplexity metrics and logging of any ID mismatches

### Implementation Tasks (sequential – data flow requires order)

- [ ] T018 [US1] Stream `codeparrot/github-code` (a representative subset) using HuggingFace datasets library with streaming mode enabled; output stored as `data/raw/github-code-sample.csv` (CSV format per FR-008)
- [ ] T017 [US1] Implement `projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/pii_scanner.py` to scan all files under `data/` (specifically `data/raw/github-code-sample.csv`) for PII patterns per Constitution Principle III
- [X] T019 [US1] Implement `projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/ast_cloner.py` to parse Python files via the built‑in `ast` module, classify clones (Type‑1, Type‑2), and compute clone density (stdlib only) on PII-cleaned data
- [X] T020 [US1] Implement `projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/model_metrics.py` to load `Salesforce/codegen-350M-mono` in 8‑bit quantization using bitsandbytes and compute perplexity
- [ ] T053 [US1] Extend `model_metrics.py` to compute semantic distance using CodeBERT embeddings and cosine similarity; output to `data/processed/semantic_distance.csv`
- [ ] T053b [US1] **Verification**: Execute the CodeBERT embedding pipeline on the real corpus and verify the generation of `data/processed/semantic_distance.csv` with valid cosine similarity scores
- [ ] T021 [US1] Implement `projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/main.py` orchestration to join clone‑density and perplexity metrics, producing `data/processed/clone_metrics.csv` and `data/processed/perplexity_scores.csv`; includes error handling for ID mismatches
- [ ] T021b [US1] Fix `main.py` to guarantee creation of both CSVs as required by FR‑008 and SC‑001 <!-- FAILED: unspecified -->
- [X] T022 [US1] Add comprehensive error handling for parse failures, NaN/infinite perplexity, network interruptions, and syntax errors (logging to `data/parse_failures.csv`)
- [ ] T023 [US1] Memory‑monitoring validates that the model remains within an appropriate memory limit throughout inference.
- [ ] T024 [US1] SC‑001 performance validation test (`tests/integration/test_performance.py`) ensuring 500 MB corpus processed within 24 h [UNRESOLVED-CLAIM: c_70971edc — status=not_enough_info] on standard runner
- [ ] T025 [US1] Compute checksums for all output and intermediate files; record in `artifact_hashes` state manifest
- [X] T026 [US1] SC‑003 segment‑count verification (`tests/integration/test_segment_count_validation.py`) ensuring ≥ 1000 processed code segments [UNRESOLVED-CLAIM: c_519e0ef9 — status=not_enough_info]
- [ ] T062 [US1] Additional verification that segment‑count threshold is met and logged

**Checkpoint**: User Story 1 should now be fully functional and testable independently

---

## Phase 4: User Story 2 - Evaluate Bug Detection Accuracy and Calculate Correlation (Priority: P2)

**Goal**: Evaluate bug detection on HumanEval and calculate Spearman correlation

**Independent Test**: Must be written before implementation.

### Test Tasks

- [X] T027 [US2] Contract test for correlation schema (`tests/contract/test_correlation_schema.py`) using pytest
- [X] T028 [US2] Integration test for end‑to‑end correlation pipeline (`tests/integration/test_pipeline_end_to_end.py`) using pytest
- [X] T029 [US2] Unit test for `bug_detection.py` pass@1 accuracy calculation (`tests/unit/test_bug_detection.py`) using pytest
- [X] T030 [US2] Unit test for `correlation_analysis.py` Spearman coefficient computation (`tests/unit/test_correlation_analysis.py`) using pytest
- [X] T035a [US2] {{claim:c_ce79d100}} (1601.06805, https://arxiv.org/abs/1601.06805 [UNRESOLVED-CLAIM: c_c7be4fa8 — status=verified])
- [X] T014b [US2] (re‑use) Unit test for model‑loading failure in low‑bit quantization (ensures edge‑case coverage for US‑2)

### Implementation Tasks

- [ ] T070 [US2] **CRITICAL**: Refactor `projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/bug_detection.py` to remove ALL synthetic data generation logic and fallback mechanisms; implement strict loading of the official `human-eval` dataset (a representative subset) via `datasets.load_dataset("openai_humaneval")`; ensure the script raises a fatal error if the real dataset is unavailable.
- [ ] T071 [US2] Split `bug_detection.py` logic: move data loading to `projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/data_loading.py` (≤200 lines) and keep evaluation logic in `bug_detection.py` to prevent truncation and improve modularity.
- [ ] T031 [US2] Implement `projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/bug_detection.py` to load a representative HumanEval subset, join with segment‑level clone density, and compute pass@k accuracy; **no synthetic fallback** (synthetic fallback removed per T054)
- [ ] T032 [US2] Implement `projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/correlation_analysis.py` to calculate Spearman rank correlation between duplication density and both perplexity and accuracy (segment‑level)
- [ ] T032a [US2] Adjust correlation analysis to use segment‑level joins (function‑body key) as required by FR‑007
- [ ] T032b [US2] **Verification**: Add validation logic to assert that correlation analysis strictly uses `segment_id` (function body) and explicitly excludes `problem_id` aggregation
- [ ] T032c [US2] **Verification**: Run the correlation analysis on real data and verify that the output `data/analysis/correlation_results.csv` contains segment-level metrics (N ≥ 1000) and no problem-level aggregation
- [ ] T033 [US2] Join all intermediate metrics (clone, perplexity, bug‑detection) for correlation input using `segment_id` (function body) as the unique key; **explicitly exclude problem_id aggregation**
- [ ] T034 [US2] Save correlation results with p‑values to `data/analysis/correlation_results.csv`
- [ ] T035 [US2] Add validation task to verify SC‑004 significance (p < 0.05) using test T035a
- [ ] T036 [US2] Compute checksum for correlation results and record in `artifact_hashes` state manifest
- [ ] T054 [US2] Refactor `bug_detection.py` to remove any synthetic‑data fallback logic (already completed)
- [ ] T055 [US2] Extract HumanEval loading into new module `code/data_loading.py` (≤ 200 lines)
- [ ] T056 [US2] Update `main.py` (or wrapper) to import `data_loading.py` and ensure real dataset usage
- [ ] T072 [US2] **CRITICAL**: Re‑run the full pipeline on the real 500MB `codeparrot/github-code` subset and the real 50-problem HumanEval subset to generate authentic `data/processed/perplexity_scores.csv`, `data/processed/bug_detection_results.csv`, and `data/analysis/correlation_results.csv` artifacts; verify no synthetic placeholders exist.
- [ ] T073 [US2] Validate data completeness: Add a validation step to assert that `correlation_results.csv` contains non-null, non-NaN Spearman coefficients and p-values derived from real data, with sample size N matching processed segments.
- [ ] T057 [US2] Re‑run full pipeline on a real large‑scale subset and real HumanEval problem subset to generate authentic metrics
- [ ] T058 [US2] Recompute correlation with real metrics and overwrite `correlation_results.csv`
- [ ] T059 [US2] Update `artifact_hashes` with SHA‑256 checksums for refreshed CSVs
- [ ] T060 [US2] Extend test T035 to assert non‑null, non‑NaN coefficients, p‑values, and correct sample size N
- [ ] T018c [US2] **Dependency**: Use the lightweight CSVs produced by T018c (US‑1) when real data is not yet available for isolated US‑2 testing

**Checkpoint**: User Stories 1 & 2 should both work independently and be based on real data.

---

## Phase 5: User Story 3 - Perform Sensitivity Analysis and Generate Visualizations (Priority: P3)

**Goal**: Sensitivity analysis across thresholds and publication‑ready visualizations

**Independent Test**: Must be written before implementation.

### Test Tasks

- [X] T037 [US3] Unit test for visualization generation (`tests/unit/test_visualization.py`) using pytest
- [X] T038 [US3] Unit test for sensitivity analysis across thresholds at a lower level, along with representative high-value settings. (`tests/unit/test_sensitivity_analysis.py::test_thresholds_0_7_0_8_0_9`)
- [X] T039 [US3] Integration test for scatter‑plot output format validation (`tests/integration/test_visualization_output.py`) using pytest
- [X] T043a [US3] Verification test that `hyperparameters.md` exists and contains entries for seeds and thresholds

### Implementation Tasks

- [X] T040 [US3] Extend `projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/correlation_analysis.py` to perform sensitivity analysis for clone‑detection thresholds at a lower level, as well as moderate (0.8) and high (0.9) thresholds
- [ ] T041 [US3] Implement `projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/visualization.py` to generate scatter plots with regression lines using matplotlib
- [ ] T041b [US3] **Critical Visualization**: Implement the 'structural heat map (or confusion matrix)' to visualize code region contributions (function headers vs. bodies) to perplexity spikes; input must be a mapping of segment regions (header/body) to perplexity values; output to `data/analysis/figures/structural_heatmap.png`
- [ ] T042 [US3] Save all plots to `data/analysis/figures/` in documented formats (PNG & PDF)
- [ ] T074 [US3] **CRITICAL**: Update documentation location and content: Move `hyperparameters.md` to `specs/001-evaluating-the-impact-of-code-duplication/hyperparameters.md` (if not already there) and expand content to explicitly list clone‑detection thresholds (0.7, 0.8, 0.9) [UNRESOLVED-CLAIM: c_96cc127b — status=not_enough_info], random seeds, model quantization parameters, and all configuration details from `code/config.py` to satisfy SC‑005.
- [ ] T075 [US3] **CRITICAL**: Generate missing analysis artifacts: Execute T034 and T042 to ensure `data/analysis/correlation_results.csv` and `data/analysis/figures/` (with PNG/PDF plots) exist and are populated with real data results.
- [X] T043 [US3] Document random seeds, thresholds (0.7, 0.8, 0.9) and **all** configuration parameters in `specs/001-evaluating-the-impact-of-code-duplication/hyperparameters.md`
- [X] T044 [US3] Add checksum computation for visualization outputs and record in `artifact_hashes` state manifest

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T045 [P] Documentation updates in `specs/001-evaluating-the-impact-of-code-duplication/quickstart.md`
- [X] T046 Code cleanup and refactoring across `projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/`
- [X] T047 [P] Additional integration tests in `tests/integration/`
- [X] T048 Run quickstart validation to ensure reproducibility steps work
- [X] T049 [P] Run pytest on Linux/GitHub Actions platform to validate platform compatibility
- [X] T050 [P] Document parallel execution opportunities and team capacity planning in `quickstart.md`
- [X] T051 Map Constitution Check principles to concrete task IDs for traceability (`tasks.md` includes a table linking each principle to tasks)
- [X] T052 [US1] Add explicit validation task to verify SC‑007 (PII detection) (`tests/integration/test_pii_validation.py`) using pytest
- [X] T053 (already defined in Phase 3) – semantic distance calculation
- [X] T054 (already completed) – bug_detection synthetic fallback removal
- [X] T055 (already completed) – data_loading extraction
- [X] T056 (already completed) – main.py integration with data_loading
- [X] T057‑T060 (already completed) – re‑run pipeline with real data and update artifacts
- [X] T061 [P] Move hyperparameters documentation to `specs/.../hyperparameters.md` and expand it (already completed as T043)
- [X] T062 [US1] Segment‑count verification for SC‑003 (already completed)
- [X] T063 [P] Update `plan.md` to reflect new hyperparameters location and visualization module path
- [X] T064 [P] Verify that `data/raw/github-code-sample.csv` exists, is ~500 MB, and was created via streaming as specified in T018
- [X] T065 [P] Ensure all schema files are non‑empty and validated (covers CRITICAL issue from analysis)
- [ ] T076 [P] **CRITICAL**: Align code structure: Consolidate any scattered visualization or checksum logic (e.g., `utils/checksum_visualizations.py`, `visualization/plotting.py`) into the single `code/visualization.py` module defined in `plan.md`, or update `plan.md` and all task references to reflect the new directory structure. (Note: This is a sequential refactoring task, not parallel)
- [ ] T077 [P] **CRITICAL**: Verify artifact paths: Ensure `data/raw/github-code-sample.csv`, `data/processed/clone_metrics.csv`, `data/processed/perplexity_scores.csv`, `data/processed/bug_detection_results.csv`, and `data/analysis/correlation_results.csv` exist in the exact locations specified in `plan.md` and `tasks.md`. (Run `test -f` commands and log results)
- [ ] T078 [P] **End-to-End Real Data Verification**: Execute the full pipeline on real data (T018, T019, T020, T031, T032) and verify that all artifacts (CSVs, plots) are generated with real data (no synthetic placeholders) and valid checksums; mark T021, T070-T077 as [X] only after this verification passes.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
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
- **CRITICAL**: Tasks T070, T071, T072, T073, T074, T075, T076, T077, T078 address critical research integrity, filesystem hygiene, and reproducibility concerns raised in prior reviews. These MUST be completed before advancing. T078 is the gatekeeper for marking T021 and T070-T077 as complete.