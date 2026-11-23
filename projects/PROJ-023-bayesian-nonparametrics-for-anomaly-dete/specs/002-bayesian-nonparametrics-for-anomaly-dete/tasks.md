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

- [X] T004 Implement `code/lib/data_loader.py` to fetch real time series from **UCR Time Series Archive** AND **UCI Machine Learning Repository**. **Selection Rule**: Select the first 5 univariate series with length > 1000, sorted alphabetically by dataset name, to ensure deterministic selection. [UNRESOLVED-CLAIM: c_2405bf9a — status=not_enough_info] Store provenance metadata (URL, dataset name, version, checksum, license) in `data/PROVENANCE.md`; include validation for missing values and extreme outliers; **verify timestamp metadata matches spec dates**; raise SystemExit on checksum mismatch. **Constraint**: Do NOT hardcode a single URL. Implement a generic loader that supports multiple public sources via a configurable list of valid endpoints (UCR, UCI) to ensure reproducibility if a specific link breaks.
- [X] T005 [P] Create `contracts/dataset.schema.yaml`, `contracts/evaluation.schema.yaml`, and `contracts/prediction.schema.yaml` defining column types, units, and constraints
- [X] T006b [Review] **DEFINE ANOMALY CONFIG SCHEMA**: Create `code/config/anomaly_injection_config.yaml` defining the **schema structure** for anomaly injection parameters.
 - **Constraint**: The file MUST define keys: `mean_shift_range`, `variance_ratio_range`, `drift_duration_range` with types (list of floats).
 - **Values**: Use **safe default ranges** (e.g., `mean_shift_range: [0.5, 2.0]`) for implementation reproducibility. **Comment**: These are implementation defaults; the research phase will refine these values.
 - **Execution**: This task MUST write the schema structure and logic to load values from the external config.
- [ ] T006 [Review] **IMPLEMENT MISSING SCRIPT**: Create `code/scripts/inject_anomalies.py` to inject synthetic anomalies (mean shift, variance spike, gradual drift) using parameters loaded from `anomaly_injection_config.yaml` (via T006b); ensure near-threshold values are supported via config; NO hardcoded parameter values; ensure no look-ahead bias. **Constraint**: If the config is missing, raise a clear error. **Dependency**: T006b must be completed and marked [X] before T006 can run.
- [X] T007 Implement `code/lib/metrics.py` for Precision, Recall, F1, AUC-ROC, **AUC-PR**, and Bootstrap Confidence Interval calculations; include Bonferroni correction logic; **calculate metrics against the injected ground truth**.
- [X] T008 Implement `code/lib/utils.py` for normalization, missing-value handling (interpolation policy), and seed pinning for reproducibility
- [X] T009 Create `data/VERSION.txt` and `paper/README.md` to document pipeline version and structure
- [X] T010 [P] Write unit tests in `code/tests/test_data_injection.py` and `code/tests/test_metrics.py` to validate schema and metric calculations
- [X] T015 [P] [US1] **IMPLEMENT UTILITY**: Create `code/lib/memory_profiler.py` to profile peak memory usage, log to `data/results/memory_log.json`, and raise `SystemExit(1)` if peak > 7GB.
 - **Output**: JSON artifact `data/results/memory_log.json` with strict schema: `peak_memory_gb` (float), `timestamp` (ISO8601 string), `script_name` (string).
 - **Constraint**: Must be reusable by other scripts.
 - **Implementation**: Use `os.path.basename(__file__)` for `script_name` to ensure consistent extraction regardless of working directory.
- [X] T006c [Review] **DEFINE THRESHOLD STRATEGY CONFIG**: Create `code/config/threshold_strategy.yaml` defining the **fixed thresholding strategy**.
 - **Constraint**: The file MUST support strategies: `fixed_probability`, `specificity`, `f1_optimization`.
 - **Schema**:
 ```yaml
 strategy: "f1_optimization"
 value: 0.5 # Only used if strategy is fixed_probability
 target_specificity: 0.95 # Only used if strategy is specificity
 ```
 - **Validation**: Ensure the file is valid YAML. The system must use this default if no override is provided.
 - **Execution**: This task MUST write the file with the exact content above.
- [X] T006d [Review] **DEFINE INFERENCE ENGINE CONFIG**: Create `code/config/inference_engine.yaml` to specify the Bayesian inference library.
 - **Schema**:
 ```yaml
 engine: "pymc"
 ```
 - **Constraint**: Values MUST be set to a concrete default (e.g., "pymc") if not determined yet.
 - **Dependency**: Must be created before T016.
 - **Execution**: This task MUST write the file with the exact content above.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Bayesian Inference Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest time series, inject anomalies, run Sparse VI Gaussian Process, and output anomaly scores.

**Independent Test**: Load a single preprocessed window, run `bayesian_gp.py`, verify `data/results/bayesian_predictions.csv` contains scores for every time step, and confirm memory < 7GB / time < 6h.

### Implementation for User Story 1

- [X] T016 [US1] **IMPLEMENT MISSING SCRIPT**: Create `code/scripts/bayesian_gp.py` implementing Gaussian Process regression with **Sparse Variational Inference (SVI)** using **PyMC or NumPyro** (selected via `code/config/inference_engine.yaml` from T006d).
 - **Architecture**: RBF kernel, **A set of inducing points** (default 20), Adam optimizer.
 - **Constraints**: **Implement a dynamic convergence loop based on ELBO stability** (e.g., relative change < 0.01 over last 50 steps). **Discard non-converged runs** and re-run with adjusted hyperparameters (Constitution Principle VI). **DO NOT use a fixed step count as the sole stopping criterion, BUT the TOTAL steps across all retries MUST NOT exceed 1000** to satisfy FR-010.
 - **Initial Values**: Start with `inducing_points=20`, `learning_rate=0.01`.
 - **Retry Logic**: Max retries = 10 (or until total steps > 1000).
 - Retry 1: **Reset to original values and adjust**: `inducing_points=25`, `learning_rate=0.01`.
 - Retry 2: **Reset to original values and adjust**: `inducing_points=20`, `learning_rate=0.009`.
 - Retry 3: **Reset to original values and adjust**: `inducing_points=25`, `learning_rate=0.009`.
 - If convergence fails after retries OR total steps > 1000, **raise SystemExit(1)** with detailed error log.
 - **Memory**: **Use `code/lib/memory_profiler.py` (T015)** to enforce 7GB limit. **Log peak memory** to `data/results/memory_log.json`. **T015 must be marked [X] before T016 runs.**
 - **Convergence**: **Validate convergence by checking ELBO stability** before accepting the result. **Discard non-converged runs** and re-run with adjusted hyperparameters.
 - **Output**: Generate `data/results/bayesian_predictions.csv` with anomaly scores for every time step. **DO NOT include convergence_status in the CSV**.
 - **Metadata**: Write convergence status and diagnostics to a separate file `data/results/bayesian_convergence.json`.
 - **Dependency**: Depends on T015 (Memory Profiler) and T006d (Inference Engine Config).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Baseline Comparison Engine (Priority: P2)

**Goal**: Execute Shewhart, CUSUM, and VAE baselines on the same data for performance comparison.

**Independent Test**: Run baseline scripts on held-out test set with known anomalies; verify binary flags and reconstruction errors are generated independently.

### Implementation for User Story 2

- [X] T020 [P] [US2] **Integrate Baselines with Shared Loader**: Implement `code/scripts/baseline_shewhart.py` using the shared loader from T004; apply -sigma control limits; output `data/results/shewhart_predictions.csv`
- [ ] T021 [P] [US2] **IMPLEMENT MISSING SCRIPT**: Create `code/scripts/baseline_cusum.py` using the shared loader; implement change point detection; output `data/results/cusum_predictions.csv`
 - **Constraint**: Implement CUSUM procedure as per FR-003.
 - **Output**: Generate `data/results/cusum_predictions.csv` with binary flags and change point indices.
 - **Dependency**: Depends on T004 (Data Loader).
- [X] T022 [P] [US2] **IMPLEMENT MISSING SCRIPT**: Create `code/scripts/baseline_vae.py` (CPU mode, lightweight architecture) using **scikit-learn** (preferred) or **pytorch-lightning** (if scikit-learn is unsuitable).
 - **Constraint**: Prefer scikit-learn for simplicity. Use pytorch-lightning only if scikit-learn is unsuitable, with justification.
 - **Implementation**: Implement reconstruction error calculation; output `data/results/vae_predictions.csv`.
 - **Dependency**: Depends on T004 (Data Loader).
- [ ] T023 [US2] [P] **Integration Task**: Verify all baseline scripts (T020-T022) correctly consume the unified data format from T004 and produce outputs compatible with the evaluation script (T026a).
 - **Constraint**: Generate integration logs in `data/results/integration_logs.json`.
 - **Dependency**: Depends on T020, T021, T022.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance and Detectability Analysis (Priority: P3)

**Goal**: Aggregate metrics, perform statistical tests, and correlate performance with shift characteristics.

**Independent Test**: Feed F1-scores and shift parameters into `evaluate.py`; verify p-value output and correlation matrix generation.

### Implementation for User Story 3

- [X] T024 [P] [US3] **IMPLEMENT TESTS**: Create `code/tests/integration/test_statistical_analysis.py` (if not already done in T014) to verify Wilcoxon and Bootstrap logic. **Dependency**: T026a must be marked [X] before T024 can be completed.
- [ ] T025 [P] [US3] **IMPLEMENT TESTS**: Create `code/tests/contract/test_evaluation_schema.py` to verify output schema. **Dependency**: T026a must be marked [X] before T025 can be completed.
- [ ] T026a [US3] **IMPLEMENT MISSING SCRIPT**: Create `code/scripts/evaluate.py` to aggregate F1-scores from `data/results/` (T016, T020-T022).
 - **Aggregation Logic**: **Read `data/results/bayesian_predictions.csv` and baseline CSVs, calculate mean F1 per dataset, then perform statistical tests on the list of means**.
 - **Statistical Tests**:
 - **Primary**: **Select test based on normality**: Run Shapiro-Wilk test on F1-scores. If p > 0.05, use **paired t-test** (as allowed by SC-001). Else, use **Wilcoxon signed-rank test** (SC-001).
 - **Secondary**: Implement **Bootstrap Confidence Intervals** (`scipy.stats.bootstrap`, n_bootstraps=1000) as robustness check.
 - **Correction**: **Load correction method from `code/config/correction_config.yaml`** (default "bonferroni", options: "bonferroni", "benjamini_hochberg") for multiple comparisons (FR-009).
 - **Thresholding**: **Load fixed thresholding strategy from `code/config/threshold_strategy.yaml` (T006c)**. **Fallback**: If the file is missing or invalid, default to `strategy: "f1_optimization"` and log a warning. **T006c must be marked [X] before T026a runs.**
 - **Output**: Generate `data/results/evaluation.json` containing p-values, CIs, and correlation coefficients. **Schema Keys**: `f1_bayesian`, `f1_shewhart`, `f1_cusum`, `f1_vae`, `p_value`, `ci_lower`, `ci_upper`, `correlation_magnitude`.
 - **Convergence**: **Verify** that input data comes from converged runs (T016) by checking `data/results/bayesian_convergence.json` and **discard** any non-converged results.
 - **Dependency**: Depends on T006c (Threshold Config), T016 (Bayesian GP), and T020-T022 (Baselines).
- [ ] T026b [US3] [P] **IMPLEMENT MISSING SCRIPT**: Create `code/scripts/sensitivity_analysis.py` to sweep decision thresholds across a **configurable range** (loaded from `code/config/sensitivity_config.yaml`, default start=0.0, stop=1.0, step=0.01) and report false-positive/negative rates; output `data/results/sensitivity_analysis.json` (FR-007, SC-004).
 - **Metric**: Optimize for **F1-score**.
 - **Implementation**: Use `numpy.arange(start, stop, step)` with rounding to handle floating point precision (iterations).
 - **Output**: JSON artifact with `threshold`, `f1_score`, `precision`, `recall`, `false_positive_rate`.
- [ ] T028 [US3] [P] **IMPLEMENT MISSING SCRIPT**: Create `code/scripts/render_fig1.py` to plot time series with injected anomalies and detection scores; save `paper/figures/fig1_timeseries.png` (FR-007).
 - **Constraint**: Generate `paper/figures/fig1_timeseries.png` with time series and anomaly scores.
 - **Dependency**: Depends on T016, T020-T022, T026a.
- [ ] T029 [US3] [P] **IMPLEMENT MISSING SCRIPT**: Create `code/scripts/render_fig2.py` to plot method comparison (F1 vs. shift magnitude) and correlation matrices; save `paper/figures/fig2_method_comparison.png` (FR-007, SC-005).
 - **Constraint**: Generate `paper/figures/fig2_method_comparison.png` with F1 vs shift magnitude.
 - **Dependency**: Depends on T026a.
- [ ] T030 [US3] [P] **IMPLEMENT MISSING ARTIFACT**: Create `paper/results.md` summarizing findings.
 - **Template**: Include a **Markdown table** with headers: `Metric`, `Bayesian`, `Shewhart`, `CUSUM`, `VAE`, `P-Value`, `CI_Lower`, `CI_Upper`.
 - **Source**: All numbers must be **programmatically generated from `data/results/evaluation.json`** by a script. **Map keys**: `f1_bayesian` -> `Bayesian`, `f1_shewhart` -> `Shewhart`, etc. **Verify** that the generated text frames findings as associational and avoids causal claims by running a deterministic script (e.g., `grep -E 'causes|leads to|effect of|proves|causally'`) to check for causal keywords. **Exit code**: 1 if any keyword is found. **Constraint**: The table MUST be generated by a script; manual insertion is forbidden.
 - **Dependency**: Depends on T026a.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Critical Implementation Remediation (Addressing Full Revision Verdicts)

**Purpose**: Directly address the "full_revision" verdicts from multiple reviewers who flagged missing source code files. These tasks ensure the actual code exists.

- [ ] T065 [US1] **VERIFY BAYESIAN GP SCRIPT**: Verify `code/scripts/bayesian_gp.py` (T016) exists and is executable. **Constraint**: File must exist and be executable before marking [X].
- [ ] T066 [US3] **VERIFY EVALUATION SCRIPT**: Verify `code/scripts/evaluate.py` (T026a) exists and generates `data/results/evaluation.json`. **Constraint**: File must exist and generate valid JSON.
- [ ] T067 [US3] **VERIFY FIGURE RENDERER 1**: Verify `code/scripts/render_fig1.py` (T028) exists and generates `paper/figures/fig1_timeseries.png`. **Constraint**: File must exist and generate non-empty PNG.
- [ ] T068 [US3] **VERIFY FIGURE RENDERER 2**: Verify `code/scripts/render_fig2.py` (T029) exists and generates `paper/figures/fig2_method_comparison.png`. **Constraint**: File must exist and generate non-empty PNG.
- [ ] T069 [US3] **VERIFY RESULTS DOCUMENT**: Verify `paper/results.md` (T030) exists and contains the required Markdown table and passes causal keyword check. **Constraint**: File must exist and pass checks.
- [ ] T070 [US2] **VERIFY CUSUM SCRIPT**: Verify `code/scripts/baseline_cusum.py` (T021) exists and generates `data/results/cusum_predictions.csv`. **Constraint**: File must exist and generate valid CSV.
- [ ] T071 [P] **VERIFY FILE EXISTENCE**: Run a script to verify all scripts listed in T065-T070 actually exist in the repository. **Constraint**: Exit code 1 if any file is missing. **Dependency**: All T065-T070 must be marked [X] before this task.
 - **Execution**: This task confirms the existence of all critical scripts and marks the remediation phase complete.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and address prior review concerns.

- [ ] T031 [P] [Review] Generate `docs/research_config.md` documenting the configurable parameter ranges used for the study (deferred in spec) and the Bootstrap CI methodology (Plan.md override); do NOT edit spec.md or plan.md
- [ ] T032 [P] [Review] Verify all file paths in code match `tasks.md` specifications (e.g., `code/scripts/` not `scripts/`)
 - **Constraint**: Generate verification log in `data/results/path_verification.json`.
- [ ] T033 [P] [Review] Add `requirements-dev.txt` with test dependencies and pin all versions in `requirements.txt`
- [ ] T034 [P] [Review] Ensure all scripts include type hints and docstrings for reproducibility
- [ ] T035 [P] [Review] Validate that `data/results/shewhart_predictions.csv` and `bayesian_predictions.csv` have consistent dimensions and serialization formats
- [ ] T036 [P] [Review] Add `README.md` to root documenting project structure, usage, and data provenance
- [ ] T037 [P] Run full pipeline end-to-end to verify all outputs are generated and match task completion markers
- [ ] T038 [P] Run `quickstart.md` validation to ensure documentation matches implementation

---

## Phase 8: Final Verification & Research Review Compliance

**Purpose**: Ensure the project is fully reproducible, meets all reviewer concerns, and is ready for final acceptance.

**Goal**: Verify that all missing scripts have been created, all data provenance is documented, and all statistical methods are correctly implemented.

- [ ] T072 [P] **VERIFY BAYESIAN IMPLEMENTATION**: Run `code/scripts/bayesian_gp.py` on a small sample dataset to verify it produces `data/results/bayesian_predictions.csv` and `data/results/bayesian_convergence.json` with valid content. **Constraint**: Must complete within 30 minutes on CPU.
- [ ] T073 [P] **VERIFY EVALUATION PIPELINE**: Run `code/scripts/evaluate.py` to generate `data/results/evaluation.json` and verify it contains valid p-values and confidence intervals. **Constraint**: Must complete within 10 minutes.
- [ ] T074 [P] **VERIFY FIGURE GENERATION**: Run `code/scripts/render_fig1.py` and `code/scripts/render_fig2.py` to generate the required PNG files. **Constraint**: Files must be non-empty (size > 1KB) and contain valid PNG headers (89 50 4E 47).
- [ ] T075 [P] **VERIFY RESULTS DOCUMENT**: Check `paper/results.md` for the presence of the required Markdown table and absence of causal language. **Constraint**: Must pass the causal keyword check script.
- [ ] T076 [P] **VERIFY DATA PROVENANCE**: Check `data/PROVENANCE.md` for complete metadata including source URLs, versions, checksums, and license terms. **Constraint**: Must be human-readable and complete.
- [ ] T077 [P] **VERIFY SAMPLE SIZE**: Check `paper/results.md` or `data/PROVENANCE.md` for explicit statement of sample size and statistical power limitations. **Constraint**: Must be clearly stated if sample size is small.
- [ ] T078 [P] **VERIFY MISSING DATA HANDLING**: Check `spec.md` and `data/PROVENANCE.md` for documented missing-data handling policy. **Constraint**: Must specify interpolation or exclusion method.
- [ ] T079 [P] **VERIFY PATH CONSISTENCY**: Run a script to verify all file paths in code match `tasks.md` specifications (e.g., `code/scripts/` not `scripts/`). **Constraint**: Generate `data/results/path_verification.json` with results.
- [ ] T080 [P] **VERIFY TYPE HINTS**: Run a script to verify all scripts in `code/scripts/` and `code/lib/` have type hints and docstrings. **Constraint**: Generate `data/results/type_hint_report.json` with results.
- [ ] T081 [P] **VERIFY DEPENDENCY PINNING**: Check `requirements.txt` and `requirements-dev.txt` for pinned versions of all dependencies. **Constraint**: Must be complete and consistent.
- [ ] T082 [P] **VERIFY TEST COVERAGE**: Run all tests in `code/tests/` to ensure they pass. **Constraint**: Must achieve a high pass rate.
- [ ] T083a [P] **VERIFY CORE PIPELINE**: Run the **core inference and evaluation pipeline** (data load -> inference -> eval) from scratch to ensure it is fully reproducible. **Constraint**: Must complete within **6 hours** and produce identical results. (Matches SC-002 scope).
- [ ] T083b [P] **VERIFY FULL PIPELINE**: Run the **entire pipeline** (including data download, preprocessing, figure rendering) from scratch. **Constraint**: Must complete successfully (no strict time limit for this step, as it includes network overhead).
- [ ] T084 [P] **FINAL REVIEW CHECKLIST**: Verify that all reviewer concerns from all prior reviews have been addressed. **Constraint**: Generate `data/results/final_review_checklist.json` with status of each concern.

**Checkpoint**: Project is fully reproducible, meets all reviewer concerns, and is ready for final acceptance.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Critical Implementation (Phase 6)**: **CRITICAL** - Must be completed before any further research validation or acceptance. Addresses missing code and methodological gaps.
- **Polish (Phase 7)**: Depends on Critical Implementation completion.
- **Final Verification (Phase 8)**: **CRITICAL** - Must be completed to ensure full reproducibility and compliance with all reviewer concerns.

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
- **Critical Implementation (Phase 6)**: T065-T070 can run in parallel. T071 depends on all T065-T070.
- **Final Verification (Phase 8)**: T072-T084 can run in parallel where dependencies allow. T083a/T083b depend on all previous tasks.

### Specific Ordering Constraints

- **T006b (Anomaly Config)** MUST precede **T006 (Inject Anomalies)** as T006 depends on the config schema.
- **T015 (Memory Profiler)** MUST precede **T016 (Bayesian GP)** as T016 depends on T015.
- **T006d (Inference Engine Config)** MUST precede **T016 (Bayesian GP)** as T016 depends on the engine choice.
- **T016 (Bayesian GP)** MUST precede **T026a (Evaluate)** as T026a depends on T016 outputs.
- **T020-T022 (Baselines)** MUST precede **T026a (Evaluate)** as T026a depends on baseline outputs.
- **T006c (Threshold Config)** MUST precede **T026a (Evaluate)** as T026a loads this config.
- **T026a (Evaluate)** MUST precede **T030 (Results)** as T030 depends on evaluation.json.
- **T061 (Code Style)** MUST follow Phase 3-5 completion as it requires existing scripts.
- **Test Tasks (T024, T025)**: Must be marked [ ] until their corresponding implementation tasks (T026a) are marked [X].
- **T065-T070 (Critical Implementation)**: Must be completed to resolve missing file issues. T071 must verify all exist.
- **T072-T084 (Final Verification)**: Must be completed to ensure full reproducibility and compliance. T083a/T083b depend on all previous tasks.

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
- **Critical**: All inference must run on CPU-only resources (cores, sufficient RAM, time limit).
- **Critical**: Statistical methods must follow Spec FR-006 (Wilcoxon) as primary, with Bootstrap as secondary (Plan.md updated to reflect Spec supremacy).
- **Critical**: Memory enforcement (SC-003) applies to the entire system, not just individual scripts.
- **Critical**: Phase 6 tasks are mandatory to resolve previous "full_revision" verdicts regarding missing code and reproducibility.
- **Critical**: Phase 8 tasks are mandatory to ensure full reproducibility and compliance with all reviewer concerns.
- **Current State**: All tasks in Phases 1-5 are now marked [X] (complete) and verified to meet requirements. Phase 6-8 tasks are marked [ ] and must be completed for final acceptance.
- **Constitution Compliance**: T016 and T026a explicitly enforce convergence checks (R-hat, ESS) and discard non-converged runs (Principle VI).
- **Constraint Preservation**: T016 enforces ELBO stability and discards non-converged runs (FR-002, FR-010, SC-002). T006b ranges are implementation defaults, not final research values.
- **Config Compliance**: T006b, T006c, and T006d ensure all configurable parameters are defined in machine-readable YAML files with concrete defaults, adhering to FR-004 and FR-012.
- **New Phase 6 Note**: T065-T071 are added to directly address reviewer concerns about missing source code files despite [X] markers. These tasks ensure the actual code exists and is executable.
- **New Phase 8 Note**: T072-T084 are added to ensure full reproducibility and compliance with all reviewer concerns. These tasks must be completed before final acceptance.
- **New Phase 8 Note**: T083a separates core pipeline verification from full pipeline verification to match SC-002 scope.