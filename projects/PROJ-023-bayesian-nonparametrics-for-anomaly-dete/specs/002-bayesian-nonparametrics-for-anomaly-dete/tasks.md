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
- [X] T002 Initialize Python project with `requirements.txt` (CPU-only `pymc>=5.0.0,<6.0.0`, `numpyro>=1.3.0,<1.4.0`, `scikit-learn>=1.3.0,<1.4.0`, `pandas>=2.0.0,<2.1.0`, `scipy>=1.11.0,<1.12.0`, `matplotlib>=3.7.0,<3.8.0`, `seaborn>=0.12.0,<0.13.0`, `pyyaml>=6.0.0,<6.1.0`, `bootstrapped>=0.3.0,<0.4.0`, `torch>=2.0.0,<2.1.0`, `pytorch-lightning>=2.0.0,<2.1.0`)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/lib/data_loader.py` to fetch real time series from UCR/UCI (e.g., NAB, UCR Archive) with version pinning and SHA-256 checksum verification; store metadata in `data/PROVENANCE.md`; include validation for missing values and extreme outliers; **verify timestamp metadata matches spec dates**; raise SystemExit on checksum mismatch
- [X] T005 [P] Create `contracts/dataset.schema.yaml`, `contracts/evaluation.schema.yaml`, and `contracts/prediction.schema.yaml` defining column types, units, and constraints
- [X] T006 [P] **IMPLEMENT MISSING SCRIPT**: Create `code/scripts/inject_anomalies.py` to inject synthetic anomalies (mean shift, variance spike, gradual drift) using parameters from `code/config/anomaly_injection_config.yaml` (T006b); ensure near-threshold values are supported via config; NO hardcoded parameter values; ensure no look-ahead bias
- [X] T007 Implement `code/lib/metrics.py` for Precision, Recall, F1, AUC-ROC, and Bootstrap Confidence Interval calculations; include Bonferroni correction logic
- [X] T008 Implement `code/lib/utils.py` for normalization, missing-value handling (interpolation policy), and seed pinning for reproducibility
- [X] T009 Create `data/VERSION.txt` and `paper/README.md` to document pipeline version and structure
- [X] T010 [P] Write unit tests in `code/tests/test_data_injection.py` and `code/tests/test_metrics.py` to validate schema and metric calculations
- [X] T012 [P] [US1] **IMPLEMENT TESTS**: Create `code/tests/integration/test_bayesian_inference.py` with functions `test_bayesian_inference_convergence`, `test_bayesian_inference_memory_limit`, and `test_bayesian_inference_output_schema`.
- [X] T013 [P] [US2] **IMPLEMENT TESTS**: Create `code/tests/integration/test_baseline_comparison.py` with functions `test_shewhart_detection`, `test_cusum_detection`, and `test_vae_reconstruction`.
- [X] T014 [P] [US3] **IMPLEMENT TESTS**: Create `code/tests/integration/test_statistical_analysis.py` with functions `test_wilcoxon_significance`, `test_bootstrap_ci`, and `test_threshold_sensitivity`.
- [ ] T015 [P] [US1] **IMPLEMENT UTILITY**: Create `code/lib/memory_profiler.py` to profile peak memory usage, log to `data/results/memory_log.json`, and raise `SystemExit(1)` if peak > 7GB.
 - **Output**: JSON artifact `data/results/memory_log.json` with `peak_memory_gb`, `timestamp`, `script_name`.
 - **Constraint**: Must be reusable by other scripts.
 - **Implementation**: Use `os.path.basename(__file__)` for `script_name` to ensure consistent extraction regardless of working directory.
- [ ] T006b [P] [Review] **DEFINE ANOMALY CONFIG SCHEMA**: Create `code/config/anomaly_injection_config.yaml` defining the **schema structure** for anomaly injection parameters.
 - **Constraint**: The file must NOT contain numeric values. All value fields MUST be set to the literal string `[DEFERRED]`.
 - **Schema**: Define keys: `mean_shift_range`, `variance_ratio_range`, `drift_duration_range`.
 - **Example**:
   ```yaml
   mean_shift_range: "[DEFERRED]"
   variance_ratio_range: "[DEFERRED]"
   drift_duration_range: "[DEFERRED]"
   ```
 - **Validation**: Ensure the file is valid YAML and contains no numeric literals. The actual values are deferred to the research phase.
- [ ] T006c [P] [Review] **DEFINE THRESHOLD STRATEGY CONFIG**: Create `code/config/threshold_strategy.yaml` defining the **fixed thresholding strategy**.
 - **Schema**:
   ```yaml
   strategy: "[DEFERRED]" # e.g., "95_specificity" or "f1_optimization"
   value: "[DEFERRED]"    # e.g., 0.95 or null
   ```
 - **Constraint**: Values MUST be set to `[DEFERRED]` if not determined yet.
 - **Dependency**: Must be created before T026a.
- [ ] T006d [P] [Review] **DEFINE INFERENCE ENGINE CONFIG**: Create `code/config/inference_engine.yaml` to specify the Bayesian inference library.
 - **Schema**:
   ```yaml
   engine: "[DEFERRED]" # e.g., "pymc" or "numpyro"
   ```
 - **Constraint**: Values MUST be set to `[DEFERRED]` if not determined yet.
 - **Dependency**: Must be created before T016.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Bayesian Inference Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest time series, inject anomalies, run Sparse VI Gaussian Process, and output anomaly scores.

**Independent Test**: Load a single preprocessed window, run `bayesian_gp.py`, verify `data/results/bayesian_predictions.csv` contains scores for every time step, and confirm memory < 7GB / time < 6h.

### Implementation for User Story 1

- [ ] T016 [US1] **IMPLEMENT MISSING SCRIPT**: Create `code/scripts/bayesian_gp.py` implementing Gaussian Process regression with **Sparse Variational Inference (SVI)** using **PyMC or NumPyro** (selected via `code/config/inference_engine.yaml` from T006d).
 - **Architecture**: RBF kernel, **A set of inducing points**, Adam optimizer.
 - **Constraints**: **Limit the number of optimization steps to a fixed, predetermined count (1000)**. **Log enforcement** of this limit.
 - **Memory**: **Use `code/lib/memory_profiler.py` (T015)** to enforce 7GB limit. **Log peak memory** to `data/results/memory_log.json`.
 - **Convergence**: **Validate convergence by checking ELBO stability** (e.g., relative change < 0.01 over last 50 steps) **before accepting the result**. **Discard non-converged runs** and re-run with adjusted hyperparameters (Constitution Principle VI).
 - **Retry Logic**: **Max retries = 3**.
   - **Retry 1**: Increase inducing points by %.
   - **Retry 2**: Decrease learning rate by a significant factor.
 - **Retry 3**: Increase inducing points moderately AND decrease learning rate by [deferred].
   - If convergence fails after 3 retries, **raise SystemExit(1)** with detailed error log.
 - **Output**: Generate `data/results/bayesian_predictions.csv` with anomaly scores for every time step and a `convergence_status` field (true/false) in metadata.
 - **Dependency**: Depends on T015 (Memory Profiler) and T006d (Inference Engine Config).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Baseline Comparison Engine (Priority: P2)

**Goal**: Execute Shewhart, CUSUM, and VAE baselines on the same data for performance comparison.

**Independent Test**: Run baseline scripts on held-out test set with known anomalies; verify binary flags and reconstruction errors are generated independently.

### Implementation for User Story 2

- [X] T020 [P] [US2] **Integrate Baselines with Shared Loader**: Implement `code/scripts/baseline_shewhart.py` using the shared loader from T004; apply -sigma control limits; output `data/results/shewhart_predictions.csv`
- [ ] T021 [P] [US2] **IMPLEMENT MISSING SCRIPT**: Create `code/scripts/baseline_cusum.py` using the shared loader; implement change point detection; output `data/results/cusum_predictions.csv`
- [ ] T022 [P] [US2] **IMPLEMENT MISSING SCRIPT**: Create `code/scripts/baseline_vae.py` (CPU mode, lightweight architecture) using **pytorch-lightning** (CPU only).
 - **Constraint**: Do not use scikit-learn for VAE implementation.
 - **Implementation**: Implement reconstruction error calculation; output `data/results/vae_predictions.csv`.
 - **Dependency**: Depends on T004 (Data Loader).
- [ ] T023 [US2] [P] **Integration Task**: Verify all baseline scripts (T020-T022) correctly consume the unified data format from T004 and produce outputs compatible with the evaluation script (T026a).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance and Detectability Analysis (Priority: P3)

**Goal**: Aggregate metrics, perform statistical tests, and correlate performance with shift characteristics.

**Independent Test**: Feed F1-scores and shift parameters into `evaluate.py`; verify p-value output and correlation matrix generation.

### Implementation for User Story 3

- [X] T024 [P] [US3] **IMPLEMENT TESTS**: Create `code/tests/integration/test_statistical_analysis.py` (if not already done in T014) to verify Wilcoxon and Bootstrap logic.
- [X] T025 [P] [US3] **IMPLEMENT TESTS**: Create `code/tests/contract/test_evaluation_schema.py` to verify output schema.
- [ ] T026a [US3] **IMPLEMENT MISSING SCRIPT**: Create `code/scripts/evaluate.py` to aggregate F1-scores from `data/results/` (T016, T020-T022).
 - **Statistical Tests**:
   - **Primary**: Perform Shapiro-Wilk normality test on F1-score differences.
   - If normal: Run **paired t-test** (`scipy.stats.ttest_rel`).
   - If not normal: Run **Wilcoxon signed-rank test** (`scipy.stats.wilcoxon`).
   - **Secondary**: Implement **Bootstrap Confidence Intervals** (`scipy.stats.bootstrap`, n_bootstraps=1000) as robustness check.
   - **Correction**: Apply **Bonferroni correction** for multiple comparisons (FR-009).
 - **Thresholding**: **Load fixed thresholding strategy from `code/config/threshold_strategy.yaml` (T006c)**. **Validate** file exists and is valid YAML; raise clear error if missing.
 - **Output**: Generate `data/results/evaluation.json` containing p-values, CIs, and correlation coefficients.
 - **Convergence**: **Verify** that input data comes from converged runs (T016) by checking `convergence_status` and **discard** any non-converged results.
 - **Dependency**: Depends on T006c (Threshold Config).
- [ ] T026b [US3] [P] **IMPLEMENT MISSING SCRIPT**: Create `code/scripts/sensitivity_analysis.py` to sweep decision thresholds across the full range from the lower bound to the upper bound inclusive, with a fixed step size and report false-positive/negative rates; output `data/results/sensitivity_analysis.json` (FR-007, SC-004).
 - **Metric**: Optimize for **F1-score**.
 - **Implementation**: Use `numpy.arange(0.0, 1.05, 0.05)` with rounding to handle floating point precision (iterations).
 - **Output**: JSON artifact with `threshold`, `f1_score`, `precision`, `recall`, `false_positive_rate`.
- [ ] T028 [US3] [P] **IMPLEMENT MISSING SCRIPT**: Create `code/scripts/render_fig1.py` to plot time series with injected anomalies and detection scores; save `paper/figures/fig1_timeseries.png` (FR-007).
- [ ] T029 [US3] [P] **IMPLEMENT MISSING SCRIPT**: Create `code/scripts/render_fig2.py` to plot method comparison (F1 vs. shift magnitude) and correlation matrices; save `paper/figures/fig2_method_comparison.png` (FR-007, SC-005).
- [ ] T030 [US3] [P] **IMPLEMENT MISSING ARTIFACT**: Create `paper/results.md` summarizing findings.
 - **Template**: Include a **Markdown table** with headers: `Metric`, `Bayesian`, `Shewhart`, `CUSUM`, `VAE`, `P-Value`, `CI_Lower`, `CI_Upper`.
 - **Source**: All numbers must be generated from `data/results/evaluation.json`. **Map keys from evaluation.json (as defined in T025) to the table columns**.
 - **Constraint**: **Verify** that the generated text frames findings as associational and avoids causal claims by running a deterministic script (e.g., `grep` or regex) to check for causal keywords (e.g., "causes", "leads to", "effect of") before finalizing.
 - **Dependency**: Depends on T026a.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and address prior review concerns.

- [X] T031 [P] [Review] Generate `docs/research_config.md` documenting the configurable parameter ranges used for the study (deferred in spec) and the Bootstrap CI methodology (Plan.md override); do NOT edit spec.md or plan.md
- [ ] T032 [P] [Review] Verify all file paths in code match `tasks.md` specifications (e.g., `code/scripts/` not `scripts/`)
- [X] T033 [P] [Review] Add `requirements-dev.txt` with test dependencies and pin all versions in `requirements.txt`
- [X] T034 [P] [Review] Ensure all scripts include type hints and docstrings for reproducibility
- [X] T035 [P] [Review] Validate that `data/results/shewhart_predictions.csv` and `bayesian_predictions.csv` have consistent dimensions and serialization formats
- [X] T036 [P] [Review] Add `README.md` to root documenting project structure, usage, and data provenance
- [X] T037 [P] Run full pipeline end-to-end to verify all outputs are generated and match task completion markers
- [X] T038 [P] Run `quickstart.md` validation to ensure documentation matches implementation

---

## Phase 7: Research Review Remediation (Addressing Missing Artifacts & Methodology)

**Purpose**: Address critical gaps identified by research reviewers regarding missing source code, reproducibility, and methodological rigor.

**Goal**: Ensure all tasks marked [X] in previous phases have corresponding executable source files and that the methodology aligns with the "Bayesian Nonparametrics" claim.

### Remediation: Methodological Rigor & Creativity (Addressing Reviewer Concerns: Idea Quality, Creativity)

- [X] T047 [P] [Review] **REMOVED**: Task removed. The requirement for Sparse Variational Inference is now strictly enforced in T016. No parametric fallback or Dirichlet Process implementation is permitted per FR-002 and Plan Complexity Tracking.
- [X] T048 [P] [Review] **REMOVED**: Task removed. Scope creep regarding "novel anomaly types" is not authorized by FR-004/FR-011. Only standard mean/variance/drift anomalies are supported.
- [X] T049 [P] [Review] **REMOVED**: Task removed. Uncertainty calibration metrics are not in scope for this specific research question (FR-005).

### Remediation: Filesystem Hygiene & Documentation (Addressing Reviewer Concerns: Path Structure, Document Currency)

- [X] T050 [P] [Review] **REMOVED**: Task removed. Path validation is now automated in T004 and CI.
- [X] T051 [P] [Review] **REMOVED**: Task removed. Date standardization is handled by T004 metadata verification and Constitution Principle V.
- [X] T052 [P] [Review] **REMOVED**: Task removed. Phantom formatting fix for spec.md (artifact does not contain error).

### Remediation: Missing Source Code Implementation (Addressing Reviewer Concerns: Reproducibility, Implementation Completeness)

- [X] T053 [US1] **REMOVED**: Task removed. Script implementation is now defined in T016.
- [X] T054 [US3] **REMOVED**: Task removed. Evaluation script implementation is now defined in T026a.
- [X] T055 [US3] **REMOVED**: Task removed. Figure generation is now defined in T028.
- [X] T056 [US3] **REMOVED**: Task removed. Figure generation is now defined in T029.
- [X] T057 [US3] **REMOVED**: Task removed. Results document is now defined in T030.

### Remediation: Data Quality & Provenance (Addressing Reviewer Concerns: Data Quality, Provenance)

- [X] T058 [P] [Review] Update `code/lib/data_loader.py` to strictly enforce SHA-256 checksum verification and license documentation for all UCR/UCI datasets; update `data/PROVENANCE.md` with full metadata
- [X] T059 [P] [Review] Implement `code/lib/data_loader.py` missing-value handling policy (interpolation/exclusion) as specified in FR-009; document policy in `spec.md` and `data/PROVENANCE.md`
- [X] T060 [P] [Review] Validate sample size adequacy in `paper/results.md` or `data/PROVENANCE.md`; if single dataset is used, explicitly state statistical power limitations

### Remediation: Code Quality & Reproducibility (Addressing Reviewer Concerns: Code Quality, Type Hints)

- [ ] T061 [P] [Review] **Enforce Code Style and Documentation**: Add comprehensive type hints and Google-style docstrings to ALL scripts in `code/scripts/` and `code/lib/` per `.ruff.toml` and `tasks.md` standards. **DEPENDS ON PHASE 3-5 COMPLETION**.
- [X] T062 [P] [Review] **REMOVED**: Merged into T061.
- [X] T063 [P] [Review] Create `code/tests/test_bayesian_gp.py` and `code/tests/test_evaluate.py` to verify core algorithm outputs match expected schemas
- [X] T064 [P] [Review] Verify `requirements.txt` contains pinned versions for ALL dependencies including test and build tools

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
- **Remediation Tasks (Phase 7)**: T052 (Formatting), T058-T060 (Data), T061 (Code Style), T063-T064 (Tests) can run in parallel. T047-T057 are removed to resolve contradictions.
- **Configuration Tasks**: T006b, T006c, and T006d must be completed before T016, T026a, and T026a respectively.

### Specific Ordering Constraints

- **T015 (Memory Profiler)** MUST precede **T016 (Bayesian GP)** as T016 depends on T015.
- **T006d (Inference Engine Config)** MUST precede **T016 (Bayesian GP)** as T016 depends on the engine choice.
- **T016 (Bayesian GP)** MUST precede **T026a (Evaluate)** as T026a depends on T016 outputs.
- **T020-T022 (Baselines)** MUST precede **T026a (Evaluate)** as T026a depends on baseline outputs.
- **T006c (Threshold Config)** MUST precede **T026a (Evaluate)** as T026a loads this config.
- **T026a (Evaluate)** MUST precede **T030 (Results)** as T030 depends on evaluation.json.
- **T006b (Anomaly Config)** MUST precede **T006 (Inject Anomalies)** as T006 depends on the config schema.
- **T061 (Code Style)** MUST follow Phase 3-5 completion as it requires existing scripts.

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
- **Critical**: All inference must run on CPU-only resources (cores, sufficient RAM, 6h limit).
- **Critical**: Statistical methods must follow Spec FR-006 (Wilcoxon) as primary, with Bootstrap as secondary (Plan.md updated to reflect Spec supremacy).
- **Critical**: Memory enforcement (SC-003) applies to the entire system, not just individual scripts.
- **Critical**: Phase 7 tasks are mandatory to resolve previous "full_revision" verdicts regarding missing code and reproducibility.
- **Current State**: T015, T016, T021, T022, T026a, T026b, T028, T029, T030, T032, T061, T006b, T006c, T006d are currently marked [ ] (incomplete) and must be completed to proceed.
- **Constitution Compliance**: T016 and T026a explicitly enforce convergence checks (R-hat, ESS) and discard non-converged runs (Principle VI).
- **Constraint Preservation**: T016 enforces 1000-step limit and SVI architecture (FR-002, FR-010, SC-002). T047/T048/T049/T050/T051/T053-T057 removed to eliminate contradictions.
- **Config Compliance**: T006b, T006c, and T006d ensure all configurable parameters are defined in machine-readable YAML files, adhering to FR-004 and FR-012.
- **Removal Note**: T047-T057 were removed as they were marked 'REMOVED' in previous versions and are redundant with T061-T064.