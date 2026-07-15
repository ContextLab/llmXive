# Tasks: Bayesian Nonparametrics for Anomaly Detection in Time Series

**Input**: Design documents from `/specs/001-bayesian-nonparametrics-anomaly-detection/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `data/`, `paper/`, `contracts/`, `tests/` at repository root
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

- [X] T001 Create project structure per implementation plan: `code/`, `data/`, `paper/`, `contracts/`, `tests/`, `data/raw/`, `data/processed/`, `data/results/`, `paper/figures/`
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (CPU-only `pymc>=5.0.0,<6.0.0`, `numpyro>=1.3.0,<1.4.0`, `scikit-learn>=1.3.0,<1.4.0`, `pandas>=2.0.0,<2.1.0`, `scipy>=1.11.0,<1.12.0`, `matplotlib>=3.7.0,<3.8.0`, `seaborn>=0.12.0,<0.13.0`, `pyyaml>=6.0.0,<6.1.0`, `bootstrapped>=0.3.0,<0.4.0`)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/lib/data_loader.py` to fetch real time series from UCR/UCI (e.g., NAB, UCR Archive) with version pinning and SHA-256 checksum verification; store metadata in `data/PROVENANCE.md`; include validation for missing values and extreme outliers
- [X] T005 [P] Create `contracts/dataset.schema.yaml`, `contracts/evaluation.schema.yaml`, and `contracts/prediction.schema.yaml` defining column types, units, and constraints
- [X] T006 Implement `code/lib/anomaly_injector.py` to inject synthetic anomalies (mean shift, variance spike, gradual drift) with configurable parameters via a YAML/JSON config file; ensure near-threshold values are supported; NO hardcoded parameter values; ensure no look-ahead bias
- [ ] T007 Implement `code/lib/metrics.py` for Precision, Recall, F1, AUC-ROC, and Bootstrap Confidence Interval calculations; include Bonferroni correction logic
- [ ] T008 Implement `code/lib/utils.py` for normalization, missing-value handling (interpolation policy), and seed pinning for reproducibility
- [X] T009 Create `data/VERSION.txt` and `paper/README.md` to document pipeline version and structure
- [X] T010 [P] Write unit tests in `code/tests/test_data_injection.py` and `code/tests/test_metrics.py` to validate schema and metric calculations

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Bayesian Inference Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest time series, inject anomalies, run Sparse VI Gaussian Process, and output anomaly scores.

**Independent Test**: Load a single preprocessed window, run `bayesian_gp.py`, verify `data/results/bayesian_predictions.csv` contains scores for every time step, and confirm memory < 7GB / time < 6h.

### Tests for User Story 1 (OPTIONAL - only if requested) ⚠️

> **NOTE**: IF `plan.md` has `TESTS_ENABLED: true`, then write these tests FIRST, ensure they FAIL before implementation.

- [X] T011 [P] [US1] IF `plan.md` TESTS_ENABLED is true, create `code/tests/contract/test_bayesian_schema.py`
- [X] T012 [P] [US1] IF `plan.md` TESTS_ENABLED is true, create `code/tests/integration/test_bayesian_inference.py`

### Implementation for User Story 1

- [~] T014 [US1] Implement `code/scripts/inject_anomalies.py` to invoke `code/lib/anomaly_injector.py` (T006) with research parameters; save `data/processed/series_with_anomalies.csv` and `data/processed/ground_truth.csv`
- [X] T015 [US1] Implement `code/scripts/bayesian_gp.py` using `pymc` or `numpyro` with Sparse Variational Inference (SVI); ensure CPU-only execution; implement convergence checks for ELBO stability and Effective Sample Size (ESS); include R-hat check ONLY if MCMC fallback is used (per Plan.md Constitution Check); **limit to a sufficient number of steps** and **log enforcement** of this limit; output `data/results/bayesian_predictions.csv`
- [~] T017 [US1] Implement memory profiling wrapper in `code/scripts/bayesian_gp.py` AND `code/lib/utils.py` that monitors peak usage across ALL inference scripts using `tracemalloc`; **raise SystemExit(1)** if limit > 7GB is exceeded to satisfy SC-003 system-wide

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Baseline Comparison Engine (Priority: P2)

**Goal**: Execute Shewhart, CUSUM, and VAE baselines on the same data for performance comparison.

**Independent Test**: Run baseline scripts on held-out test set with known anomalies; verify binary flags and reconstruction errors are generated independently.

### Tests for User Story 2 (OPTIONAL - only if requested) ⚠️

> **NOTE**: IF `plan.md` has `TESTS_ENABLED: true`, then write these tests FIRST, ensure they FAIL before implementation.

- [ ] T018 [P] [US2] IF `plan.md` TESTS_ENABLED is true, create `code/tests/contract/test_baseline_schema.py` <!-- FAILED: unspecified -->
- [X] T019 [P] [US2] IF `plan.md` TESTS_ENABLED is true, create `code/tests/integration/test_baseline_comparison.py`

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `code/scripts/baseline_shewhart.py` with -sigma control limits; output `data/results/shewhart_predictions.csv`
- [~] T021 [P] [US2] Implement `code/scripts/baseline_cusum.py` for change point detection; output `data/results/cusum_predictions.csv`
- [~] T022 [P] [US2] Implement `code/scripts/baseline_vae.py` (CPU mode, lightweight architecture) using `scikit-learn` or `pytorch-lightning` (CPU only); output reconstruction errors and binary flags in `data/results/vae_predictions.csv`
- [~] T023 [US2] Integrate baseline scripts with the shared data loader and anomaly injection pipeline from US1

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance and Detectability Analysis (Priority: P3)

**Goal**: Aggregate metrics, perform statistical tests, and correlate performance with shift characteristics.

**Independent Test**: Feed F1-scores and shift parameters into `evaluate.py`; verify p-value output and correlation matrix generation.

### Tests for User Story 3 (OPTIONAL - only if requested) ⚠️

> **NOTE**: IF `plan.md` has `TESTS_ENABLED: true`, then write these tests FIRST, ensure they FAIL before implementation.

- [X] T024 [P] [US3] IF `plan.md` TESTS_ENABLED is true, create `code/tests/contract/test_evaluation_schema.py`
- [X] T025 [P] [US3] IF `plan.md` TESTS_ENABLED is true, create `code/tests/integration/test_statistical_analysis.py`

### Implementation for User Story 3

- [X] T026a [US3] Implement `code/scripts/evaluate.py` to calculate F1, AUC, and Bootstrap Confidence Intervals (per Plan.md Complexity Tracking); ensure dependencies on T015, T020, T021, T022, T023 are met; output `data/results/evaluation.json`
- [X] T026b [US3] Implement **Wilcoxon signed-rank test** (or paired t-test) in `code/scripts/evaluate.py` to compare Bayesian vs. Baseline F1-scores as mandated by FR-006 and SC-001; output p-value to `data/results/evaluation.json`
- [X] T026c [US3] Implement **Bonferroni correction** (or Benjamini-Hochberg) in `code/scripts/evaluate.py` for multiple hypothesis tests as mandated by FR-009; output adjusted p-values to `data/results/evaluation.json`
- [X] T026d [US3] Implement **fixed thresholding strategy** (e.g., % specificity) in `code/scripts/evaluate.py` and enforce it before correlation analysis as mandated by FR-012; output threshold parameters to `data/results/evaluation.json`
- [~] T027 [US3] Implement `code/scripts/sensitivity_analysis.py` to sweep decision thresholds (High specificity, F1-opt) and report false-positive/negative rates; output `data/results/sensitivity_analysis.json`
- [ ] T028 [US3] Implement `code/scripts/render_fig1.py` to plot time series with injected anomalies and detection scores; save `paper/figures/fig1_timeseries.png`
- [ ] T029 [US3] Implement `code/scripts/render_fig2.py` to plot method comparison (F1 vs. shift magnitude) and correlation matrices; save `paper/figures/fig2_method_comparison.png`
- [ ] T030 [US3] Create `paper/results.md` summarizing findings, p-values, and associational claims (avoiding causal language per FR-008)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and address prior review concerns.

- [ ] T031 [P] [Review] Generate `docs/research_config.md` documenting the configurable parameter ranges used for the study (deferred in spec) and the Bootstrap CI methodology (Plan.md override); do NOT edit spec.md or plan.md
- [ ] T032 [P] [Review] Verify all file paths in code match `tasks.md` specifications (e.g., `code/scripts/` not `scripts/`)
- [ ] T033 [P] [Review] Add `requirements-dev.txt` with test dependencies and pin all versions in `requirements.txt`
- [ ] T034 [P] [Review] Ensure all scripts include type hints and docstrings for reproducibility
- [ ] T035 [P] [Review] Validate that `data/results/shewhart_predictions.csv` and `bayesian_predictions.csv` have consistent dimensions and serialization formats
- [ ] T036 [P] [Review] Add `README.md` to root documenting project structure, usage, and data provenance
- [ ] T037 [P] Run full pipeline end-to-end to verify all outputs are generated and match task completion markers
- [ ] T038 [P] Run `quickstart.md` validation to ensure documentation matches implementation

---

## Phase 7: Research Review Remediation (Addressing Missing Artifacts & Methodology)

**Purpose**: Address critical gaps identified by research reviewers regarding missing source code, reproducibility, and methodological rigor.

**Goal**: Ensure all tasks marked [X] in previous phases have corresponding executable source files and that the methodology aligns with the "Bayesian Nonparametrics" claim.

### Remediation: Methodological Rigor & Creativity (Addressing Reviewer Concerns: Idea Quality, Creativity)

- [ ] T047 [P] [Review] Refactor `code/scripts/bayesian_gp.py` to explicitly utilize nonparametric priors (e.g., Dirichlet Process Mixture or Hierarchical GP) where feasible; **IF** a standard parametric GP is used, **MUST** clearly document the parametric GP limitations and justify the approach in `paper/results.md` to address creativity gaps without weakening FR-002
- [ ] T048 [P] [Review] Extend `code/lib/anomaly_injector.py` to support novel anomaly types (e.g., context-dependent or regime shifts) beyond standard mean/variance shifts to address creativity gaps
- [ ] T049 [P] [Review] Add uncertainty calibration metrics (e.g., Brier score) to `code/lib/metrics.py` to evaluate the quality of probability scores, not just binary classification

### Remediation: Filesystem Hygiene & Documentation (Addressing Reviewer Concerns: Path Structure, Document Currency)

- [ ] T050 [P] [Review] Audit all file paths in `code/`, `data/`, and `paper/` to ensure strict adherence to `code/` prefix and `data/` prefix as defined in `tasks.md`
- [ ] T051 [P] [Review] Standardize `plan.md` and `spec.md` dates to current revision date to prevent audit trail confusion and ensure Constitution Principle V compliance
- [ ] T052 [P] [Review] Fix formatting artifact in `spec.md` (orphaned text "for consistent testing.")

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete
- **Remediation (Phase 7)**: **CRITICAL** - Must be completed before any further research validation or acceptance. Addresses missing code and methodological gaps.

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
- **Remediation Tasks (Phase 7)**: T047-T049 (Methodology) and T050-T052 (Hygiene) can run in parallel. T047 should follow T015.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical**: All data must be real (from public repos) or synthetically injected with known ground truth; NO fake data generation for evaluation.
- **Critical**: All inference must run on CPU-only resources (cores, 7GB RAM, 6h limit).
- **Critical**: Statistical methods must follow Plan.md (Bootstrap CI) over Spec.md (Wilcoxon) where Plan explicitly overrides due to F1-score skewness, BUT FR-006 and SC-001 require Wilcoxon/t-test implementation (T026b) to satisfy the spec's explicit requirement.
- **Critical**: Memory enforcement (SC-003) applies to the entire system, not just individual scripts.
- **Critical**: Phase 7 tasks are mandatory to resolve previous "full_revision" verdicts regarding missing code and reproducibility.
- **Current State**: T005, T015, T026, T030 are currently marked [ ] (incomplete) and must be completed to proceed.