# Tasks: Quantifying the Impact of Data Artifacts on Planetary Nebula Morphology

**Input**: Design documents from `/specs/001-quantify-artifact-bias/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a1 [P] Create `code/` directory and subdirectories: `synthetic`, `metrics`, `analysis`, `io`
- [X] T001a2 [P] Create `data/` directory and subdirectories: `raw`, `synthetic`, `processed`, `validation`
- [X] T001a3 [P] Create `tests/` directory and subdirectories: `unit`, `contract`, `integration`
- [X] T001a4 [P] Create `logs/` directory
- [X] T001b [P] Create `.gitignore` excluding `data/`, `__pycache__`, `*.pyc`, `logs/`, `*.log`
- [X] T001c [P] Initialize `README.md` with project overview and quickstart instructions
- [X] T003 [P] Configure linting (ruff/flake) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

**Dependency Note**: T006 (Generation) MUST complete before T005 (Loader) if T005 validates generated files. T009 (Real HST) must complete before T028/T031 (Validation tasks in Phase 5). T046a (CLI Stub) MUST complete before US1/US2 implementation. T037b (Spec Update) MUST complete before T021/T024.

- [X] T037a [P] **Create Decision Document**: Create `docs/decisions/001-saturation-range.md` formally resolving the saturation range to `0.0 to 0.5 in 0.05 increments`. (FR-003, SC-003)
- [X] T037b [P] **Update Spec**: Update `spec.md` (FR-003, SC-003, Assumptions, US2 Acceptance 1) to replace all `[deferred]` placeholders with `0.0 to 0.5 in 0.05 increments` based on T037a. (FR-003, SC-003)
- [X] T037c [P] **Update Config**: Update `code/config.py` to reflect saturation range `0.0 to 0.5` with step `0.05` as defaults. (FR-003)
- [X] T009 [P] **CRITICAL**: Acquire, vet, checksum, and process exactly **2** real HST images (MAST) for **qualitative validation only** as required by Constitution Principle VII. **Targets**: NGC 7009 (Saturn Nebula), NGC 6543 (Cat's Eye). **Fallback**: If validation fails, use NGC 6572. **Criteria**: Bipolar/elliptical morphology, calibrated flux, valid WCS. **Output**: Store in `data/validation/`, create `data/validation/validation_manifest.json` with schema `{ "target_id": str, "file_path": str, "morphology_type": str, "checksum": str }`. **Query**: MAST `target='NGC 7009' OR target='NGC 6543' filter='F658N' instrument='ACS'`. Note: This task is for qualitative validation only; bias quantification remains synthetic. (Plan: Constitution Check Principle VII)
- [X] T006 [P] **CRITICAL**: Create `code/synthetic/generator.py` to generate **50** synthetic planetary nebulae with known ground-truth ellipticity and asymmetry (no GPU, CPU-only). **Naming**: Save images as `data/synthetic/synth_{id:03d}.fits` where `id` ranges from `000` to `049`. **Ground Truth**: Save exact ground-truth values to `data/synthetic/gt_metadata.json` with schema `{ "image_id": str, "filename": str, "ellipticity": float, "asymmetry": float, "checksum": str }`. **Seed**: Use multiple synthetic sources with ellipticity in a moderate range and asymmetry within a low-to-moderate interval. (FR-001, Constitution Principle IV)
- [X] T002 [P] Initialize Python 3.11 project with `requirements.txt` (numpy, scikit-image, astropy, scipy, statsmodels, pandas, matplotlib, pytest)
- [X] T004 [P] Create `code/config.py` with pinned random seeds, default paths, and **concrete** artifact parameters: noise levels `{0.01, 0.05, 0.10}`, saturation range `0.0` to `0.5` in `0.05` increments (FR-002, FR-003, SC-003)
- [X] T007 [P] Implement `code/io/writer.py` to save generated images and logs with checksums for reproducibility (FR-008)
- [X] T008 [P] Setup `tests/unit/` structure and `pytest` configuration
- [X] T046a [P] **Create CLI Stub**: Create `code/main.py` as the single CLI entry point with `--run-all` flag. Implement `main()` stub and basic argument parsing. Do NOT implement `validate_pipeline_state()` yet. (FR-001, FR-008)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Evaluate Noise‑Induced Bias on Ellipticity (Priority: P1) 🎯 MVP

**Goal**: Quantify how varying Gaussian noise levels bias ellipticity measurements against a known ground truth.

**Independent Test**: Run pipeline on clean synthetic image, inject specific noise level, compute ellipticity, and verify deviation from ground truth.

**Dependency Note**: Tasks T010-T012 depend on T005 completion. T015 depends on T006 completion. T015 depends on T016. T014 depends on T006.

### Tests for User Story 1 (MANDATORY) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T010 [P] [US1] Contract test for `code/io/loader.py` in `tests/unit/test_loader.py`: **Function `test_loader_raises_on_missing_wcs`** asserting that `loader.load()` raises `ValueError` when WCS metadata is missing (FR-009)
- [X] T011 [P] [US1] Unit test for noise injection logic in `tests/unit/test_artifacts.py`: **Function `test_noise_injection_sigma`** asserting that injected noise matches target sigma within tolerance (FR-002)
- [X] T012 [P] [US1] Unit test for ellipticity calculation in `tests/unit/test_ellipticity.py`: **Function `test_ellipticity_calculation`** asserting that second-order moments yield correct ellipticity for a known synthetic shape (FR-004)

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement `code/metrics/ellipticity.py` using second-order moments (FR-004)
- [X] T014 [P] [US1] Implement `code/synthetic/artifacts.py` noise injection function: **Iterate over a range of sigma levels.**, save results to `data/processed/noise_sweep_{sigma_value}.fits`. **FITS Header**: Include `NOISE_SIGMA`, `WCS`, `FILTER`, `EXPTIME`. **Aggregate results into `data/processed/noise_trend_report.csv` to verify monotonic bias trends (SC-003)**. (FR-002)
- [X] T016 [P] [US1] Implement statistical test logic in `code/analysis/statistics.py`: **Function `run_noise_regression`** performing **Linear Regression** linking artifact magnitude to parameter deviation with Bonferroni correction; output coefficients and p-values to `data/processed/noise_stats.csv` with schema `{ "sigma": float, "mean_bias": float, "p_value": float, "significant": bool, "slope": float }` (FR-005, SC-003)
- [X] T015 [P] [US1] Implement `run_us1_pipeline` function in `code/main.py`: load clean image -> inject noise (T014) -> measure ellipticity (T013) -> **load ground truth from `data/synthetic/gt_metadata.json`** -> compute bias -> **call `run_noise_regression` (T016)** -> log results (FR-001, FR-008)
- [X] T017 [P] [US1] Add logging for noise parameters, seeds, and bias results to `logs/research.log`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Quantify Saturation‑Induced Bias on Asymmetry (Priority: P2)

**Goal**: Determine if pixel-level saturation systematically inflates the asymmetry index.

**Independent Test**: Inject controlled saturation, compute asymmetry, and test against clean baseline.

### Tests for User Story 2 (MANDATORY) ⚠️

- [X] T018 [P] [US2] Unit test for saturation clipping logic in `tests/unit/test_artifacts.py`: **Function `test_saturation_clipping`** asserting that the correct fraction of brightest pixels are clipped (FR-003)
- [X] T019 [P] [US2] Unit test for asymmetry calculation in `tests/unit/test_asymmetry.py`: **Function `test_asymmetry_conselice`** asserting that the A-statistic matches the Conselice (2003) definition (FR-004)

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `code/metrics/asymmetry.py` using Conselice (2003) definition with robust centering (FR-004)
- [X] T021 [P] [US2] Implement `code/synthetic/artifacts.py` saturation clipping function: **Generate files for a range of saturation fractions spanning from 0.00 to 0.50.**. **Output**: Save each artifact as `data/processed/sat_{fraction:.2f}.fits`. **Flag**: If clipping results in zero signal, log warning and mark as `valid=False` in metadata. (FR-003)
- [X] T023 [P] [US2] Implement statistical test logic in `code/analysis/statistics.py`: **Function `run_saturation_regression`** performing **Linear Regression** linking artifact magnitude to parameter deviation with Bonferroni correction; output coefficients and p-values to `data/processed/saturation_stats.csv` with schema `{ "saturation_fraction": float, "mean_bias": float, "p_value": float, "significant": bool, "slope": float }` (FR-005, SC-003)
- [X] T040 [P] [US2] Update `run_us2_pipeline` in `code/main.py` to explicitly load the ground-truth metadata from `data/synthetic/gt_metadata.json` before computing asymmetry bias, ensuring the "Single Source of Truth" principle is followed in the pipeline execution flow.
- [X] T022 [P] [US2] Implement `run_us2_pipeline` function in `code/main.py`: load clean image -> inject saturation (T021) -> measure asymmetry (T020) -> **load ground truth from `data/synthetic/gt_metadata.json`** -> **call `run_saturation_regression` (T023)** -> compute bias -> log results (FR-001, FR-008)
- [X] T024 [P] [US2] Implement sensitivity analysis sweep: **range from a minimum threshold up to 0.5, with incremental steps of 0.05**; aggregate results from T021 into `data/processed/saturation_sweep.csv` with columns [saturation_fraction, asymmetry_mean, asymmetry_std, valid]; **generate statistical summary** to verify p < 0.05 and monotonic trends (SC-003). (SC-003)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Derive Calibration Functions to Correct Bias (Priority: P3)

**Goal**: Fit regression models linking artifact intensity to bias and derive correction functions.

**Independent Test**: Apply derived correction to synthetic data and verify residual bias is non-significant.

**Dependency Note**: US3 depends on data aggregation from US1 and US2, and specifically on the completion of T027 (regression model) and T028 (validation logic). **T028 and T031 require T009 (Real HST validation) to be complete.** **T028 requires T041 (Aggregation).**

### Tests for User Story 3 (MANDATORY) ⚠️

- [X] T025 [P] [US3] Contract test for regression model output schema in `tests/contract/test_regression.py`
- [X] T026 [P] [US3] Unit test for correction application logic in `tests/unit/test_validation.py`

### Implementation for User Story 3

- [X] T027 [P] [US3] Implement `code/analysis/regression.py` to fit linear/polynomial models (artifact intensity -> bias) using AIC for model selection (FR-005)
- [X] T041 [P] [US3] **Aggregate Bias Data**: Implement a data-aggregation task in `code/analysis/validation.py` that merges the CSV outputs from T015 (noise) and T022 (saturation) into a single `data/processed/aggregated_bias.csv` before regression, ensuring US3 has a unified input source.
- [X] T028 [US3] Implement `code/analysis/validation.py` to apply inverse correction and compute residual bias; **generate statistical report** (p-values, confidence intervals) for residual bias as mandated by FR-007. **Requires T009 (Real HST validation) for qualitative morphology check, but quantitative validation is synthetic.** (FR-007)
- [X] T029 [P] [US3] Add function `run_us3_pipeline` to `code/main.py`: aggregate results from US1/US2 -> fit models -> apply corrections -> validate (FR-006, FR-007)
- [X] T030 [US3] **Power Analysis and Cross-Validation**: Implement `code/analysis/power_analysis.py` to perform a **Post-hoc Limitation Check** verifying n=50 achieves ≥80% power for effect size. **Parameters**: alpha=0.05, test_type='two-sample t-test', effect_size='Cohen's d'. **Execute after US1/US2 data collection** to use observed effect size. **Include cross-validation loop** to test derived calibration functions on a held-out subset of the synthetic data (merged from T048). **Output**: `data/validation/power_analysis_report.md` with explicit limitation documentation if power < 80% (SC-004). **Schema**: Include 'Observed Effect Size', 'Calculated Power', 'Conclusion', 'Limitations', 'Cross-Validation Results'.
- [X] T031 [US3] Generate final calibration function outputs: save to `data/processed/calibration_functions.json` with schema `{ "ellipticity_model": {...}, "asymmetry_model": {...} }` and validation report linking to underlying files. **Requires T009 (Real HST validation) for qualitative morphology check.** (SC-002)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T032a [P] Update `quickstart.md`: Add sections on data generation, artifact injection, and metric calculation with code snippets
- [X] T032b [P] Update `research.md`: Add sections on results, bias trends, and calibration function performance
- [X] T033 [P] Code cleanup and refactoring of `code/main.py` into modular CLI entry points
- [X] T034 [P] Performance optimization: Ensure full sensitivity sweep runs < 4 hours on 2 CPU cores
- [X] T035 [P] Integration test for full pipeline (Synth -> Inject -> Measure -> Correct -> Validate) in `tests/integration/test_pipeline.py`
- [X] T036 [P] Run `quickstart.md` validation to ensure all artifacts are reproducible
- [X] T038 [US2] **Add Saturation Validation Guard**: Add a validation guard in `code/synthetic/artifacts.py` saturation logic that raises a `ValueError` if the clipping fraction exceeds a high threshold or results in zero total signal for a standard nebula profile, preventing silent generation of unusable artifacts.
- [X] T039 [US3] **Enforce Zero-Intercept Constraint**: Modify `code/analysis/regression.py` to enforce a zero-intercept constraint (or explicit offset modeling) when the artifact intensity is zero, ensuring the baseline bias is mathematically consistent with the ground-truth definition.
- [X] T042 [US1] **Validate Noise Injection**: Refactor `code/synthetic/artifacts.py` to implement a robust noise injection routine that validates the injected noise standard deviation against the target sigma within a tight tolerance, raising a `ValueError` on deviation to ensure FR-002 compliance.
- [X] T043 [US2] **Handle Disconnected Cores**: Update `code/synthetic/artifacts.py` saturation logic to explicitly handle edge cases where saturation clipping results in a disconnected nebula core, logging a warning and flagging the image in `data/processed/saturation_sweep.csv` as `valid=False` rather than crashing.
- [X] T044 [US3] **Automate Model Selection**: Enhance `code/analysis/regression.py` to automatically select between linear and quadratic models based on the Akaike Information Criterion (AIC) rather than hard-coding a single model type, ensuring the best fit for the observed bias trends.
- [X] T045 [US3] **Implement Cross-Validation**: Implement a cross-validation loop in `code/analysis/validation.py` to test the derived calibration functions on a held-out subset of the synthetic data, ensuring the correction generalizes beyond the training set.
- [X] T046b [P] **Implement Validation Logic**: Implement `validate_pipeline_state()` in `code/main.py` to check for `data/synthetic/gt_metadata.json` before US1/US2 and `data/processed/aggregated_bias.csv` before US3. Abort execution with clear error messages if dependencies are missing. (FR-001, FR-008)
- [X] T046c [P] **Wire Orchestration**: Update `main()` in `code/main.py` to wire the full pipeline execution flow: US1 -> US2 -> US3 based on `--run-all` flag. (FR-001, FR-008)

---

## Phase N+1: Review Resolution & Robustness Enhancements

**Purpose**: Address specific reviewer concerns regarding data flow, edge cases, and statistical rigor.

- [ ] T047 [US1] **Enforce Data Flow Dependency**: Refactor `code/main.py` and `code/synthetic/generator.py` to ensure `run_us1_pipeline` explicitly waits for and validates the existence of `data/synthetic/gt_metadata.json` (produced by T006) before attempting to load ground truth, preventing race conditions in parallel execution. (Review Concern: Data Flow)
- [X] T048 [US2] **Implement Robust Edge-Case Handling**: Update `code/synthetic/artifacts.py` to detect and handle "extreme artifact levels" (e.g., saturation > 0.5 or noise σ > 0.10) as defined in Edge Cases, logging a specific warning and skipping the metric calculation for that specific image rather than crashing or producing NaNs. (Review Concern: Edge Cases) <!-- ATOMIZE: requested -->
- [ ] T049 [US3] **Formalize Power Analysis Limitations**: Update `code/analysis/power_analysis.py` to explicitly calculate and report the "Minimum Detectable Effect Size" (MDES) given the n=50 constraint, and ensure `data/validation/power_analysis_report.md` clearly states if the study is underpowered for subtle biases (< 0.05). (Review Concern: Statistical Rigor)
- [ ] T050 [US1/US2] **Add Reproducibility Audit Trail**: Extend `code/io/writer.py` to generate a `data/processed/run_manifest.json` that captures the exact git commit hash, environment variables, and full artifact parameter set used for *every* run, ensuring FR-008 compliance is verifiable post-hoc. (Review Concern: Reproducibility)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **Note**: T006 (Generation) produces files that T005 (Loader) validates; T006 is a prerequisite for T005.
 - **Note**: T009 (Real HST) must complete before T028/T031 (Validation tasks in Phase 5).
 - **Note**: T046a (CLI Stub) must complete before US1/US2 implementation.
 - **Note**: T037b (Spec Update) must complete before T021/T024.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Review Resolution (Phase N+1)**: Depends on completion of all User Story phases to address findings.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on data aggregation from US1 and US2 **and completion of T027 (regression) and T028 (validation)** and **T041 (Aggregation)** and **T009 (Real HST)**

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Metrics before services/pipeline steps
- Core implementation before integration
- Story complete before moving to next priority
- **Statistical Logic (T016, T023) must be implemented before Pipeline Steps (T015, T022) that consume their output.**
- **Injection (T014, T021) must be implemented before Statistical Logic (T016, T023).**

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 and US2 can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (US1/US2 parallel, US3 after)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Contract test for loader in tests/unit/test_loader.py (test_loader_raises_on_missing_wcs)"
Task: "Unit test for noise injection in tests/unit/test_artifacts.py (test_noise_injection_sigma)"
Task: "Unit test for ellipticity in tests/unit/test_ellipticity.py (test_ellipticity_calculation)"

# Launch models/metrics for User Story 1 together:
Task: "Implement code/metrics/ellipticity.py"
Task: "Implement code/synthetic/artifacts.py (noise)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (Clean vs. Noise)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo (Calibration)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Noise/Ellipticity)
 - Developer B: User Story 2 (Saturation/Asymmetry)
3. Developer C: User Story 3 (Calibration/Regression) - starts after US1/US2 data available
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Constraint**: All tasks must run on CPU-only CI with a limited number of cores and memory. No GPU, no 8-bit quantization, no deep learning.
- **Data**: Synthetic data generation must be deterministic and checksummed. No fake data for final metrics; use synthetic ground truth for validation.
- **Ground Truth**: All ground-truth values MUST be saved to machine-readable artifacts (JSON/CSV) as per Constitution Principle IV.
- **Saturation Range**: Concrete values (0.0-0.5, step 0.05) are defined in T037a and used in T021/T024.
- **Real HST Validation**: T009 must be completed before T028/T031 to satisfy Constitution Principle VII (qualitative only).
- **Power Analysis**: T030 must be executed after US1/US2 data collection to use observed effect size.
- **CLI**: T046a/46b/46c define the single entry point; T015/T022/T029 implement functions within it.
- **Review Resolution**: Tasks T047-T050 address specific reviewer concerns regarding data flow, edge cases, and statistical rigor.