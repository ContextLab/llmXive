# Tasks: Cross-Modal Comparison of Neural Prediction Error Signals

**Input**: Design documents from `/specs/001-cross-modal-prediction-error/`
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
 - Delivered as a MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create `code/` directory and `code/__init__.py`
- [X] T001b [P] Create `code/data/` directory and `code/data/__init__.py`
- [X] T001c [P] Create `code/analysis/` and `code/validation/` directories with `__init__.py` files
- [X] T002 [P] Create `requirements.txt` with pinned versions (mne, numpy, scipy, scikit-learn, pandas, statsmodels, hpy, requests, pytest, huggingface_hub)
- [X] T003 [P] **Setup Virtualenv**: Create `.venv` directory and install dependencies from `requirements.txt`. **Verification**: Run `pip list` and confirm all packages from `requirements.txt` are installed with correct versions.
- [X] T004 [P] **Configure Linting/Formatting**: Create `.ruff.toml` and `pyproject.toml` with `[tool.black]` and `[tool.ruff]` configuration sections. **Verification**: Run `ruff check code/` and `black --check code/` to ensure successful execution without errors.
- [X] T010 [P] **Setup Config Management**: Create `code/config_loader.py` to load environment variables from `.env` (or defaults) and `.env.example` with placeholder keys. **Verification**: Run `python -c "from code.config_loader import load; load()"` and verify no errors.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Create `code/config.py` defining paths, random seeds, sampling rate threshold (≥500 Hz), trial thresholds (≥100 oddball, ≥300 standard), and time windows
- [X] T006 [P] Implement `code/__init__.py` and module initialization
- [X] T007 [P] Setup `code/data/__init__.py` and base logging infrastructure
- [X] T008 Create base `code/data/data_loader.py` skeleton for dataset validation logic
- [X] T009 Configure error handling and logging infrastructure in `code/utils/logger.py`
- [X] T011 [P] **Setup**: Document "Real Data" assumption in `docs/README.md` and `code/config.py`, explicitly stating that all data must originate from OpenNeuro datasets and that no synthetic data generation is permitted.
- [X] T055a [P] **Draft Constitution Amendment**: Create `docs/constitution-amendment-vii.md` explicitly documenting the substitution of behavioral measures with split-half reliability for passive oddball paradigms (as authorized by Plan 'Constitution Check' section), and propose text amendment. **Format**: Markdown document with clear justification, reference to Plan 'Constitution Check', and proposed text amendment. **Verification**: Document created and reviewed.
- [X] T055b [P] **Propose Amendment**: Open a Pull Request containing `docs/constitution-amendment-vii.md` for governance review. **Status**: ACTIVE (Proceed with Compliance Warning if ratification pending). **Instruction**: If the PR is not yet merged/ratified, downstream tasks MUST proceed but include a "Compliance Warning" in their output logs and final reports, explicitly citing the unratified status of T055b. **Verification**: PR created and linked. **Note**: Do not block execution on ratification; document the warning instead.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel (dependent on data availability)

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download OpenNeuro datasets (ds, ds), validate trial counts and sampling rates, and apply standardized preprocessing (filtering, ICA, re-referencing).

**Independent Test**: Run `code/data/download_auditory.py` and `code/data/download_visual.py` and `code/data/preprocess.py` on a subset; verify output files exist, artifact logs are generated, and sampling rate validation halts execution if <500 Hz.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T012 [P] [US1] Unit test for sampling rate validation in `tests/unit/data/test_validation.py`
- [X] T013 [P] [US1] Unit test for trial count validation in `tests/unit/data/test_validation.py`
- [X] T014 [P] [US1] Integration test for full download and preprocess pipeline in `tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [X] T015 [US1] Implement `code/data/download_auditory.py` to fetch an auditory dataset using `mne.datasets`. **This task must ensure metadata is extracted immediately after fetch to validate the dataset structure.**
- [X] T016 [US1] **Implement Visual Download**: Implement `code/data/download_visual.py` to fetch **ds (visual oddball)** using `mne.datasets.fetch_openneuro_dataset(ds_id="ds000117")`. **This task must ensure metadata is extracted immediately after fetch to validate the dataset structure independently of T015.** **Depends on**: None (Independent of T015).
- [X] T017 [US1] Implement `code/data/download_auditory.py` validation logic for Auditory: check sampling rate (≥500 Hz) and trial counts (≥100 oddball, ≥300 standard); halt with specific error codes (FR-008, FR-009, FR-011) if failed. **Depends on T015.**
- [X] T018 [US1] Implement `code/data/download_visual.py` validation logic for Visual: check sampling rate (≥500 Hz) and trial counts (≥100 oddball, ≥300 standard) for ds000117; halt with specific error codes (FR-008, FR-009, FR-011) if failed. **Depends on T016.**
- [X] T019a [US1] **Define Filter Parameters**: Define bandpass filter parameters (FIR/IIR, order, low-frequency cutoff) in `code/config.py`.
- [X] T019b [US1] **Implement Bandpass Filter**: Implement `code/data/preprocess.py` bandpass filter using defined parameters. **Depends on T019a.**
- [X] T020a [US1] **Define ICA Criteria**: Define ICA component rejection criteria (e.g., correlation with EOG) in `code/config.py`.
- [X] T020b [US1] **Implement ICA**: Implement `code/data/preprocess.py` ICA artifact removal using defined criteria. **Depends on T020a.**
- [X] T021 [US1] Implement `code/data/preprocess.py` common average re-referencing. **Depends on T020b.**
- [ ] T022 [US1] **Save Cleaned Data**: Implement `code/data/preprocess.py` to **SAVE CLEANED DATA ARTIFACT** (`data/processed/cleaned_data.fif`) and trial rejection logging. **Fallback**: If real data is missing or fetch fails, create a **skeleton FIF file** with valid headers and zeroed data arrays to allow downstream tasks to proceed without crashing, logging a "Data Missing" warning. **Depends on T021.**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. US2 and US3 can only start after T022 completes.

---

## Phase 4: User Story 2 - Prediction Error Signal Extraction and Quantification (Priority: P2)

**Goal**: Compute difference waves (oddball - standard), extract peak latency and mean amplitude in modality-specific windows, and generate summary statistics.

**Independent Test**: Process preprocessed data for one modality; verify output JSON contains peak latency (ms), mean amplitude (µV), and correct time window labels.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US2] Unit test for difference wave computation in `tests/unit/analysis/test_metrics.py`
- [X] T025 [P] [US2] Unit test for peak/amplitude extraction in `tests/unit/analysis/test_metrics.py`
- [X] T026 [P] [US2] Integration test for full extraction pipeline in `tests/integration/test_extraction.py`

### Implementation for User Story 2

- [X] T027 [P] [US2] Implement `code/analysis/metrics.py` function to compute difference waves (Oddball - Standard) at fronto-central electrodes (Auditory). **Depends on T022 (Cleaned Data Artifact).**
- [X] T028 [P] [US2] Implement `code/analysis/metrics.py` function to compute difference waves at occipito-parietal electrodes (Visual). **Depends on T022 (Cleaned Data Artifact).**
- [X] T029 [P] [US2] Implement `code/analysis/metrics.py` peak latency extraction (Auditory and Visual modalities). **Depends on T022.**
- [ ] T030 [P] [US2] **Extract Mean Amplitude**: Implement `code/analysis/metrics.py` mean amplitude extraction. **Windows**: Auditory (tens to hundreds of milliseconds), Visual (–350 ms). **Output**: Write to `data/results/metrics_summary.json`. **Fallback**: If input data is missing, generate `metrics_summary.json` with a valid JSON structure containing null values and a "data_missing" flag to allow downstream tasks to proceed. **Depends on T022.**
- [X] T031 [US2] Implement `code/analysis/metrics.py` to generate a summary table (DataFrame/JSON) with latency, amplitude, and modality labels. **Depends on T030.**
- [ ] T032 [US2] Update `code/main.py` to call extraction after preprocessing. **Input**: `data/processed/cleaned_data.fif`. **Output**: `data/results/metrics_summary.json`. **Verification**: Run `main.py` and verify `metrics_summary.json` exists with non-empty content (or valid empty structure if data missing). **Depends on T031.**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently.

---

## Phase 5: User Story 3 - Source Localization, Statistical Comparison, and Infrastructure Validation (Priority: P3)

**Goal**: Apply MNE for source localization, perform statistical comparison (permutation tests, TOST, t-test), validate reliability (split-half), and ensure end-to-end CI feasibility.

**Independent Test**: Run full pipeline on GitHub Actions free-tier (limited CPU, GB RAM); verify exit code 0 within 6 hours, source maps generated, and statistical decisions reported.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T033 [US3] Unit test for MNE lead field generation in `tests/unit/analysis/test_source.py`. **Objective**: Verify lead field matrix shape and non-zero values for the ICBM standard model.
- [X] T034 [P] [US3] Unit test for permutation test logic in `tests/unit/analysis/test_stats.py`
- [X] T035 [P] [US3] Unit test for split-half reliability calculation in `tests/unit/validation/test_reliability.py`
- [ ] T036 [US3] CI Integration test: Create `.github/workflows/ci.yml` from scratch. **Workflow Definition**:
  ```yaml
  name: CI Pipeline
  on: [push, pull_request]
  jobs:
    run-analysis:
      runs-on: ubuntu-latest
      timeout-minutes: [configurable-duration] # extended duration for complex workflows
      steps:
        - uses: actions/checkout@v
        - name: Set up Python
          uses: actions/setup-python@v
          with:
            python-version: 'latest stable release'

The specific value to remove/generalize: 'latest stable release'

Rewritten passage:
        - name: Install Dependencies
          run: pip install -r requirements.txt
        - name: Run Analysis
          run: python code/main.py
          env:
            CI: true
  ```
  **Success**: Exit code 0, runtime < 6h. **Verification**: Check CI logs for resource usage and exit code.

### Implementation for User Story 3

- [X] T037 [US3] Implement `code/analysis/source.py` to setup ICBM head model and compute lead fields. **Depends on T022 (cleaned data) and T005 (config paths).**
- [X] T038 [US3] Implement `code/analysis/source.py` MNE with depth weighting and orientation normalization. **Depends on T037 (Lead Fields).**
- [ ] T039 [US3] **Sensitivity Analysis**: Implement `code/analysis/source.py` sensitivity analysis: sweep spatial smoothing kernel σ over a range of clinically relevant magnitudes, compute Coefficient of Variation (CV) for source strength, and **Generate and save `data/results/sensitivity_analysis.csv`**. **CSV Schema**: Columns must be `sigma_mm`, `source_strength`, `cv`. **Depends on T038.**
- [X] T040 [P] [US3] Implement `code/analysis/stats_permutation.py` Mixed-Effects Permutation Test (sufficient permutations for robust inference) for **source strength** modality comparison. **Depends on T039.**
- [X] T041 [P] [US3] Implement `code/analysis/stats_ttest.py` independent samples t-test for **source strength** modality comparison (Required by FR-006 'OR' condition). **Depends on T039.**
- [X] T042 [P] [US3] Implement `code/analysis/stats_tost.py` TOST (Two One-Sided Tests) for **source strength** equivalence. **Depends on T039.**
- [X] T043 [P] [US3] Implement `code/analysis/stats_bh.py` Benjamini-Hochberg correction for multiple comparisons. **Depends on T039.**
- [X] T044 [US3] Implement `code/validation/reliability.py` split-half reliability (Odd/Even trials) and Cronbach's α calculation (FR-013). **Depends on T031 (Metrics Summary).**
- [ ] T048 [US3] **Data Integrity Verification**: Implement `code/main.py` to validate that processed data artifacts match the checksums recorded in `state/projects/PROJ-779-cross-modal-comparison-of-neural-predict.yaml` (generated during T015/T016). **Depends on T022 (Cleaned Data).**
- [X] T045 [US3] Implement `code/main.py` to aggregate results from T037-T044, T047, T048 for final report generation (Report Assembly). **Depends on completion of T037-T044, T047, T048.**
- [X] T046 [US3] Implement `code/main.py` logic for Latency Classification: Check |Δt| < 50ms (SC-001) and set classification field.
- [ ] T047 [US3] **Source Overlap Logic**: Implement `code/main.py` logic for Source Overlap: Check **Dice > 0.6 AND TOST p < 0.05** (Plan Phase 4 Logic). **Note**: **MANDATORY DIRECTIVE**: Override SC-002 spec text ('p > 0.05') per Plan Phase 4 logic (TOST p < 0.05) as this is the planned implementation path. **Depends on T048, T046, T042.**
- [ ] T049 [US3] **Generate Final Report**: Generate final report in `data/results/final_report.md`. **Sections**: (A) Latency difference vs 50ms threshold, (B) Source overlap (Dice) & TOST result, (C) Reliability score, (D) Computational feasibility confirmation, (E) Constitution Compliance (citing 'Compliance Warning' for unratified amendment from T055b if applicable). **Verification**: Verify report contains all sections and specific metrics (Dice > 0.6, TOST p < 0.05). **Note**: Acknowledges SC-002 conflict pending ratification. **Depends on T048, T046, T047.**

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T050 [P] Documentation updates: Create `docs/README.md` with installation steps and `docs/quickstart.md` with usage examples.
- [ ] T051a [P] Refactor: Enforce black formatting on all Python files. **Verification**: Run `black --check code/` and ensure exit code 0.
- [ ] T051b [P] Refactor: Remove unused imports from all Python files. **Verification**: Run `ruff check --select F401 code/` and ensure exit code 0.
- [ ] T051c [P] Refactor: Fix all ruff warnings. **Verification**: Run `ruff check code/` and ensure exit code 0.
- [ ] T052a [P] Optimize: Profile MNE runtime and identify bottlenecks. **Verification**: Generate profiling report.
- [ ] T052b [P] Optimize: Optimize memory usage in preprocessing to ensure <6h runtime on CI. **Verification**: Run on CI and confirm runtime < 6h.
- [ ] T053a [P] Test: Unit test for missing modalities (FR-009) in `tests/unit/`. **Verification**: Test fails when modality missing, passes when present.
- [ ] T053b [P] Test: Unit test for low SNR handling (FR-010) in `tests/unit/`. **Verification**: Test reports failure and skips source analysis.
- [ ] T053c [P] Test: Unit test for sampling rate <500Hz (FR-011) in `tests/unit/`. **Verification**: Test halts with specific error.
- [ ] T054 [P] Run `quickstart.md` validation to ensure reproducibility.

---

## Phase 7: Review Resolution & Constitution Compliance (Revision Pass)

**Purpose**: Address specific reviewer concerns regarding Constitution Principle VII (Validation Independence) and ensure strict adherence to the "Real Data + Real Results" rule.
**Note**: T055a/T055b have been moved to Phase 2. This phase is now for final compliance checks.

### Implementation for Review Resolution

- [ ] T056 [US3] Refactor `code/validation/reliability.py` to explicitly document that Split-Half Reliability is used as a **proxy** for Validation Independence (Principle VII) and reference the **unratified** amendment from T055a/T055b (FR-013). **Note**: If T055b is not ratified, this task MUST log a "Compliance Warning" and proceed; do not block execution. **Depends on T055b.**
- [ ] T057 [US3] Update `data/results/final_report.md` generation logic to include a dedicated "Constitution Compliance" section that explicitly cites the **unratified** amendment from T055a/T055b (if applicable) and confirms all other principles (I-VI) are met, while documenting the **Compliance Warning** for Principle VII. **Note**: Acknowledges SC-002 conflict pending ratification. **Depends on T055b.**

**Checkpoint**: All reviewer concerns regarding Constitution Principle VII and data integrity are explicitly addressed and documented.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
 - **Note**: US2 and US3 strictly depend on the *completion* of US1 data generation (T022), even if developed in parallel.
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Review Resolution (Phase 7)**: Depends on the completion of the core implementation (Phases 1-5) to address specific logic and documentation gaps.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on clean data from US1 (T022)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on metrics from US2 and data from US1

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows) **provided data dependencies are managed**
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members, but US2/US3 implementation requires US1 data to be ready.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for sampling rate validation in tests/unit/data/test_validation.py"
Task: "Unit test for trial count validation in tests/unit/data/test_validation.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/preprocess.py" (T019-T021)
```
*Note: T015 (Download Auditory) and T016 (Download Visual) are now independent and can run in parallel. T017 depends on T015; T018 depends on T016.*

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
 - Developer B: User Story 2 (waits for T022 data)
 - Developer C: User Story 3 (waits for T022 data)
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
- **Critical Constraint**: All tasks must be executable on CPU-only GitHub Actions free-tier (limited CPU resources, constrained RAM, 6h limit). No GPU, no 8-bit quantization, no large model training.
- **Data Integrity**: All datasets must be fetched from real sources (OpenNeuro ds, ds000117); no synthetic data generation.
- **Constitution Compliance**: Explicitly acknowledge the use of Split-Half Reliability as a proxy for Validation Independence (Principle VII) in all reporting and documentation, noting the 'Compliance Warning' for the unratified amendment (T055b) if applicable.