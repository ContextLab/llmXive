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

**Purpose**: Project initialization and basic structure.
**⚠️ Atomic Execution**: Task T001 must be executed as a single block to ensure complete directory structure integrity.

- [X] T001 [P] Create `projects/PROJ-496-the-influence-of-simulated-social-valida/` directory structure. **Command**: `mkdir -p projects/PROJ-496-the-influence-of-simulated-social-valida/{code,data,tests,docs,data/{raw,processed,results}} && touch projects/PROJ-496-the-influence-of-simulated-social-valida/{code,data,tests,docs,data/raw,data/processed,data/results}/.gitkeep`. **Verification**: Confirm all directories and `.gitkeep` files exist.
- [X] T002a [P] Create `requirements.txt` with pinned versions for `mne`, `statsmodels`, `pandas`, `numpy`, `scikit-learn`, `openneuro-py`, `requests`, `pyyaml`, `matplotlib`, `seaborn`, `reportlab`, `pingouin`.
- [X] T003 [P] Configure linting (flake8/black) and formatting tools in `.github/workflows/lint.yml`. **Content**: Create `.github/workflows/lint.yml` with:
 ```yaml
 name: Lint
 on: [push, pull_request]
 jobs:
 lint:
 runs-on: ubuntu-latest
 steps:
 - uses: actions/checkout@v3
 - name: Set up Python
 uses: actions/setup-python@v4
 with:
 python-version: '3.11'
 - name: Install dependencies
 run: |
 pip install black flake8
 - name: Run black
 run: black --check --line-length 88 code/
 - name: Run flake8
 run: flake8 --max-line-length=88 --exclude=.git code/
 ```
- [X] T007 [P] Create base data schemas in `specs/main-feature-sim-social-validation/contracts/` (`eeg_dataset.schema.yaml`, `p300_measure.schema.yaml`). **Content**:
 `eeg_dataset.schema.yaml`:
 ```yaml
 type: object
 properties:
 dataset_id: {type: string}
 title: {type: string}
 feedback_type: {type: string, enum: [simulated, real, mixed]}
 anxiety_measure: {type: string}
 url: {type: string}
 required: [dataset_id, title, feedback_type, url]
 ```
 `p300_measure.schema.yaml`:
 ```yaml
 type: object
 properties:
 subject_id: {type: string}
 condition: {type: string}
 p300_amplitude: {type: number}
 p300_latency: {type: number}
 qc_status: {type: string, enum: [pass, fail]}
 required: [subject_id, condition, p300_amplitude, p300_latency, qc_status]
 ```

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Setup `data/raw`, `data/processed`, `data/results` directory structure. **Command**: `mkdir -p projects/PROJ-496-the-influence-of-simulated-social-valida/data/{raw,processed,results} && touch projects/PROJ-496-the-influence-of-simulated-social-valida/data/{raw,processed,results}/.gitkeep`. **Verification**: Confirm all three subdirectories and `.gitkeep` files exist.
- [X] T005 [P] Implement `code/config.py` for path management and environment variables
- [X] T006 [P] Setup `code/__init__.py` and logging infrastructure in `code/logger.py`
- [X] T008 [P] Implement `code/main.py` entry point with argument parsing and phase routing logic
- [X] T046 [P] **Constitution Compliance**: Implement random seed pinning in `code/config.py` (set `RANDOM_SEED=42`) and propagate to `numpy`, `random`, and any ML libraries in `code/main.py` before any data loading or model fitting. This satisfies Constitution Principle I (Reproducibility).
- [X] T009a [P] Create `tests/test_search.py` with function `test_categorizes_eligible_dataset`
- [X] T009b [P] Create `tests/test_preprocess.py` with function `test_filtering_and_ica` <!-- FAILED: unspecified -->
- [X] T009c [P] Create `tests/test_analyze.py` with function `test_lmm_convergence`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Discovery & Eligibility Check (Priority: P1) 🎯 MVP

**Goal**: Identify a single dataset containing both social feedback manipulation and social anxiety measures. If none found, execute the Manual Review Protocol (expanded search). If still no single dataset, trigger the Negative Finding Protocol (T016b). **NOTE**: Per Plan `Critical Data Constraint`, meta-analysis of separate datasets is scientifically invalid for this hypothesis; the project MUST abort if a single dataset is not found.

**Independent Test**: Run `code/search.py` against OpenNeuro/PhysioNet/Zenodo; verify it outputs a CSV of candidates, correctly categorizes them, and triggers the appropriate exit code and report generation.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for dataset categorization logic in `tests/test_search.py`
- [X] T011 [P] [US1] Integration test for OpenNeuro API query in `tests/test_search.py`

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/search.py` to query OpenNeuro/PhysioNet. **API Endpoint**: ` Name or service not known)"))]. **Query**: `query { datasets(filter: { modalities: [EEG] }) { id, label, description, task } }`. **Keywords**: "social", "feedback", "validation", "anxiety". **Output**: JSON list of candidate datasets.
- [X] T013 [P] [US1] Implement metadata parsing in `code/search.py` to detect `feedback_type` (simulated vs real) and `anxiety_measure` (e.g., LSAS, SPIN). **JSON Fields**: `task`, `description`, `custom_metadata.anxiety_scale`. **Logic**: Parse `custom_metadata` or `description` for keywords.
- [X] T014 [US1] Implement logic to categorize datasets: "Eligible" (both present), "Sim-Only", "Real-Only", "Partial-EEG", "Partial-Anxiety", or "None". **Output**: Log categorized lists to `data/results/categorization_log.json` with schema: `{"Eligible": [...], "Sim-Only": [...], "Real-Only": [...], "Partial-EEG": [...], "Partial-Anxiety": [...], "None": [...]}`. **Note**: Per Plan, "Sim-Only"/"Real-Only" are NOT valid for analysis; they trigger abort.
- [X] T016a [US1] Generate `data/results/dataset_search_results.csv` with columns: `dataset_id`, `title`, `feedback_type`, `anxiety_measure`, `status`, `url`. **Format**: CSV with header.
- [X] T012b [US1] **Manual Review Protocol**: If T014 finds no "Eligible" dataset, execute expanded search. **Action**: Query Zenodo/Figshare. **Endpoint**: `. **Query Params**: `q=(social validation AND EEG) AND (anxiety)`. **Output**: Append results to `data/results/categorization_log.json`.
- [X] T013b [US1] **Manual Review Protocol**: Parse Zenodo/Figshare metadata for `feedback_type` and `anxiety_measure`. **Logic**: Map `metadata.subjects` (keyword: "social validation") to `feedback_type`; map `metadata.description` (keywords: "LSAS", "SPIN", "anxiety") to `anxiety_measure`. **Output**: Update `categorization_log.json`.
- [X] T015 [US1] **Abort Logic & Router**: Read `data/results/categorization_log.json` (after T012b/T013b completes).
 - **If "Eligible" list is NOT empty**: Proceed to Phase 4.
 - **If "Eligible" is empty**: **IMMEDIATELY** Trigger T016b (Negative Finding Report). **DO NOT** check for "Sim-Only" or "Real-Only" as valid paths. The Plan mandates abort if no single dataset is found.
 - **Function Call**: `generate_report(type="no_data", data=log)`. **Dependencies**: T014, T016a, T012b, T013b.
- [X] T016b [US1] **Negative Finding Report (No Data)**: Generate PDF/HTML for "No Eligible Datasets Found" scenario. **Trigger Condition**: Execute ONLY IF T015 detects "None" status or empty "Eligible" list. **Content**:
 - **Sections**: "Search Summary", "Eligibility Criteria", "Results (None Found)", "Conclusion (Negative Finding)".
 - **Data Mapping**: List all searched keywords, repos, and the "None" status datasets.
 - **Template**: Use `reportlab` to generate PDF.
 - **Dependencies**: T015 (must execute abort logic). **Note**: This is the ONLY valid outcome if no single dataset is found.
- [X] T057 [P] [US1] **Data Integrity**: Implement `code/utils.py` function `verify_real_data_source(dataset_id)` that performs a live connectivity check (HEAD request) to the dataset URL and validates file checksum if available. **Constraint**: This function MUST raise a `RuntimeError` if the real data source is unreachable; it MUST NOT fall back to synthetic/mock data. **Algorithm**: Use SHA256 for checksum validation if provided by source; if not, log "No checksum provided" and proceed. **Usage**: Integrate into T012/T013 to gate dataset eligibility.
- [X] T058 [US1] **Fail-Loud Enforcement**: Refactor `code/search.py` to ensure that if a dataset is marked "Eligible" but `verify_real_data_source` fails, the dataset is immediately re-categorized as "Partial-EEG" or "Partial-Anxiety" (as appropriate) and logged, rather than proceeding with a broken download. This prevents silent fabrication.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - EEG Pre‑processing & P300 Extraction (Priority: P2)

**Goal**: Preprocess raw EEG files and extract P300 amplitude/latency for eligible datasets, applying strict QC checks. Supports parameterized threshold for sensitivity analysis.

**Independent Test**: Run `code/preprocess.py` on a sample of 20 participants with a specific threshold; verify output CSV has correct columns, epoch retention >80%, and P amplitudes in 2–15 µV range.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Unit test for band-pass filtering in `tests/test_preprocess.py`
- [ ] T022 [P] [US2] Unit test for ICA artifact removal in `tests/test_preprocess.py`

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/preprocess.py` to load raw.edf files, apply band-pass filter (0.1 Hz high-pass, 40 Hz low-pass), and accept a `--rejection_threshold` argument (default ±100 µV) for epoch rejection. **Output**: Preprocessed epochs object.
- [ ] T023 [US2] Implement average referencing and ICA-based ocular artifact removal in `code/preprocess.py`. **Call**: `mne.preprocessing.ICA`.
- [X] T024 [US2] Implement epoching logic: baseline pre-stimulus to post-stimulus window around feedback onset. **Call**: `mne.Epochs(raw, events, tmin=-0.2, tmax=0.8, baseline=(-0.2, 0))`. **Output**: `data/processed/epochs_raw.fif`.
- [X] T025 [US2] Implement P300 extraction: find peak amplitude (maximum positive voltage) within a **250–550 ms** window **specifically at electrodes Pz and CPz** for each trial. **Method**: `np.max(epochs_data[channels=[Pz, CPz],:, time_indices])`. **Output**: `data/processed/p300_measures.csv`.
- [X] T026 [US2] Implement QC validation: check trial retention (>80%) and amplitude range (2–15 µV); exclude participants failing QC. **Output**: If QC fails for any participant, flag and log to `data/results/qc_failures.log`; if aggregate QC fails, trigger T016d. **Log Format**: `[INFO] Participant {id} excluded: {reason}`.
- [X] T027 [US2] Generate `data/processed/p300_measures.csv` with columns: `subject_id`, `condition`, `p300_amplitude`, `p300_latency`, `qc_status`, `threshold_used`. **Format**: Float with 3 decimal places. **Sample Row**: `001, simulated, 5.123, 340.500, pass, 100`.
- [X] T028a [US2] Implement logging for excluded participants and rejected epochs (<20% rejection rate target). **Log Path**: `data/results/qc_failures.log`. **Format**: `[INFO] Participant {id} excluded: {reason}`.
- [X] T016d [US1/US2] Generate "Negative Finding Report" (PDF/HTML) for the "QC Failure" scenario. **Trigger Condition**: Execute ONLY IF T026 triggers an abort due to QC failure. **Content**: List of excluded participants, reasons for exclusion, and statement of data quality gap. **Template**: Use `reportlab` to generate PDF with sections: "QC Summary", "Excluded Participants", "Conclusion (Negative Finding - Data Quality)". **Dependencies**: T026 (if triggered).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Modeling & Sensitivity Analysis (Priority: P3)

**Goal**: Fit a mixed-effects model to test the interaction between validation type and social anxiety, including sensitivity analysis and Bayes Factor calculation.

**Independent Test**: Run `code/analyze.py` on the full cleaned dataset; verify model convergence, Holm-Bonferroni correction, and stable sensitivity sweep results.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T029 [P] [US3] Unit test for LMM model fitting in `tests/test_analyze.py`. **Function Name**: `test_lmm_convergence`. **Input**: Mock P300 data. **Assertion**: Model converges without error.
- [ ] T030b [P] [US3] Unit test for Holm-Bonferroni correction in `tests/test_analyze.py`. **Function Name**: `test_holm_correction`. **Input**: Mock p-values. **Assertion**: Adjusted p-values are correct.

### Implementation for User Story 3

- [ ] T051 [US3] Implement `code/analyze.py` to fit Linear Mixed-Effects Model: `p300_amplitude ~ validation_type * social_anxiety_score + (1|subject)` using `statsmodels.formula.api.mixedlm`. **Output**: Generate `data/results/model_summary.csv` with fixed effects, p-values, effect sizes, and BF.
- [X] T030 [US3] Implement Holm-Bonferroni correction for fixed effects and compute Cohen's d effect sizes. **Call**: `statsmodels.stats.multitest.multipletests(pvals, method='holm')`.
- [X] T031 [US3] Implement Bayes Factor calculation (using `pingouin`) for the interaction term. **Call**: `pingouin.compute_bf(df, formula,...)`. **Output**: Log BF value to `data/results/model_summary.csv`. **Note**: Ensure model matches statsmodels mixedlm.
- [X] T033b [US3] Generate `data/results/model_summary.csv` with fixed effects, p-values, effect sizes, and BF (Consolidated output from T045). **Columns**: `term`, `estimate`, `std_error`, `p_value`, `holm_p_value`, `cohen_d`, `bayes_factor`.
- [ ] T034 [US3] Implement conditional logic: If Phase 0 or Phase 1 aborted, ensure "Negative Finding Report" was generated (T016b/T016d) and skip statistical modeling. **Condition Check**: Check for existence of `data/results/negative_finding_report_v1.pdf` or `qc_failures.log`. **Action**: If found, `return early` with exit code 0.
- [X] T061 [US3] **Threshold Justification**: Generate `data/results/threshold_justification.md`. **Content**: Cite Polich, 2007 (DOI: 10.1016/j.biopsycho.2007.01.005, Title: "P300: A review of the literature", Authors: Polich, J.) supporting the sweep range {75, 100, 150 µV}. **Requirement**: This file is a prerequisite for T052.
- [X] T052 [US3] Implement Sensitivity Loop: For each threshold in {±75, ±100, ±150 µV}:
 1. **Hard Gate**: Verify `data/results/threshold_justification.md` exists (T061). If not, abort.
 2. **Load**: Read pre-filtered, pre-ICA'd raw data from `data/processed/cleaned_raw.fif` (created once in T024).
 3. **Re-apply**: Create epochs from this cleaned data with the specific `--rejection_threshold <value>`. **Do not** re-filter or re-run ICA.
 4. **Re-extract**: Re-run P300 extraction (T025) on the re-thresholded epochs.
 5. **Re-model**: Call `code/analyze.py` (T051) on the resulting data to fit a new model.
 6. **Store**: Save model summary as `data/results/model_summary_<value>.csv`.
 Dependencies: T020 (implementation), T024 (epochs), T051 (analysis), T061 (justification).
- [X] T044 [US3] Compare Interaction Stability: Read `model_summary_75.csv`, `model_summary_100.csv`, `model_summary_150.csv`. Extract the interaction term `estimate` and `p_value` for each.
 - **Stability Logic**:
 - `direction_stable = all(sign(estimate) == sign(estimate[0]))`
 - `cv = std(effect_sizes) / mean(effect_sizes)`
 - `is_stable = (direction_stable) and (cv < 0.2 or (cv >= 0.2 and all(p < 0.05) or all(p > 0.05)))`
 - **Output**: `data/results/sensitivity_comparison.csv` with columns `threshold`, `estimate`, `p_value`, `cv`, `is_stable`. **Requirement**: Must explicitly compare interaction statistics to satisfy FR-006/SC-003.
- [X] T062 [US3] **Stability Metric Enhancement**: Refine T044 to calculate a "Stability Score" (0.0 to 1.0) based on the coefficient of variation of the interaction effect size across the three thresholds. **Output**: Add `stability_score` column to `data/results/sensitivity_comparison.csv`. A score < 0.8 should flag the result as "Unstable" in the final report (T037).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reporting & Visualization (Priority: P3)

**Goal**: Generate reproducible PDF/HTML reports containing waveforms, model tables, and sensitivity plots.

**Independent Test**: Run `code/report.py` and verify PDF/HTML files are generated with correct figures and traceable data.

### Implementation for Reporting

- [ ] T035 [P] [US3] Implement `code/report.py` to generate ERP waveform plots (simulated vs real) using `matplotlib`/`seaborn`. **Output**: `data/results/erp_waveform.png`. **Labels**: X-axis (Time ms), Y-axis (Amplitude µV), Legend (Condition). **Plot Type**: Line plot.
- [X] T036 [US3] Implement table generation for LMM results and sensitivity analysis. **Format**: Markdown table. **Columns**: Term, Estimate, P-Value, BF.
- [X] T037 [US3] Generate `data/results/report.html` and `data/results/report.pdf` with discussion of associational vs. causal interpretation. **Content**: Include Sensitivity plots from T052 and model tables from T051. **Condition**: Skip if Negative Finding path taken (T016b/d). Dependencies: T052, T051, T044, T062.
- [X] T038b [US3] Implement verification script `code/verify_traceability.py` to assert file paths match data/processed CSVs. **Logic**: Check that all figures/tables in reports reference files in `data/processed/`. **Action**: Assert file existence and hash match.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T040 [P] Documentation updates in `docs/` and `README.md`. **Content**: Update `README.md` with installation instructions (`pip install -r requirements.txt`), usage examples (`python code/main.py --phase search`), and data structure description.
- [X] T041 [P] Code cleanup and refactoring for performance optimization. **Target**: Optimize preprocessing loop (memory < 7GB) and model fitting (time < 6h).
- [X] T055 [P] Additional unit tests for edge cases (missing data, low-quality epochs) in `tests/unit/`. **Function Names**: `test_missing_data_handling`, `test_low_quality_epochs`. **Input**: Mock datasets with missing values. **Assertion**: Graceful handling or explicit error.
- [X] T043b [P] Security hardening: PII scan on data commits. **Tool**: Use `git-secrets`. **Config**: Add `.gitignore` rules for sensitive data patterns.
- [X] T056 [P] Run `quickstart.md` validation to ensure full pipeline execution on CPU-only CI. **Command**: `bash quickstart.sh`. **Expected Output**: Exit code 0 and all artifacts generated.
- [X] T063 [P] **Pipeline Diagram**: Generate `docs/pipeline_flow.svg` (or `.png`) illustrating the decision tree from Dataset Search (US1) through the Negative Finding paths (T016b/d) vs. the Analysis path (US2/US3). **Requirement**: Must clearly show the "Abort" triggers (No Single Dataset) and the "Success" path ONLY for a single eligible dataset. **Note**: The "Meta-Analysis Feasibility" path is REMOVED as per Plan constraint.
- [X] T064 [P] **Reproducibility Checklist**: Create `docs/reproducibility_checklist.md` that maps each Constitution Principle (I-VII) to the specific task ID that satisfies it (e.g., "Principle I: T046, T057").

**NOTE: Plan/Spec Conflict Alert**: The Plan (`plan.md:Critical Data Constraint`) explicitly forbids meta-analysis of separate datasets, while the Spec (`spec.md:Assumptions`) suggests it as a fallback. The tasks above strictly follow the Plan (abort if no single dataset). This conflict is flagged for human review/kickback to align the artifacts.

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
 - **Critical**: Must complete before US2/US3 to determine if "Negative Finding" or "Analysis" path is triggered
 - **Abort Path**: If T015 triggers T016b, the project completes with a report.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) AND US1 confirms "Eligible" dataset
 - Depends on US1 output (`data/results/dataset_search_results.csv`)
 - **Abort Path**: If T026 triggers QC failure, T016d generates report and BYPASSES Phase 5.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) AND US2 confirms QC pass
 - Depends on US2 output (`data/processed/p300_measures.csv`)
 - Depends on T052 (Sensitivity Loop) and T044 (Stability Check) completion.

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
 - If **No**: T016b generates report (No Data) and project completes.
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
- **CRITICAL**: If US1 finds no eligible dataset, the pipeline MUST execute the Manual Review Protocol (T012b/T013b). If still no single dataset, the project MUST trigger T016b (Negative Finding Report). **Meta-analysis of separate datasets is NOT a valid success path per Plan.**
- **Sensitivity Analysis**: T052 and T044 ensure re-processing and re-modeling at each threshold to satisfy FR-006, with T044 explicitly verifying the stability of the *interaction term conclusions*.
- **Data Integrity**: T057 and T058 ensure that no synthetic data is ever used as a fallback for missing real data sources, adhering to the "Fail-Loud" principle.
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

---

## Revision: New Tasks for Review Concerns

**Purpose**: Address specific reviewer concerns regarding data source verification, robustness of the abort logic, and explicit handling of the "Separate Datasets" scenario (which is now an abort condition).

### Data Source Verification & Fail-Loud Logic

- [ ] T065 [US1] **Real Data Stream Implementation**: Implement `code/search.py` to support streaming large EEG datasets via `datasets.load_dataset(..., streaming=True)` if a direct download exceeds 14GB disk. **Constraint**: Must accumulate statistics online without loading full dataset into RAM. **Output**: Log streaming status to `data/results/streaming_log.json`. **Dependency**: T057 (must verify source before streaming).
- [ ] T066 [US2] **Memory-Efficient Epoching**: Refactor `code/preprocess.py` to process EEG data in chunks if the raw file size exceeds a significant threshold, ensuring memory usage stays under a manageable limit. **Technique**: Use `mne.read_raw_edf(..., preload=False)` and process epochs in batches. **Output**: Log chunk processing stats to `data/results/memory_log.json`.

### Documentation & Reproducibility

- [X] T067 [US3] **Explicit Sample Size Justification**: Add a task to generate `data/results/sample_size_justification.md` that explicitly states the number of participants and trials used, and calculates the achieved statistical power for the interaction effect. **Requirement**: Must use `pingouin.power_ttest` or similar to report power. **Dependency**: T051 (must run model first).
- [X] T068 [US1] **Negative Finding Protocol Documentation**: Update `docs/NEGATIVE_FINDING_PROTOCOL.md` to explicitly detail the decision tree for T015, T016b, and T016d, including the exact conditions for triggering each report type. **Requirement**: Must include a flowchart image generated by T063.
