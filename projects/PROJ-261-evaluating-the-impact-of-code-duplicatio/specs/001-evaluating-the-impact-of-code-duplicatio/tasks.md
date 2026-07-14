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
- [X] T003 [P] Configure linting and formatting tools (black, flake8, isort) in `.pre-commit-config.yaml`
- [X] T004 [P] Create `research.md` documentation artifact in `specs/001-evaluate-code-duplication-llm-understanding/` with literature review and research question justification
- [X] T005 [P] Create `data-model.md` documentation artifact in `specs/001-evaluate-code-duplication-llm-understanding/` with entity definitions and data flow diagrams

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 [P] Implement `projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/config.py` for seeds, thresholds, and model parameters
- [X] T007 [P] Setup data directory structure (`projects/PROJ-261-evaluating-the-impact-of-code-duplication/data/raw`, `.../processed`, `.../analysis`)
- [X] T008 [P] Configure logging infrastructure for parse failures (logs to `projects/PROJ-261-evaluating-the-impact-of-code-duplication/data/parse_failures.csv`)
- [X] T009 [P] Create checksum state manifest infrastructure in `projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/checksum_manifest.py` with `artifact_hashes` tracking
- [X] T010 [P] Create contract schema files: `clone_metrics.schema.yaml`, `model_metrics.schema.yaml`, `correlation_results.schema.yaml`, `pipeline_config.schema.yaml` in `specs/001-evaluate-code-duplication-llm-understanding/contracts/`
- [X] T011 [P] Implement contract tests for all schemas in `projects/PROJ-261-evaluating-the-impact-of-code-duplication/tests/contract/`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute Clone Density and Model Perplexity (Priority: P1) 🎯 MVP

**Goal**: Download corpus, compute AST clone density, and measure token‑level perplexity

**Independent Test**: Must be written **before** any implementation code and verified to fail.

### Test Tasks (must appear **before** any implementation tasks)

- [X] T012 [US1] Unit test for syntax‑error handling in Python files (`projects/PROJ-261-evaluating-the-impact-of-code-duplication/tests/unit/test_ast_cloner.py`) using pytest - **COMPLETED** (file exists and contains tests)
- [X] T013 [US1] Unit test for NaN/infinite perplexity value detection (`projects/PROJ-261-evaluating-the-impact-of-code-duplication/tests/unit/test_model_metrics.py`) using pytest
- [X] T014 [US1] Unit test for PII scan detection (`projects/PROJ-261-evaluating-the-impact-of-code-duplication/tests/unit/test_pii_scanner.py`) using pytest
- [X] T015a [US1] Integration test for HuggingFace rate‑limiting and network‑interruption handling during 500 MB download [UNRESOLVED-CLAIM: c_c641f793 — status=not_enough_info] (`projects/PROJ-261-evaluating-the-impact-of-code-duplication/tests/integration/test_data_loader.py`) using pytest
- [X] T015b [US1] Integration test for pipeline on a Integration test for pipeline on a small sample (10 files) verifying clone‑density and perplexity CSV output [UNRESOLVED-CLAIM: c_b65b81c9 — status=not_enough_info] (`projects/PROJ-261-evaluating-the-impact-of-code-duplication/tests/integration/test_us1_small_sample.py`) using pytest
- [X] T016a [US1] Edge‑case test for parse‑failure logging (`projects/PROJ-261-evaluating-the-impact-of-code-duplication/tests/unit/test_parse_failures.py`) using pytest
- [X] T016b [US1] Edge‑case test for zero‑clone‑density handling (`projects/PROJ-261-evaluating-the-impact-of-code-duplication/tests/unit/test_zero_clone_density.py`) using pytest
- [X] T016c [US1] Edge‑case test for model‑loading failure in 8‑bit quantization (`projects/PROJ-261-evaluating-the-impact-of-code-duplication/tests/unit/test_model_metrics.py`) using pytest

### Implementation Tasks (sequential – data flow requires order)

- [X] T018 [US1] stream `codeparrot/github-code` (500 MB subset) using HuggingFace datasets library with streaming mode enabled [UNRESOLVED-CLAIM: c_1e877f51 — status=not_enough_info] with streaming mode enabled
- [X] T017 [US1] Implement `projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/pii_scanner.py` to scan all files under `data/` including `raw/`, `processed/`, and `analysis/` subdirectories for PII patterns per Constitution Principle III (must run after T018 completes)
- [X] T019 [US1] Implement `projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/ast_cloner.py` to parse Python files via the built‑in `ast` module, classify clones by type (Type‑1 exact copy, Type‑2 parameterized copy), and compute clone density (stdlib only - verify no external dependencies in implementation)
- [X] T020 [US1] Implement `projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/model_metrics.py` to load `Salesforce/codegen-350M-mono` in 8‑bit quantization using bitsandbytes and compute perplexity
- [X] T021 [US1] Implement `projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/main.py` pipeline orchestration to join clone‑density and perplexity metrics, saving to `projects/PROJ-261-evaluating-the-impact-of-code-duplication/data/processed/clone_metrics.csv` and `.../perplexity_scores.csv` <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [X] T022 [US1] Add error handling for parse failures (log to `data/parse_failures.csv`), NaN/infinite perplexity values, network interruptions, and syntax errors (implementation layer - distinct from test tasks T012, T013, T015a, T016a-c)
- [X] T023 [US1] Memory‑monitoring validates a 7 GB limit throughout model inference [UNRESOLVED-CLAIM: c_d816300d — status=not_enough_info]
- [X] T024 [US1] SC‑001 validation includes a 500 MB corpus requirement (`projects/PROJ-261-evaluating-the-impact-of-code-duplication/tests/integration/test_performance.py`) using pytest
- [X] T025 [US1] Add checksum computation for all output files AND intermediate files/logs, record in `artifact_hashes` state manifest
- [X] T026 [US1] SC‑003 claim of 2409.08555 from arXiv 2409.08555 [UNRESOLVED-CLAIM: c_cd457742 — status=not_enough_info] (`projects/PROJ-261-evaluating-the-impact-of-code-duplication/tests/integration/test_segment_count_validation.py`) using pytest (`projects/PROJ-261-evaluating-the-impact-of-code-duplication/tests/integration/test_segment_count_validation.py`) using pytest
- [X] T053 [US1] Implement semantic distance calculation in `projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/model_metrics.py` (or `code/semantic_cloner.py`) per FR-003 using embedding-based similarity, and add a corresponding unit test in `projects/PROJ-261-evaluating-the-impact-of-code-duplication/tests/unit/test_model_metrics.py`

**Checkpoint**: User Story 1 should now be fully functional and testable independently

---

## Phase 4: User Story 2 - Evaluate Bug Detection Accuracy and Calculate Correlation (Priority: P2)

**Goal**: Evaluate bug detection on HumanEval and calculate Spearman correlation

**Independent Test**: Must be written before implementation.

### Test Tasks

- [X] T027 [US2] Contract test for correlation schema (`projects/PROJ-261-evaluating-the-impact-of-code-duplication/tests/contract/test_correlation_schema.py`) using pytest
- [X] T028 [US2] Integration test for end‑to‑end correlation pipeline (`projects/PROJ-261-evaluating-the-impact-of-code-duplication/tests/integration/test_pipeline_end_to_end.py`) using pytest
- [X] T029 [US2] Unit test for bug_detection.py pass@1 accuracy calculation (`projects/PROJ-261-evaluating-the-impact-of-code-duplication/tests/unit/test_bug_detection.py`) using pytest
- [X] T030 [US2] Unit test for correlation_analysis.py Spearman coefficient computation (`projects/PROJ-261-evaluating-the-impact-of-code-duplication/tests/unit/test_correlation_analysis.py`) using pytest

### Implementation Tasks

- [ ] T031 [US2] Implement `projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/bug_detection.py` to load the 50‑problem HumanEval subset, retrieve the associated clone density metric for each problem from the processed metrics, and compute pass@1 accuracy, ensuring clone density is stored as a float type to match correlation analysis requirements.
- [X] T032 [US2] Implement `projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/correlation_analysis.py` to calculate Spearman rank correlation between duplication density and both perplexity and accuracy
- [X] T033 [US2] Join all intermediate metrics (clone, perplexity, bug‑detection) for correlation input
- [X] T034 [US2] Save correlation results with p‑values to `projects/PROJ-261-evaluating-the-impact-of-code-duplication/data/analysis/correlation_results.csv`
- [X] T035 [US2] Add validation task to verify **SC‑004** – ({{claim:c_5bb2307c}}) documented (`projects/PROJ-261-evaluating-the-impact-of-code-duplication/tests/integration/test_significance.py`) using pytest
- [X] T036 [US2] Add checksum computation for correlation results and record in `artifact_hashes` state manifest

**Checkpoint**: User Stories 1 & 2 should both work independently

---

## Phase 5: User Story 3 - Perform Sensitivity Analysis and Generate Visualizations (Priority: P3)

**Goal**: Sensitivity analysis across thresholds and publication‑ready visualizations

**Independent Test**: Must be written before implementation.

### Test Tasks

- [X] T037 [US3] Unit test for visualization generation (`projects/PROJ-261-evaluating-the-impact-of-code-duplication/tests/unit/test_visualization.py`) using pytest
- [X] T038 [US3] Unit test for sensitivity analysis across thresholds 0.7, 0.8, 0.9 (`projects/PROJ-261-evaluating-the-impact-of-code-duplication/tests/unit/test_correlation_analysis.py`) - distinct from T030 which tests Spearman coefficient computation only, using pytest
- [X] T039 [US3] Integration test for scatter‑plot output format validation (`projects/PROJ-261-evaluating-the-impact-of-code-duplication/tests/integration/test_visualization_output.py`) using pytest

### Implementation Tasks

- [X] T040 [US3] Extend `projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/correlation_analysis.py` to perform sensitivity analysis for clone‑detection thresholds 0.7, 0.8, 0.9
- [X] T041 [US3] Implement `projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/visualization.py` to generate scatter plots with regression lines using matplotlib
- [X] T042 [US3] Save all plots to `projects/PROJ-261-evaluating-the-impact-of-code-duplication/data/analysis/figures/` in documented format (PNG & PDF)
- [X] T043 [US3] Document random seeds, thresholds (0.7, 0.8, 0.9 explicitly called out), and **ALL** configuration parameters in `projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/config.py` for reproducibility (SC‑005) - T006 creates config.py infrastructure, T043 documents parameters for reproducibility with explicit threshold documentation
- [X] T044 [US3] Add checksum computation for visualization outputs and record in `artifact_hashes` state manifest

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T045 [P] Documentation updates in `specs/001-evaluate-code-duplication-llm-understanding/quickstart.md`
- [X] T046 Code cleanup and refactoring across `projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/`
- [X] T047 [P] Additional integration tests in `projects/PROJ-261-evaluating-the-impact-of-code-duplication/tests/integration/`
- [X] T048 Run quickstart validation to ensure reproducibility steps work
- [X] T049 [P] Run pytest on Linux/GitHub Actions platform to validate platform compatibility
- [X] T050 [P] Document parallel execution opportunities and team capacity planning in `specs/001-evaluate-code-duplication-llm-understanding/quickstart.md`
- [X] T051 Map Constitution Check principles to concrete task IDs for traceability (`projects/PROJ-261-evaluating-the-impact-of-code-duplication/tasks.md` includes a table linking each principle to the tasks that satisfy it)
- [X] T052 [US1] Add explicit validation task to verify **SC‑007** (no PII patterns found; any detected are logged and flagged) (`projects/PROJ-261-evaluating-the-impact-of-code-duplication/tests/integration/test_pii_validation.py`) using pytest

---

## Phase Dependencies & Execution Order

**Data Flow Ordering (MANDATORY - 6-Stage Computational Pipeline)**
1. **Data Download**: T018 → T017 (PII scan requires data to exist)
2. **Clone Detection**: T019 → T021 (clone_metrics.csv)
3. **Model Inference**: T020 → T021 (perplexity_scores.csv)
4. **Bug Detection**: T031 → T032 (bug_detection_results.csv)
5. **Correlation Analysis**: T032 → T034 → T035 (correlation_results.csv)
6. **Visualization**: T040 → T041 → T042 (figures/)

**Full Task Order by Data Dependency**:
T018 → T017 → T019 → T020 → T021 → T022 → T023 → T024 → T025 → T026 → T031 → T032 → T033 → T034 → T035 → T036 → T040 → T041 → T042 → T043 → T044

**Parallel Opportunities**
- All Setup tasks `[P]` can run in parallel
- All Foundational tasks `[P]` can run in parallel
- All test tasks for a given user story can run in parallel
- Visualization and sensitivity analysis tasks can run in parallel once correlation results are available

**Path Consistency**
All file references now use the full repository‑root‑relative path `projects/PROJ-261-evaluating-the-impact-of-code-duplication/...` as required by `plan.md`.

**Edge‑Case Coverage**
Each of the six edge cases listed in `spec.md` now has a dedicated task (T012, T013, T014, T015a, T016a‑c, T023).

**Success‑Criterion Validation**
- SC‑001 validation is performed by T024 (with 500MB corpus verification)
- SC‑002 memory monitoring is T023
- SC‑003 segment‑count validation is T026 (NEW - {{claim:c_65dd4ded}})
- SC‑004 significance‑threshold check is T035
- SC‑005 reproducibility documentation is T043 (with explicit threshold documentation for 0.7, 0.8, 0.9)
- SC‑006 checksum tracking is implemented by T025, T036, T044 (now covers intermediate files and logs)
- SC‑007 PII‑scan handling is T017 (data loader must run first), validation by T052 (explicit validation task)

**Constitution Traceability**
Task T051 provides the mapping between Constitution Check and concrete task IDs.

| Principle | Task IDs |
|-----------|----------|
| I. Reproducibility | T002, T006, T043 |
| II. Verified Accuracy | T029, T030, T034, T035 |
| III. Data Hygiene | T014, T017, T025, T036, T044 |
| IV. Single Source of Truth | T021, T025, T036, T044 |
| V. Versioning Discipline | T025, T036, T044 |
| VI. Statistical Correlation Integrity | T032, T034, T035 |
| VII. Clone Detection Consistency | T019, T040 |
