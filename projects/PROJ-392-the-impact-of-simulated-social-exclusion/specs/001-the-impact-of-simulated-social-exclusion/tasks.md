# Tasks: The Impact of Simulated Social Exclusion on Neural Responses to Reward

**Input**: Design documents from `/specs/001-social-exclusion-reward-neural/`
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

## Phase 0: Feasibility Check & Design Verification (CRITICAL)

**Purpose**: Verify data availability and statistical design before proceeding. This phase resolves the "Feasibility Pivot" mandated by the plan.

- [ ] T008 [P] [US0] **Design Verification**: Inspect BIDS task files (`participants.tsv`, `task-*.tsv`) to determine if the design is **within-subject** (each participant does both exclusion and inclusion) or **between-subject**. Output: `data/design_type.json` (value: "within" or "between").
- [ ] T009 [P] [US0] **Feasibility Check**: Download `ds000246` (or specified dataset) header only. Verify if it contains BOTH social exclusion AND reward tasks. Output: `data/feasibility_status.json` (value: "combined" or "missing_reward").
- [ ] T010 [P] [US0] **Synthetic Data Generation (Feasibility Pivot)**: **IF** T009 reports "missing_reward", implement `code/synthetic_data.py` to generate **deterministic synthetic reward task data** (simulated BOLD responses with known beta differences) that mimics the statistical properties required for downstream analysis. Output: `data/synthetic/reward_task.nii.gz` and `data/synthetic/behavioral.csv`. **Verification**: Ensure synthetic data produces expected beta differences (e.g., exclusion < inclusion) to validate the pivot.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure at **repository root**: `code/`, `data/raw-fmri/`, `data/processed-fmri/`, `data/behavioral/`, `data/synthetic/`, `data/extracted/`, `tests/`, `docs/`, `docs/paper/`, `docs/paper/figures/`.
- [ ] T002 [P] Initialize Python 3.11 project with `code/requirements.txt`. **Content must include**: `nilearn>=0.10`, `nibabel`, `scikit-learn`, `pandas`, `openneuro-py`, `matplotlib`, `seaborn`, `scipy`, `numpy`, `pytest`.
- [ ] T003 [P] [US1] Configure linting (ruff/flake8) and formatting (black) tools.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Setup BIDS-compliant directory structure (`data/raw-fmri/`, `data/processed-fmri/`, `data/behavioral/`, `data/synthetic/`).
- [ ] T005 [P] [US1] Implement memory monitoring and chunked processing utility in `code/utils.py` (monitor RAM, trigger downsampling to 4mm if >6GB). **Verification**: Run a script that triggers the 6GB threshold and logs a warning.
- [ ] T006 [P] Create base data models/entities in `code/models.py`: `Participant` (attrs: id, group, betas), `ROI` (attrs: name, atlas, coords), `AnalysisResult` (attrs: roi, event, t, p, d).
- [ ] T007 [P] Setup logging infrastructure to record preprocessing success/failure rates for SC-004.
- [ ] T008 [P] Configure environment variables for OpenNeuro API keys and dataset IDs.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download and preprocess fMRI data from OpenNeuro (ds000246) using CPU-tractable methods, or use synthetic data if T010 was triggered.

**Independent Test**: Can be fully tested by downloading ds000246 (or using synthetic data), running the Preprocessing Module on CPU, and verifying output BOLD images and first-level GLM estimates are generated without GPU resources.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T009 [P] [US1] Contract test for dataset download in `tests/contract/test_download.py` (verify BIDS structure).
- [ ] T010 [P] [US1] Integration test for preprocessing pipeline on a single subject in `tests/integration/test_preprocess.py` (verify <7GB RAM usage).

### Implementation for User Story 1

- [ ] T011 [US1] Implement `code/download.py` to fetch ds000246 via `openneuro-py` and verify checksums. Output: `data/raw-fmri/`.
- [ ] T016 [US1] **Gating Step**: Check if reward task runs exist in downloaded data. **IF** no reward runs exist (and T010 not run), halt with error: 'Error: Missing condition labels. Dataset must contain a "condition" column...'. **IF** T010 was triggered, proceed with synthetic data.
- [ ] T012 [US1] Implement `code/preprocess.py` with slice-timing correction and realignment (Nilearn/AFNI CPU mode). **Output**: `data/processed-fmri/sub-*/func/sub-*_slice_realigned.nii.gz`.
- [ ] T013 [US1] Implement normalization to MNI space in `code/preprocess.py` (resample to 4mm if memory >6GB). **Verification**: Verify output file exists in `data/processed-fmri/` with MNI header.
- [ ] T014 [US1] Implement smoothing at mm FWHM in `code/preprocess.py` (with hooks for 4mm/8mm sensitivity).
- [ ] T015 [US1] Implement chunked batch processing in `code/preprocess.py` to handle N=40 within 4 hours.
- [ ] T017 [US1] Add error handling for missing condition labels (halt with specific error message).
- [ ] T018 [US1] Log preprocessing completion rate (Success/Total) to `data/logs/preprocess_status.json`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - ROI-Based Statistical Analysis (Priority: P1)

**Goal**: Extract beta estimates from ROIs and perform second-level mixed-effects analysis. **Depends on Phase 3 completion.**

**Independent Test**: Can be fully tested by running the ROI extraction and t-test on preprocessed data from ≥10 participants per group, producing statistically valid group-level effect estimates.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for ROI mask generation (AAL/Harvard-Oxford) in `tests/unit/test_roi.py`.
- [ ] T020 [P] [US2] Contract test for statistical output schema (t-stat, p-value, Cohen's d) in `tests/contract/test_stats.py`.

### Implementation for User Story 2

- [ ] T021 [US2] Implement ROI definition in `code/roi_extraction.py`: Ventral Striatum (AAL, MNI: +/, 8, -4) and OFC (Harvard-Oxford, Prob>50%). **Output**: Mask files in `data/extracted/`.
- [ ] T022 [US2] Implement beta extraction for 'Reward > Neutral' and 'Anticipation > Baseline' contrasts. **Output**: `data/extracted/roi_betas.csv` (participant_id, group, roi, event_type, beta_value).
- [ ] T023 [US2] Store extracted betas in `data/extracted/roi_betas.csv`.
- [ ] T024 [US2] Implement behavioral manipulation check in `code/analysis.py` (extract distress scores from `data/behavioral/`). **Output**: `data/behavioral/distress_scores.csv`. **Logic**: if mean_distress < threshold: flag 'proxy variable'.
- [ ] T025 [US2] Implement logic to flag 'proxy variable' if behavioral data is missing (FR-011).
- [ ] T026 [US2] Implement second-level statistical model in `code/analysis.py`: **SELECT** model based on T008 output (within-subject: paired t-test/interaction; between-subject: two-sample t-test). Compare ROI activation between excluded vs. included groups.
- [ ] T027 [US2] Implement Small Volume Correction (SVC) for FWE correction (p<0.05) in `code/analysis.py`.
- [ ] T028 [US2] Calculate Cohen's d and 95% CI for all ROI/event combinations.
- [ ] T029 [US2] Implement multiple-comparison correction for the set of statistical tests (2 ROIs × 2 events) with explicit method naming.
- [ ] T030 [US2] Implement power check: **IF** n<10 per group, output exact string: 'WARNING: Power limitation detected (n<20). Results framed as exploratory.' and trigger 'exploratory' framing in report.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Result Visualization and Reporting (Priority: P2)

**Goal**: Generate interpretable visualizations and a summary report with associational framing. **Depends on Phase 4 completion.**

**Independent Test**: Can be fully tested by generating figures from completed analysis outputs and verifying they display group differences with appropriate statistical annotations.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031 [P] [US3] Visual regression test for bar plot generation in `tests/unit/test_viz.py`.
- [ ] T032 [P] [US3] Contract test for report framing (scan for causal verbs) in `tests/contract/test_report_framing.py`.

### Implementation for User Story 3

- [ ] T033 [US3] Implement bar plot generation (mean ± SEM) with p-value annotations in `code/viz.py`. **Output**: `docs/paper/figures/bar_plot_vs.png`. **Format**: p<0.05, **p<0.01.
- [ ] T034 [US3] Implement SPM overlay generation on MNI template in `code/viz.py` (cluster coords + peak t-values).
- [ ] T035 [US3] Implement summary report compilation in `docs/paper/report.md` (sample size, means, stats, interpretation).
- [ ] T036 [US3] Implement framing accuracy check: scan report for causal verbs and replace with associational language (FR-009).
- [ ] T037 [US3] Add future recommendations section (FR-010) suggesting ≥30 participants per group.
- [ ] T038 [US3] Save all figures to `docs/paper/figures/` with descriptive filenames.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Sensitivity Analysis for Threshold Justification (Priority: P3)

**Goal**: Perform sensitivity analysis sweeping smoothing and ROI radius thresholds. **Depends on Phase 5 completion.**

**Independent Test**: Can be fully tested by re-running analysis with alternative thresholds and comparing resulting activation maps.

### Tests for User Story 4 (OPTIONAL - only if tests requested) ⚠️

- [ ] T039 [P] [US4] Unit test for consistency calculation logic in `tests/unit/test_sensitivity.py`.

### Implementation for User Story 4

- [ ] T040 [US4] Implement sensitivity loop in `code/analysis.py` (smoothing ∈ {mm, 6mm, 8mm}, ROI radius ∈ {mm, 10mm, 12mm}). **Output**: `data/extracted/sensitivity_table.csv`.
- [ ] T041 [US4] Generate table of mean beta values and p-values for all threshold combinations.
- [ ] T042 [US4] Implement consistency logic: check if **beta difference sign** (Group A - Group B) and significance (p<0.05) are preserved in ≥6/9 cases.
- [ ] T043 [US4] Append sensitivity results and consistency rate to `docs/paper/report.md`.

**Checkpoint**: Sensitivity analysis complete; robustness verified.