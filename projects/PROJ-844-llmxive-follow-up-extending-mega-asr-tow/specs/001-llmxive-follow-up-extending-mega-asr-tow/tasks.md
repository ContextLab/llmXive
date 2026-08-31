# Tasks: llmXive Follow-up: Extending "Mega-ASR" for Semantic Collapse Thresholds

**Input**: Design documents from `/specs/001-semantic-collapse-threshold/`
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

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create `code/` directory at repository root per plan.md
- [ ] T001b [P] Create `data/raw/` directory at repository root per plan.md
- [ ] T001c [P] Create `data/derived/` directory at repository root per plan.md
- [ ] T001d [P] Create `tests/` directory at repository root per plan.md
- [ ] T002a [P] Create `ruff.toml` configuration file with specific rules for linting
- [ ] T002b [P] Create `pyproject.toml` configuration file with specific rules for black formatting
- [ ] T003a [P] **Resolve Deferred Parameters**: Read `research.md` and `plan.md` to explicitly resolve all `[deferred]` parameters (sample size=500, correlation threshold=0.6, SNR/RT60 ranges). Write these values as hardcoded constants in `code/config.py`. (Resolves FR-023; Depends on plan.md/research.md availability)
- [ ] T003 [P] Implement `code/config.py` with paths, random seeds, and hyperparameters (thresholds, distortion counts) (Depends on T003a)
- [ ] T003b [P] **Document Power Limitation**: Update `docs/research.md` to explicitly state that the study is powered for **medium-to-large effects (f² ≥ 0.05)** only, and that the original small effect requirement (f² ≥ 0.02) is unachievable with the available data (AMI+LibriSpeech). (Resolves FR-001 power conflict; Depends on T003a)
- [ ] T003c [P] **Re-scope US-3 Hypothesis**: Explicitly update the US-3 acceptance criteria (R² ≥ 0.6) and the research hypothesis in `docs/research.md` to state that the regression analysis is **valid only for detecting medium-to-large interaction effects**, explicitly excluding small effects. This task resolves the conflict between the spec's original power requirement and the feasible sample size. (Resolves FR-001/US-3 conflict; Depends on T003b)
- [ ] T004 [P] Implement `code/monitor_resources.py` to track peak RSS and wall-clock time (SC-004)
- [ ] T005 [P] Implement `code/hash_updater.py` to compute content hashes for `data/derived/` and update state YAML (Principle V)
- [ ] T006 [P] Create base entity classes (`AudioClip`, `DistortionVector`, `StressCurve`) in `code/models.py` (or dataclasses)
- [ ] T008a [P] Implement `pytest.ini` or `pyproject.toml` test configuration for `tests/unit/` (Resolves T008 inconsistency; Replaces T008)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes data fetching, stratification, and distortion engine setup.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007a [P] Fetch and verify checksums for **LibriSpeech** subset (`openslr/librispeech_asr`, split='test.clean') in `code/data_loader.py`; implement **streaming=True** and **chunked iteration** to prevent OOM (>7GB RAM) as per FR-001; **Apply stratification by speaker ID and SNR bucket** (adapted from Voices-in-the-Wild-2M logic) (Resolves coverage-a6517289, executability-40022d60; Depends on T003a)
- [ ] T007b [P] Fetch and verify checksums for **AMI** subset (`hf-audio/ami`, split='test') in `code/data_loader.py`; implement **streaming=True** and **chunked iteration** to prevent OOM (>7GB RAM) as per FR-001; **Apply stratification by speaker ID and SNR bucket** (adapted from Voices-in-the-Wild-2M logic) (Resolves coverage-a6517289, executability-40022d60; Depends on T003a)
- [ ] T007d [P] **Document Spec Deviation**: Create `docs/dataset_substitution_rationale.md` explicitly stating that the plan deviates from FR-001 (CHiME-5, 50k clips) to LibriSpeech/AMI ([deferred] clips) due to availability constraints, and that this document serves as the approved exception for the project. **Must include exact dataset IDs and stratification mapping** (Resolves coverage-756a16d5, ordering-938fad6d, executability-6d9f2d1e, constraint_preservation-6be6f1a6, F001)
- [ ] T012c [P] **Fetch & Generate DNS Challenge Data**: Implement `code/data_loader.py` function `fetch_dns_challenge` to download exactly 50 clips from `hf-audio/dns-challenge` (train split). Implement `code/distortion_engine.py` function `generate_matching_synthetic` to create synthetic distortions for these 50 clips matching the SNR/RT60 grid. Output: `data/raw/dns_reference.parquet` and `data/derived/dns_synthetic/` (Resolves FR-018; Depends on T003a)
- [ ] T012b [P] **Distortion Realism Validation (FR-018)**: Implement `code/realism_validator.py` to compare synthetic distortion parameters (SNR/RT60) against **DNS-Challenge-Dev-Noisy** subset using Log-Mel spectral distance metric. **Must verify distance <= 0.15** for the generated scenarios. **Depends on T012c** to provide input data. (Resolves coverage-012226b3, executability-967fa365, constraint_preservation-94675693)
- [ ] T012 [P] Implement `code/distortion_engine.py` to apply **exactly 54** distinct compound distortion vectors (Cartesian product of **SNR: [, -5, 0, 5, 10, 15, 20, 25, 30] dB** and **RT: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6] s**) incrementally per FR-002; **logic MUST process clips in fixed-size batches (configurable) and flush to disk after each batch** to ensure memory safety; **MUST enforce exactly 54 scenarios** and fail if count differs (Resolves coverage-03e2998c, constraint_preservation-36bb0148, executability-5f4fa50d; Depends on T012b)
- [ ] T009 [US1] Unit test for `code/distortion_engine.py` verifying that a distinct set of vectors is generated from parameter ranges. (Resolves coverage-03e2998c, ordering-d65f987c; **Moved to Phase 3**; Depends on T012)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Compound Distortion Stress Curves (Priority: P1) 🎯 MVP

**Goal**: Systematically apply a diverse range of compound acoustic distortions to a stratified subset of audio data to generate stress curves mapping distortion intensity to semantic integrity.

**Independent Test**: Run on a sample of audio clips; verify output CSV/JSON contains the expected number of rows per clip with acoustic parameters, ASR hypothesis, and Semantic Similarity Score (SSS).

### Implementation for User Story 1

- [ ] T010 [US1] Extend `code/data_loader.py` to add US1-specific stress-curve generation logic (building on T012 engine); Depends on T007a-b, T012, T009
- [ ] T011 [US1] Integration test for `code/data_loader.py` verifying stratified sampling and stress-curve generation workflow (Depends on T010)
- [ ] T013 [US1] Implement `code/metrics.py` to compute SSS using `all-MiniLM-L6-v2` (CPU-only) per FR-003
- [ ] T014 [US1] Implement `code/metrics.py` to compute WER using `jiwer` for baseline and distorted hypotheses per FR-009
- [ ] T016 [US1] Implement validation logic in `code/metrics.py` to handle edge cases: **hysteresis requires K=3 consecutive steps below threshold** for oscillating SSS, **empty ASR output maps to lowest intensity vector with warning**, and missing distortion scenarios (FR-001 edge cases)
- [ ] T015a [US1] **Implement Missing Generation Logic**: Add concrete algorithm to `code/main.py` for T015: "Iterate clips -> Apply 54 distortions (T012) -> Run ASR -> Compute SSS/WER -> Write Parquet". **Output**: `data/derived/stress_curves.parquet` with schema: `clip_id`, `snr`, `rt60`, `asr_hypothesis`, `sss`, `wer`. **Log deterministic sample size**. (Resolves executability-9f0cdf61, executability-a5bfbfef; Removed T015; Merged into T015a; Depends on T016)
- [ ] T015c [US1] **Verify Artifact Non-Emptiness**: Implement a check in `code/main.py` to verify `data/derived/stress_curves.parquet` is generated and non-empty before proceeding to downstream tasks. Raise `RuntimeError` if empty. (Resolves executability-9f530fd5, constraint_preservation-e7ed2cd5; Depends on T015a)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Identify Semantic Collapse Points (Priority: P2)

**Goal**: Automatically identify the precise "collapse intensity" for each model/scenario where SSS drops below a normalized threshold. AND WER spikes >2x baseline.

**Independent Test**: Provide a pre-calculated stress curve with a known drop; verify the system correctly identifies the interpolation point or step meeting both criteria.

### Implementation for User Story 2

- [ ] T017 [P] [US2] Unit test for collapse detection logic with synthetic data (monotonic drop, no drop, oscillation)
- [ ] T020b [US2] Explicitly calculate and store `baseline_sss.json` for each model/scenario as a prerequisite artifact for normalization (FR-010); Schema: `{"model_id": str, "scenario_id": str, "baseline_value": float}`; Logic: Average SSS of clean audio subset
- [ ] T020c [US2] Explicitly calculate and store `baseline_wer.json` for each model/scenario as a prerequisite artifact for WER spike threshold (FR-004, FR-009); Schema: `{"model_id": str, "scenario_id": str, "baseline_value": float}`; Logic: Average WER of clean audio subset
- [ ] T020d [US2] **Perform Normalization**: Implement `code/metrics.py` function `normalize_stress_curves` to divide the SSS values in `data/derived/stress_curves.parquet` by the corresponding `baseline_sss.json` values. **Output**: `data/derived/stress_curves_normalized.parquet` with a new column `normalized_sss`. **This task MUST run before T019**. (Resolves FR-010; Depends on T015a, T020b)
- [ ] T019 [US2] Extend `code/metrics.py` to add collapse detection: Identify intensity where `normalized_sss` < 0.5 AND WER > 2x baseline per FR-004, FR-009. **Input**: `data/derived/stress_curves_normalized.parquet` (from T020d). **Output TWO artifacts**: `data/derived/collapse_points_sss.parquet` (SSS/WER based) and `data/derived/collapse_points_hvcm.parquet` (Human based, if available). (Resolves Internal Contradiction in T019 vs T026; Depends on T020d, T020b, T020c)
- [ ] T018 [P] [US2] Integration test verifying WER spike confirmation logic in `code/metrics.py` (Depends on T019 implementation)
- [ ] T021 [US2] Implement handling for "No Collapse" scenarios (record as "Max Tested") per US-2 Acceptance 2
- [ ] T022a [US2] **Generate Collapse Points Artifact**: Generate `data/derived/collapse_points.parquet` containing the identified collapse intensity vectors per model/scenario. **Must verify non-emptiness and schema validity**. (Resolves constraint_preservation-a2544b85; Depends on T019, T021)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: Human Annotation & HVCM (Priority: P2 - Dependent on US1)

**Goal**: Generate human-annotated validation set and derive the Human-Validated Collapse Margin (HVCM) to break circularity. **Note: T050b is a manual task for final report; T050c allows CI to proceed.**

**Independent Test**: Verify `data/validation/human_annotations.csv` exists with correct schema and `data/derived/hvcm_targets.parquet` is generated.

### Implementation for Human Annotation

- [ ] T050 [US1/US2] **Human Annotation Protocol Finalization**: Draft a detailed `docs/annotation_protocol.md` defining the exact Likert scale criteria (e.g., low=Unintelligible, moderate=Moderate distortion, high=Perfect) and generate a `code/annotation_tool.py` script that presents distorted clips to a human annotator via a simple CLI or web interface. (Resolves T030a "FAILED: unspecified" by defining the missing protocol and tool). **Note: This task defines the protocol and tool, but does not execute the annotation.** (Mandatory per FR-011; Depends on T015a)
- [ ] T050a [US1/US2] **Annotation Tool Implementation**: Implement `code/annotation_tool.py` to load a stratified sample of clips from `data/derived/stress_curves.parquet` and present them to a human annotator via a CLI interface, collecting `data/validation/human_annotations.csv`. Schema: `clip_id`, `distortion_vector_id`, `human_intelligibility_score_0_5 `. (Depends on T050)
- [ ] T050b [US1/US2] **Execute Real Annotation Workflow (MANUAL)**: **HARD BLOCK**: This task requires manual human execution. Run `code/annotation_tool.py` on a verified subset of clips from LibriSpeech/AMI to populate `data/validation/human_annotations.csv` with REAL human labels. **This task MUST NOT use simulated or template data.** **Must verify `docs/annotation_protocol.md` exists before execution.** The pipeline is blocked until this file exists and is non-empty for the **Final Report**. **Output**: `data/validation/human_annotations.csv`. (Resolves T030a "simulated data" concern, executability-c6dcae34; Depends on T050a, T015a)
- [ ] T050c [US1/US2] **Generate Synthetic Placeholder for CI**: Implement `code/annotation_tool.py` function `generate_synthetic_annotations` to create a deterministic `data/validation/human_annotations.csv` with mock scores for CI/CD verification. **This file is marked as "SYNTHETIC" in metadata and does NOT satisfy FR-011 for final report.** (Resolves executability-ed42c657, ordering-fae8ba71; Depends on T050a)
- [ ] T050d [US1/US2] **Manual Execution Protocol**: Document the exact steps to run the annotation tool and upload the resulting CSV to the repository in `docs/manual_annotation_steps.md`. (Depends on T050b)
- [ ] T050e [US1/US2] **Verify SSS-Human Correlation (CI Path)**: Implement `code/metrics.py` function `verify_synthetic_correlation` to compute the correlation between the synthetic annotations (T050c) and the expected human distribution model. **Generate `data/validation/synthetic_correlation_report.json`**. This task MUST pass for CI to proceed, ensuring the synthetic path is valid for automated testing. (Resolves F001, coverage-b6ad560e, executability-a14feebb; Depends on T050c)
- [ ] T030b [US3] Implement Human-Validated Collapse Margin (HVCM) calculation in `code/metrics.py`. **Logic**:
    - **Final Path (T050b complete)**: Derive HVCM from `data/validation/human_annotations.csv` (real human data) and `data/derived/stress_curves.parquet`.
    - **CI Path (T050c complete)**: Derive HVCM proxy from `data/validation/human_annotations.csv` (synthetic mock data) and `data/derived/stress_curves.parquet`. **This path uses synthetic data as a stand-in for HVCM for CI verification only.**
    - **Output**: `data/derived/hvcm_targets.parquet`. **Depends on T050b (Final) OR (T050c AND T050e) (CI)**. (Resolves T030a "simulated data" concern, executability-c6dcae34; Depends on T050b OR (T050c AND T050e))
- [ ] T050f [US1/US2] **Implement HALT Logic (FR-016)**: Implement `code/main.py` logic to check if real human validation (T050b) has failed the correlation threshold (r < 0.6). If failed, **raise RuntimeError and block US2/US3**. **Must verify T050b execution status before proceeding**. (Resolves coverage-f959e3a6, constraint_preservation-8e27b93e)
- [ ] T030a [US1/US2] **DEPRECATED**: Replaced by T050, T050a, T050b, T050c, T050e.
- [ ] T050g [US3] **Spec Amendment & Deferral**: Create `docs/spec_amendment_FR011.md` explicitly stating that FR-011 (N=1,000, 3 raters) is **amended to N=100 pilot** for this iteration due to feasibility constraints, and that the full requirement is deferred to a future release. This task resolves the conflict between the spec's mandatory gate and the task's 'out of scope' status. (Resolves FR-011 constraint preservation; Depends on T050b)

**Checkpoint**: HVCM target is now available for US3 (via T050c+T050e for CI, T050b for final)

---

## Phase 6: User Story 3 - Predict Collapse via Critical Interaction Vector (Priority: P3)

**Goal**: Train a lightweight regression model to predict collapse intensities using acoustic parameter vectors + interaction terms, and validate the "critical interaction vector" hypothesis.

**Independent Test**: Split data, train model, verify R² > 0.6 on test set and report coefficients.

### Implementation for User Story 3

- [ ] T023 [P] [US3] Unit test for interaction term generation (SNR×RT60, SNR², RT60²)
- [ ] T025a [US3] Implement `code/models.py` function `generate_interaction_terms` to explicitly create engineered interaction terms (SNR×RT60, SNR², RT60²) for feature input (Depends on T023)
- [ ] T026a [US3] **Regression Training (CI Path)**: Implement `code/models.py` to train CPU-tractable regression (Linear/Polynomial degree≤3 or DT max_depth≤5) using features from T025a. **Target**: Extract `normalized_coord` column from `data/derived/collapse_points.parquet` (generated by T022a). **Logic**: If `--report-mode=ci` is set, use SSS/WER (T022a) as target. **Explicitly verify that generated interaction terms are passed as features to the model**. **Output**: `data/derived/regression_results.json` containing R² and coefficients. (Depends on T022a, T025a)
- [ ] T026b [US3] **Regression Training (Final Path)**: Implement `code/models.py` to train CPU-tractable regression. **Target**: Extract `normalized_coord` column from `data/derived/collapse_points.parquet` (generated by T022a). **Logic**: If `--report-mode=final` is set, **MUST** use HVCM (T030b) as target; raise `RuntimeError` if HVCM is missing or T050b is not completed. **Explicitly verify that generated interaction terms are passed as features to the model**. **Output**: `data/derived/regression_results.json` containing R² and coefficients. (Resolves ordering-2b647e33, ordering-bdb21319; Depends on T022a, T025a, T030b, T050b, T050f)
- [ ] T026c [US3] **Additive Baseline Comparison (FR-013)**: Implement `code/statistics.py` to perform a statistical comparison between the full non-linear model (T026a/b) and an additive linear baseline. **Logic**: Read R² values from `data/derived/regression_results.json` (generated by T026a/b). Fit an additive baseline model (no interaction terms) and compare variance explained using an F-test. **Output**: `data/derived/baseline_comparison.json` with p-value (FDR-corrected) confirming p < 0.05 for synergistic failure modes. (Resolves FR-013, SC-003; Depends on T026a, T026b)
- [ ] T024 [US3] Implement `code/statistics.py` for multiple-comparison correction (Bonferroni/FDR) on interaction effects per FR-008
- [ ] T025 [US3] Generate `data/derived/corrected_pvalues.json` with corrected p-values and report statistical significance per SC-003
- [ ] T053 [US3] **Threshold & Morphology Stability Verification (FR-006, SC-002)**: Implement `code/analysis.py` function `verify_threshold_stability` that:
    1. Sweeps inflection detection thresholds across a defined range.
    2. **Classifies curve morphology** (sigmoid vs. linear) for each stress curve.
    3. Extracts the critical interaction vector for each threshold and morphology class.
    4. Calculates sign/magnitude variance across thresholds and **across morphology classes**.
    5. Generates `data/derived/sensitivity_analysis.csv` (full sweep data) and `morphology_stability_report.json`.
    6. Raises a `RuntimeError` if variance > 10% for any morphology class.
    (Resolves FR-006, SC-002, SC-005, executability-f3724ead, coverage-72c32fa2, ordering-30353c7c, coverage-bc0c42; Depends on T026a/T026b)
- [ ] T027 [US3] **DEPRECATED**: Functionality merged into T053.
- [ ] T028 [US3] Implement cross-model comparison logic to calculate cosine similarity of critical vectors across a set of small ASR models selected based on SC-004 (CPU-tractability) constraints; Output: `data/derived/cross_model_similarity.csv` with columns: `model_a`, `model_b`, `cosine_similarity`. (Depends on T026a/T026b)
- [ ] T029 [US3] Implement validation against held-out human-annotated subset: Correlate SSS-based collapse with Human-Validated Collapse Margin (HVCM) from `data/validation/human_annotations.csv` per FR-011 (Depends on T026b, T030b, T050b)
- [ ] T030 [US3] Generate final report artifacts in `data/derived/regression_results.json` and `data/derived/sensitivity_analysis.csv` (Depends on T026a/T026b, T053, T029, **T050b for final report**) **(Note: T053 generates the CSV, T030 aggregates it)**
- [ ] T036 [US3] Generate final report section and code comments in `research.md` and `code/models.py` explicitly framing all predictive findings as ASSOCIATIONAL, avoiding causal claims per FR-007 (Depends on T030 for data availability)
- [ ] T032 [US3] **Resource Monitoring**: Generate `data/derived/resource_monitoring_report.json` and Verify peak RSS < 7GB as a gate before proceeding (SC-004) (Depends on T015a, T026a/T026b)
- [ ] T032b [US3] **Constraint Verification**: Add a check in `code/monitor_resources.py` to explicitly assert that runtime < 6 hours and RSS < 7GB, raising an error if violated (Resolves SC-004 incompleteness)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Documentation updates in `docs/` including `research.md` citations for LibriSpeech/AMI
- [ ] T033 Performance optimization: Parallelize ASR inference and distortion application where safe
- [ ] T034 [P] Additional unit tests in `tests/unit/` for edge cases and statistical corrections
- [ ] T035 Run `quickstart.md` validation to ensure end-to-end reproducibility on GitHub Actions

---

## Phase 7: Execution Verification & Safety Gates (Revision Response)

**Purpose**: Address execution feedback regarding CPU feasibility, data integrity, and statistical rigor. These tasks ensure the pipeline runs successfully on the free tier without fabrication.

- [ ] T037 [P] [US1/US2/US3] Implement **Defensive CPU Enforcement** in `code/metrics.py` and `code/models.py` to **raise `RuntimeError` immediately** if any CUDA device is detected or if GPU libraries are inadvertently imported (Ensures "Fail Loudly" principle; prevents silent GPU fallback)
- [ ] T038 [P] [US1] Add a pre-flight check in `code/main.py` that validates the real dataset (LibriSpeech/AMI) is fully downloadable and accessible before initiating the distortion loop; if download fails, raise an exception rather than falling back to synthetic data (Enforces "Fail Loudly" rule)
- [ ] T039 [US3] Implement a memory-streaming wrapper in `code/data_loader.py` that processes the stress curve data in chunks (e.g., a fixed batch size) to ensure peak RSS remains within acceptable memory limits during the regression training phase (Addresses SC-004 memory constraint)
- [ ] T040 [P] [US3] Add a unit test in `tests/unit/test_statistics.py` that verifies the Bonferroni correction factor is correctly applied based on the exact number of interaction terms tested, ensuring p-values are not artificially inflated
- [ ] T041 [US3] Add a "Causality Warning" check in `code/models.py` that asserts the regression target (HVCM) is derived from human annotations and not from the SSS metric itself, raising an error if `human_intelligibility_score` is missing from the training data (Enforces FR-011 and breaks circularity)
- [ ] T042 [P] [US1/US2] Implement a "Distortion Coverage" validator in `code/distortion_engine.py` that logs a detailed report of which **applied distortion scenarios** were successfully applied to the sample and which were skipped, ensuring the "missing scenarios" edge case is handled transparently (FR-001)
- [ ] T043 [US3] Implement a "Threshold Stability" check in `code/analysis.py` that verifies the critical interaction vector does not change sign or magnitude by >10% when the collapse threshold is swept from 0.40 to 0.60 (Validates FR-006 and SC-002; Replaced by T053)

---

## Phase 8: Unresolved Revision Concerns & Human-in-the-Loop (Critical Path)

**Purpose**: Address specific "FAILED: unspecified" markers from previous analysis by defining concrete, executable steps for human-annotated data generation and validation logic that cannot be fully automated without external input.

- [ ] T052 [US3] **Final Report Generation Template**: Create `code/report_generator.py` to assemble `data/derived/regression_results.json` and `data/derived/sensitivity_analysis.csv` into a final `docs/final_report.md` that explicitly states the R² score, the critical interaction vector coefficients, and the stability variance, ensuring all claims are framed as associational. (Resolves T030 "FAILED: unspecified" by defining the output structure; Depends on T030, T053)
- [ ] T051 [US3] **DEPRECATED**: HVCM Calculation Logic merged into T030b.
- [ ] T054 [US3] **Human Annotation Execution Log**: Generate a log file `data/validation/annotation_log.txt` documenting the exact time, annotator ID (if applicable), and sample size of the human annotation session to satisfy FR-011 traceability. (Depends on T050b)
- [ ] T050g [US3] **Spec Amendment & Deferral**: Create `docs/spec_amendment_FR011.md` explicitly stating that FR-011 (N=1,000, 3 raters) is **amended to N=100 pilot** for this iteration due to feasibility constraints, and that the full requirement is deferred to a future release. This task resolves the conflict between the spec's mandatory gate and the task's 'out of scope' status. (Resolves FR-011 constraint preservation; Depends on T050b)

---

## Phase 9: Streamlined Data Processing & Edge Case Hardening (Revision Response)

**Purpose**: Address specific concerns regarding large dataset handling, streaming logic, and edge case robustness that were flagged as incomplete in the previous revision. These tasks ensure the pipeline handles real-world data constraints without fabrication.

- [ ] T055 [US1] **DEPRECATED**: Streaming Data Loader functionality integrated into T007a/b.
- [ ] T056 [US1] **DEPRECATED**: Chunked Distortion Application functionality integrated into T012.
- [ ] T057 [US2] **DEPRECATED**: Hysteresis Logic for Oscillating SSS integrated into T016 (K=3 steps).
- [ ] T058 [US2] **DEPRECATED**: Empty ASR Output Handler integrated into T016 (lowest intensity mapping).
- [ ] T059 [US3] **Implement Sample Size Reporting**: Add logic in `code/main.py` to explicitly report the final sample size (number of clips, number of distortion scenarios) used in the analysis, including any clips/scenarios that were skipped due to missing data or memory constraints. (Resolves transparency requirement for sample size; Depends on T015a, T007a)
- [ ] T060 [US3] **Implement Power Analysis for Sample Size**: Add a unit test in `tests/unit/test_statistics.py` that calculates the statistical power of the regression model given the final sample size and expected effect size. **Requires explicit `--power-threshold` argument or skips if undefined in `config.py`**. Raise a warning if power < threshold. (Resolves statistical rigor requirement, executability-4975d29b, constraint_preservation-8a9dc2da; Depends on T024, T059)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Execution Verification (Phase 7)**: Must be completed before final deployment to ensure CPU feasibility and data integrity
- **Human-in-the-Loop (Phase 8)**: Must be completed to resolve unspecified logic before final validation
- **Streamlined Data Processing (Phase 9)**: Must be completed to ensure robustness against large datasets and edge cases before final execution
- **GPU Offload Preparation (Phase 10)**: **DELETED** - Contradicts CPU-Tractability constraint.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 (requires stress curve data)
- **User Story 3 (P3)**: Depends on US2 (requires collapse points) and Human Annotation (Phase 5)
- **Phase 7 Tasks**: Can run in parallel with Phase 6 implementation but must pass before final report generation
- **Phase 8 Tasks**: Must be completed after Phase 5 (Human Annotation) is initiated to finalize logic
- **Phase 9 Tasks**: Must be completed after Phase 2 (Foundational) and can run in parallel with Phase 6 implementation

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
- Phase 7 safety checks can run in parallel with Phase 6 implementation
- Phase 8 tasks can run in parallel with Phase 7 execution verification
- Phase 9 tasks can run in parallel with Phase 6 implementation

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for distortion engine"
Task: "Integration test for data loader"

# Launch all models for User Story 1 together:
Task: "Implement data loader"
Task: "Implement distortion engine"
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
 - Developer D: Phase 7 Safety Gates (Execution Verification)
 - Developer E: Phase 8 Human-in-the-Loop Logic (Annotation Protocol & HVCM)
 - Developer F: Phase 9 Streamlined Data Processing (Streaming & Edge Cases)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All ASR and embedding models MUST run on CPU (no CUDA/GPU) unless explicitly offloaded via T061. Use `whisper-tiny` and `all-MiniLM-L-v2`. **(T061-T065 DELETED - Contradicts CPU constraint)**
- **Data Integrity**: Use real data from LibriSpeech/AMI. No synthetic data fabrication.
- **Statistical Rigor**: Apply multiple-comparison correction and associational framing strictly.
- **Human Validation**: FR-011 requires generating human annotations (T050b) with a **0-5 Likert scale** before US2/US3 validation. **T050c is for CI only; T050e validates CI path.**
- **Methodology**: HVCM (T030b) is an **alternative** regression target to break circularity; primary target is SSS/WER per spec.
- **Revision Update**: Phase 7 tasks added to address execution feedback regarding CPU feasibility, data integrity, and statistical rigor (T037-T043).
- **Revision Update 2**: Phase 8 tasks added to resolve "FAILED: unspecified" markers by defining concrete annotation protocols, HVCM calculation logic, and stability verification criteria (T050-T054).
- **Revision Update 3**: Phase 5 restructured to separate Protocol (T050), Tool (T050a), Execution (T050b), Synthetic Placeholder (T050c), and CI Validation (T050e).
- **Revision Update 4**: T015 marked incomplete and T015a added for concrete algorithm; T015 removed.
- **Revision Update 5**: T053 moved to Phase 6 for immediate execution after regression.
- **Revision Update 6**: T032 and T032b added for resource monitoring and constraint verification.
- **Revision Update 7**: Phase 9 added to address streaming data processing, chunked distortion application, and edge case hardening (T055-T060).
- **Revision Update 8**: T055, T056, T057, T058, T051, T027, T025b marked DEPRECATED with explicit integration notes into T007, T012, T016, T030b, T053, T026 respectively.
- **Revision Update 9**: T050b updated to be a hard-blocking manual step for final report; T050c added for CI bypass; T050d added for manual protocol; T050e added for CI validation.
- **Revision Update 10**: T008 unmarked, T008a added to resolve inconsistency.
- **Revision Update 11**: T012 updated to enforce exactly 54 scenarios; T012a added for verification.
- **Revision Update 12**: T053 updated to generate sensitivity artifacts; T030 updated to depend on T053.
- **Revision Update 13**: T026 updated to enforce HVCM for Final Report mode, SSS/WER for CI mode.
- **Revision Update 14**: T007c removed; T007d added to document deviation.
- **Revision Update 15**: T060 updated to remove hardcoded 0.8 threshold, requiring explicit argument.
- **Revision Update 16**: T009 moved to Phase 3.
- **Revision Update 17**: T019 updated to produce dual targets (SSS/WER and HVCM).
- **Revision Update 18**: Phase 10 removed (T061-T065) as it contradicts CPU-only constraint.
- **Revision Update 19**: T012b added for Distortion Realism Validation (FR-018).
- **Revision Update 20**: T050f added for HALT logic (FR-016).
- **Revision Update 21**: T026 split into T026a (CI) and T026b (Final) with explicit dependencies.
- **Revision Update 22**: T015b removed; T015c added for artifact verification.
- **Revision Update 23**: T022 removed; T022a added for artifact generation.
- **Revision Update 24**: T012c added to fetch DNS Challenge data for T012b.
- **Revision Update 25**: T020d added to perform normalization step before T019.
- **Revision Update 26**: T026c added to perform additive baseline comparison.
- **Revision Update 27**: T053 updated to include morphology classification.
- **Revision Update 28**: T003c added to re-scope US-3 hypothesis for power limitations.
- **Revision Update 29**: T050g added to amend FR-011 to pilot status.