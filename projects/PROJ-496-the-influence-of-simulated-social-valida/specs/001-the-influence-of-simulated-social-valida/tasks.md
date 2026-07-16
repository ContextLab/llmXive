# Tasks: The Influence of Simulated Social Validation on Neural Responses to Novel Information

**Input**: Design documents from `/specs/main-feature-sim-social-validation/`
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

- [ ] T001a [P] Create `projects/PROJ-496-the-influence-of-simulated-social-valida/code/` directory structure
- [ ] T001b [P] Create `projects/PROJ-496-the-influence-of-simulated-social-valida/data/` directory structure
- [ ] T001c [P] Create `projects/PROJ-496-the-influence-of-simulated-social-valida/tests/` directory structure
- [ ] T001d [P] Create `projects/PROJ-496-the-influence-of-simulated-social-valida/docs/` directory structure
- [X] T002a [P] Create `requirements.txt` with pinned versions for `mne`, `statsmodels`, `pandas`, `numpy`, `scikit-learn`, `openneuro-py`, `requests`, `pyyaml`, `matplotlib`, `seaborn`, `reportlab`, `pingouin`
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools in `.github/workflows/lint.yml`
- [ ] T007 [P] Create base data schemas in `specs/main-feature-sim-social-validation/contracts/` (`eeg_dataset.schema.yaml`, `p300_measure.schema.yaml`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Setup `data/raw`, `data/processed`, `data/results` directory structure with `.gitkeep`
- [X] T005 [P] Implement `code/config.py` for path management and environment variables
- [X] T006 [P] Setup `code/__init__.py` and logging infrastructure in `code/logger.py`
- [X] T008 [P] Implement `code/main.py` entry point with argument parsing and phase routing logic
- [X] T0046 [P] **Constitution Compliance**: Implement random seed pinning in `code/config.py` (set `RANDOM_SEED=42`) and propagate to `numpy`, `random`, and any ML libraries in `code/main.py` before any data loading or model fitting. This satisfies Constitution Principle I (Reproducibility).
- [X] T009a [P] Create `tests/test_search.py` with function `test_categorizes_eligible_dataset`
- [X] T009b [P] Create `tests/test_preprocess.py` with function `test_filtering_and_ica`
- [X] T009c [P] Create `tests/test_analyze.py` with function `test_lmm_convergence`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Discovery & Eligibility Check (Priority: P1) 🎯 MVP

**Goal**: Identify a single dataset containing both social feedback manipulation and social anxiety measures. If none found, explicitly identify separate 'Simulated-Only' and 'Real-Only' datasets for documentation, then trigger the Plan's abort logic (Negative Finding) as the valid completion state.

**Independent Test**: Run `code/search.py` against OpenNeuro/PhysioNet; verify it outputs a CSV of candidates, correctly categorizes them, and triggers the appropriate exit code and report generation.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for dataset categorization logic in `tests/test_search.py`
- [X] T011 [P] [US1] Integration test for OpenNeuro API query in `tests/test_search.py`

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/search.py` to query OpenNeuro/PhysioNet with keywords: "social", "feedback", "validation", "anxiety"
- [X] T013 [US1] Implement metadata parsing in `code/search.py` to detect `feedback_type` (simulated vs real) and `anxiety_measure` (e.g., LSAS, SPIN)
- [ ] T014 [US1] Implement logic to categorize datasets: "Eligible" (both present), "Sim-Only", "Real-Only", "Partial-EEG", "Partial-Anxiety", or "None". Output lists for each category in memory.
- [X] T016a [US1] Generate `data/results/dataset_search_results.csv` with columns: `dataset_id`, `title`, `feedback_type`, `anxiety_measure`, `status`, `url`
- [ ] T015 [US1] [Plan Override] Implement conditional routing: If "Eligible" found, proceed; ELSE, log "Sim-Only" and "Real-Only" candidates. **Output**: Generate `data/results/negative_finding_report_v1.pdf` (see T016b/T016c) and exit with code 0 (Project Complete: Negative Finding). **Spec Kickback Required**: This overrides Spec US-1 Acceptance Scenario 2 (Separate Datasets = Success) in favor of Plan's Abort strategy. Dependencies: T014, T016a. Action: BYPASS PHASES 4 & 5. TERMINATE PIPELINE.
- [ ] T016b [US1] Generate "Negative Finding Report" (PDF/HTML) for the "No Eligible Datasets Found" scenario. **Trigger Condition**: Execute ONLY IF T015 detects "None" status. **Content**: Summary of search, list of "None" status datasets, and statement of data gap. Dependencies: T015 (if triggered by "None").
- [ ] T016c [US1] Generate "Negative Finding Report" (PDF/HTML) for the "Separate Datasets Found" scenario. **Trigger Condition**: Execute ONLY IF T015 detects "Sim-Only" or "Real-Only" status. **Content Requirement**: Must explicitly list the identified "Sim-Only" and "Real-Only" dataset IDs, titles, and URLs as evidence of the specific scenario, distinguishing it from the "No Datasets" case. Dependencies: T015 (if triggered by "Sim-Only"/"Real-Only").
- [ ] T017 [US1] [Plan Override] Implement error handling for missing anxiety measures: Log specific dataset IDs, categorize (T014), then trigger abort (T015). Note: Implements Spec's search logic but follows Plan's abort directive.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - EEG Pre‑processing & P300 Extraction (Priority: P2)

**Goal**: Preprocess raw EEG files and extract P300 amplitude/latency for eligible datasets, applying strict QC checks. Supports parameterized threshold for sensitivity analysis.

**Independent Test**: Run `code/preprocess.py` on a sample of 20 participants with a specific threshold; verify output CSV has correct columns, epoch retention >80%, and P amplitudes in 2–15 µV range.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Unit test for band-pass filtering in `tests/test_preprocess.py`
- [X] T022 [P] [US2] Unit test for ICA artifact removal in `tests/test_preprocess.py` <!-- FAILED: unspecified -->

### Implementation for User Story 2

- [X] T020 [US2] Implement `code/preprocess.py` to load raw.edf files, apply band-pass filter (low-frequency to high-frequency cutoffs), and accept a `--rejection_threshold` argument (default ±100 µV) for epoch rejection.
- [X] T023 [US2] Implement average referencing and ICA-based ocular artifact removal in `code/preprocess.py`
- [ ] T024 [US2] Implement epoching logic: baseline pre-stimulus to post-stimulus window around feedback onset
- [ ] T025 [US2] Implement P300 extraction: find peak amplitude (early-to-mid latency) at Pz and CPz electrodes per trial
- [ ] T026 [US2] Implement QC validation: check trial retention (>80%) and amplitude range (2–15 µV); exclude participants failing QC. **Output**: If QC fails for any participant, flag and log; if aggregate QC fails, trigger T016d.
- [ ] T027 [US2] Generate `data/processed/p300_measures.csv` with columns: `subject_id`, `condition`, `p300_amplitude`, `p300_latency`, `qc_status`, `threshold_used`
- [ ] T028a [US2] Implement logging for excluded participants and rejected epochs (<20% rejection rate target)
- [ ] T016d [US1/US2] Generate "Negative Finding Report" (PDF/HTML) for the "QC Failure" scenario. **Trigger Condition**: Execute ONLY IF T026 triggers an abort due to QC failure. Content: List of excluded participants, reasons for exclusion, and statement of data quality gap. Dependencies: T026 (if triggered).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Modeling & Sensitivity Analysis (Priority: P3)

**Goal**: Fit a mixed-effects model to test the interaction between validation type and social anxiety, including sensitivity analysis and Bayes Factor calculation.

**Independent Test**: Run `code/analyze.py` on the full cleaned dataset; verify model convergence, Holm-Bonferroni correction, and stable sensitivity sweep results.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T029 [P] [US3] Unit test for LMM model fitting in `tests/test_analyze.py`
- [ ] T030 [P] [US3] Unit test for Holm-Bonferroni correction in `tests/test_analyze.py`

### Implementation for User Story 3

- [ ] T045 [US3] Implement `code/analyze.py` to fit Linear Mixed-Effects Model: `p300_amplitude ~ validation_type * social_anxiety_score + (1|subject)` using the aggregated data. **Output**: Generate `data/results/model_summary.csv` with fixed effects, p-values, effect sizes, and BF.
- [ ] T030 [US3] Implement Holm-Bonferroni correction for fixed effects and compute Cohen's d effect sizes
- [ ] T031 [US3] Implement Bayes Factor calculation (using `pingouin`) for the interaction term
- [ ] T033 [US3] Generate `data/results/model_summary.csv` with fixed effects, p-values, effect sizes, and BF (Consolidated output from T045)
- [ ] T034 [US3] Implement conditional logic: If Phase 0 or Phase 1 aborted, ensure "Negative Finding Report" was generated (T016b/T016c/T016d) and skip statistical modeling.
- [ ] T042 [US3] Implement Sensitivity Loop: For each threshold in {±75, ±100, ±150 µV}:
 1. Call `code/preprocess.py` with `--rejection_threshold <value>` to generate threshold-specific data.
 2. Call `code/analyze.py` (T045) on the resulting data to fit a new model.
 3. Store the resulting model summary as `data/results/model_summary_<value>.csv`.
 Dependencies: T020, T045.
- [ ] T044 [US3] Compare Interaction Stability: Read `model_summary_75.csv`, `model_summary_100.csv`, `model_summary_150.csv`. Extract the interaction term p-value and Bayes Factor for each. Verify that the significance (p < 0.05) and direction of the effect remain stable across all three thresholds. Output: `data/results/sensitivity_comparison.csv` and a boolean flag `is_stable`. **Requirement**: Must explicitly compare interaction statistics to satisfy FR-006/SC-003.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reporting & Visualization (Priority: P3)

**Goal**: Generate reproducible PDF/HTML reports containing waveforms, model tables, and sensitivity plots.

**Independent Test**: Run `code/report.py` and verify PDF/HTML files are generated with correct figures and traceable data.

### Implementation for Reporting

- [ ] T035 [P] [US3] Implement `code/report.py` to generate ERP waveform plots (simulated vs real) using `matplotlib`/`seaborn`
- [ ] T036 [US3] Implement table generation for LMM results and sensitivity analysis
- [ ] T037 [US3] Generate `data/results/report.html` and `data/results/report.pdf` with discussion of associational vs. causal interpretation. **Content**: Include Sensitivity plots from T044 and model tables from T045. **Condition**: Skip if Negative Finding path taken (T016b/c/d). Dependencies: T044, T045.
- [ ] T038 [US3] Ensure all figures/tables in reports trace back to `data/processed` CSVs (Single Source of Truth)

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Documentation updates in `docs/` and `README.md`
- [ ] T041 Code cleanup and refactoring for performance optimization
- [ ] T042 [P] Additional unit tests for edge cases (missing data, low-quality epochs) in `tests/unit/`
- [ ] T043 Security hardening: PII scan on data commits
- [ ] T044 Run `quickstart.md` validation to ensure full pipeline execution on CPU-only CI

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
 - **Critical**: Must complete before US2/US3 to determine if "Negative Finding" path is triggered
 - **Abort Path**: If T015 triggers, T016b/c/d generates report and BYPASSES Phase 4 & 5.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) AND US1 confirms "Eligible" dataset
 - Depends on US1 output (`data/results/dataset_search_results.csv`)
 - **Abort Path**: If T026 triggers QC failure, T016d generates report and BYPASSES Phase 5.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) AND US2 confirms QC pass
 - Depends on US2 output (`data/processed/p300_measures.csv`)
 - Depends on T042 (Sensitivity Loop) and T044 (Stability Check) completion.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services (N/A for research pipeline)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 can start immediately. US2 and US3 are blocked until US1 confirms eligibility.
- All tests for a user story marked [P] can run in parallel
- Different components of the same story (e.g., filtering vs. epoching) can be worked on in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for dataset categorization logic in tests/test_search.py"
Task: "Integration test for OpenNeuro API query in tests/test_search.py"

# Launch core implementation tasks for User Story 1 together:
Task: "Implement code/search.py to query OpenNeuro/PhysioNet"
Task: "Implement metadata parsing in code/search.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Dataset Search)
4. **STOP and VALIDATE**: Check if eligible dataset found.
 - If **No**: T016b/c/d generates "Negative Finding Report" and project completes.
 - If **Yes**: Proceed to Phase 4.
5. Deploy/demo if ready.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → **Decision Point** (Proceed or Abort)
3. Add User Story 2 → Test independently → QC Check
4. Add User Story 3 → Test independently → Statistical Results
5. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Dataset Search)
 - Developer B: User Story 2 (Preprocessing - can start drafting but blocked on data)
 - Developer C: User Story 3 (Analysis - can start drafting but blocked on data)
3. Once US1 confirms eligibility, US2 and US3 proceed to full implementation.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **CRITICAL**: If US1 finds no eligible dataset, the pipeline MUST abort analysis and generate a "Negative Finding Report" (T016b/c/d) rather than attempting invalid meta-analysis. The Spec's requirement to "identify" candidates is satisfied by T014, but the Plan's abort is executed in T015.
- **Sensitivity Analysis**: T042 and T044 ensure re-processing and re-modeling at each threshold to satisfy FR-006, with T044 explicitly verifying the stability of the *interaction term conclusions*.
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence