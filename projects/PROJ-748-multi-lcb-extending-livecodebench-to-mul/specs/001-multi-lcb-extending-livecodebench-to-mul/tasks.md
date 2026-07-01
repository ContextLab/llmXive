# Tasks: Multi-LCB: Extending LiveCodeBench to Multiple Programming Languages

**Input**: Design documents from `/specs/001-multi-lcb-cross-lang/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- **Documentation**: `docs/`, `quickstart.md`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create repository structure per implementation plan (`README.md`, `code/`, `tests/`, `docs/`, `requirements.txt`, `quickstart.md`).
- [X] T002 Initialize Python project with `pyproject.toml` / `requirements.txt` and pin versions of all dependencies.
- [X] T003 [P] Configure linting (ruff) and formatting tools (black) and add pre‑commit hooks.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [X] T004 Implement configuration management (`code/config.py`) with paths, random seeds, model list, and temperature settings.
- [X] T005 [P] Implement dataset download script (`code/data/download.py`) that fetches the Multi‑LCB dataset from Hugging Face, pins the commit hash, verifies checksum, and logs the total task count.
- [X] T006 [P] Implement preprocessing and contamination filter (`code/data/preprocess.py`) that converts all STDIN/STDOUT test cases to the unified format, applies the release‑date cutoff, logs the exclusion rate (SC‑005), and handles missing metadata warnings.
- [ ] T007 [P] Define JSON schemas for dataset, execution log, and statistical results (`contracts/dataset.schema.yaml`, `contracts/execution_log.schema.yaml`, `contracts/statistical_results.schema.yaml`) to ensure Single Source of Truth (Constitution Principle IV).
- [~] T008 Set up Docker sandbox infrastructure (`code/execution/sandbox.py`) with lightweight language‑specific images and unified I/O handling, including error classification for runtime failures.
- [~] T009 Implement LLM invocation wrapper (`code/execution/runner.py`) supporting temperature, seed, ten independent runs per task, and token‑usage logging.
- [~] T010 Implement Pass@k aggregation logic (`code/execution/aggregators.py`) that computes mean and standard deviation for Pass@1, Pass@5, and Pass@10.
- [~] T011 Set up centralized logging and error‑handling framework (`code/logging.py`) that records runtime failures, timeouts, and other anomalies.

---

## Phase 3: User Story 1 - Reproducible Cross‑Language Benchmark Execution (Priority: P1) 🎯 MVP

**Goal**: Execute code‑generation tasks across multiple languages and temperatures, producing a complete `execution_log.json`.

**Independent Test**: Run the pipeline on a subset of multiple languages (C++, Java, Python) and verify the JSON contains Pass@1/5/10 for each language‑model‑temperature triplet.

- [~] T012 [P] [US1] Write orchestration script (`code/execute_pipeline.py`) that iterates over languages, temperatures (0.2, 0.6, 1.0), and 10 runs, invoking the sandbox and runner, and writes `results/artifacts/execution_log.json`.
- [~] T013 [P] [US1] Create Docker image pull script (`code/execution/docker_images.py`) for C++, Java, Rust, and other required runtimes, pinning image digests.
- [~] T014 [US1] Add runtime‑failure detection and logging (`runtime_failure.log`) in the sandbox wrapper.
- [~] T015 [US1] Implement timeout handling in sandbox wrapper that records a "fail" for Pass@k and logs duration to `timeout.log` using the format "timestamp, task_id, duration_ms, status=fail, reason=timeout".
- [~] T016 [US1] Integration test for the execution pipeline on a subset of 3 languages (C++, Java, Python) (`tests/integration/test_execution_pipeline.py`).

---

## Phase 4: User Story 2 - Statistical Correlation & Ranking Analysis (Priority: P2)

**Goal**: Analyse execution results to compute Pearson correlation, GLMM rankings, and Bonferroni‑corrected significance.

**Independent Test**: Feed a mock dataset (Multiple models × 12 languages) and verify that `statistical_results.json` contains the full correlation matrix, ranked model list, and corrected p‑values.

**Note on Dependencies**: T017-T021 depend on the completion of T006 (data pipeline) and T007 (schemas). T022 depends on the output of T012 (execution log) and T017-T021.

- [~] T017 [US2] Implement Leave‑One‑Out PCA (`code/analysis/pca.py`) that excludes Python when computing the General Code Capability (PC1). (Constitution VI override: Excluding Python from PCA to ensure independence from the target variable, deviating from Spec FR-005).
- [~] T018 [US2] Implement Generalized Linear Mixed Model fitting (`code/analysis/glmm.py`) on raw binary pass/fail data with random effects for Model and Language. (Constitution VI override: Using GLMM for binary outcomes instead of LMM, deviating from Spec FR-005).
- [~] T019 [US2] Implement Pearson correlation calculation (`code/analysis/correlation.py`) between Python Pass@1 and PC1, including intra‑model baseline comparison.
- [~] T020 [US2] Implement Bonferroni correction and significance flagging (`code/analysis/correction.py`) for the A substantial number of hypothesis tests will be conducted to evaluate the research question using the specified method, drawing on the following references..
- [~] T021 [US2] Implement secondary non‑parametric tests (Wilcoxon signed‑rank) explicitly authorized by Constitution Principle VI (`code/analysis/pairwise.py`).
- [~] T022 [US2] Assemble all statistical outputs into `results/artifacts/statistical_results.json` (`code/analysis/run_analysis.py`), ensuring data flows from T012 -> T017-T021.
- [ ] T023 [US2] Unit test for the analysis pipeline using a synthetic dataset (`tests/unit/test_analysis.py`).

---

## Phase 5: User Story 3 - Sensitivity & Contamination Verification (Priority: P3)

**Goal**: Verify robustness to temperature variation and remove any contaminated tasks.

**Independent Test**: Run the sensitivity module on a small subset and confirm variance reporting; confirm contamination filter excludes tasks released after model cut‑off dates.

- [ ] T024 [P] [US3] Implement temperature‑sensitivity analysis (`code/analysis/sensitivity.py`) that sweeps temperatures (0.2, 0.6, 1.0) and reports variance of correlation coefficients.
- [ ] T025 [P] [US3] Implement contamination filter (`code/analysis/contamination.py`) that compares task release dates to model training cut‑offs using strict inequality (Task Release Date < Model Training Cutoff) and logs excluded tasks.
- [ ] T026 [US3] Implement overfitting residual detection with threshold sweep (`code/analysis/overfitting.py`) for {0.10, 0.15, 0.20}.
- [ ] T027 [US3] Integration test for sensitivity and contamination modules (`tests/integration/test_sensitivity.py`).

---

## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Update documentation (`docs/README.md`, `quickstart.md`) to include instructions for the full pipeline, interpretation of statistical results, and the new scaling law analysis.
- [ ] T034 [P] Add visualization scripts for radar charts, heatmaps, correlation plots (`code/viz/plots.py`) ensuring they read directly from the JSON artifacts.
- [ ] T035 [P] Ensure all JSON artifacts conform to their schemas via a validation script (`code/validation/validate_artifacts.py`).
- [ ] T036 [P] Run ruff on `code/` and `tests/` and ensure zero errors/warnings.
- [ ] T037 Run the full pipeline on a larger runner (`scripts/run_full_pipeline.sh`) to process **all** tasks, generate final artifacts, and produce the research report.

---

## Dependencies & Execution Order

### Phase Dependencies
- **Setup (Phase 1)**: No dependencies – can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion – **BLOCKS** all user stories.
- **User Stories (Phases 3‑5)**: All depend on Foundational phase completion.
 - **Critical Note**: T017 (LOO-PCA) depends on T006 (preprocessing) and T007 (schemas) completion. It is NOT parallel-safe with respect to the data pipeline.
 - **Critical Note**: T022 (Assembly) depends on T012 (Execution) and T017-T021 (Analysis).
- **Polish (Phase 6)**: Depends on completion of the desired user stories.

### Within Each User Story
- Tests (if included) must be written and fail before implementation.
- Core modules before wrappers, wrappers before orchestration scripts.
- Analysis modules before report generation.

### Parallel Opportunities
- All Setup tasks marked **[P]** can run in parallel.
- All Foundational tasks marked **[P]** can run in parallel (except T017 which depends on T006/T007).
- After Foundational, each User Story can be developed in parallel by separate contributors, provided data dependencies (T012 -> Analysis) are respected.
- All test tasks marked **[P]** can run concurrently.

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Complete Phase 1 (Setup).
2. Complete Phase 2 (Foundational).
3. Complete Phase 3 (User Story 1).
4. Validate execution pipeline on a sampled subset.

### Incremental Delivery
1. Add User Story 2 (statistical analysis) → validate.
2. Add User Story 3 (sensitivity & contamination) → validate.
3. Run full pipeline on all tasks (Phase 6).

---

*All tasks are expressed in the canonical `- [ ] T### [P?] [USx?] description with file path` format and respect the CPU‑only CI constraints.*