# Implementation Plan: The Influence of Simulated Social Validation on Neural Responses to Novel Information

**Branch**: `main-feature-sim-social-validation` | **Date**: 2026-07-06 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/main-feature-sim-social-validation/spec.md`

## Summary
This project investigates the neural correlates of simulated versus real social validation using EEG data, specifically focusing on the P300 component and its modulation by social anxiety. The plan executes a rigorous pipeline: (1) searching public repositories (OpenNeuro/PhysioNet) for datasets containing both social feedback manipulations and validated anxiety scales; (2) preprocessing EEG data (filtering, ICA, epoching) to extract P300 amplitude/latency; (3) fitting linear mixed-effects models (LMM) to test the interaction between validation type and anxiety; and (4) conducting sensitivity analyses on artifact rejection thresholds. The implementation prioritizes CPU-first execution on GitHub Actions, with a defined escape hatch to Kaggle GPU only if specific deep-learning preprocessing steps (not required by spec) were needed (none are; classical EEG tools are CPU-tractable).

**Critical Data Constraint**: The plan explicitly requires a **single dataset** containing both validation types (simulated/real) and anxiety measures. A meta-analytic approach using separate datasets is **scientifically invalid** for testing the interaction term (validation_type * anxiety) and is therefore **excluded** from the plan. If no single eligible dataset is found, the project **MUST abort** with a Negative Finding Report.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `mne` (EEG processing), `statsmodels` (LMM), `pandas`, `numpy`, `scipy`, `matplotlib`, `seaborn`, `datasets` (HuggingFace), `pyyaml`  
**Storage**: Local file system (`data/raw`, `data/processed`, `data/results`); no external DB.  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions Runner: 2 CPU, 7GB RAM, 14GB Disk).  
**Project Type**: Data Analysis Pipeline / Research Script  
**Performance Goals**: Complete full pipeline (download, preprocess, analyze, report) within 6 hours on CPU.  
**Constraints**: Must run on free-tier CI (no local GPU); datasets must be openly downloadable without credentials.  
**Scale/Scope**: Single dataset (or meta-analysis of two); A sample size consistent with typical EEG studies is expected.

> **Dataset Strategy**: The spec assumes a dataset exists with both simulated/real feedback and anxiety measures. If the search (FR-001) finds no single dataset, the plan **MUST** trigger the **Negative Finding Protocol** (T015, T016b, T016c, T016d). **Crucially**, if the verified datasets list (see `research.md`) does not contain a dataset with the required variables, the pipeline will NOT fabricate data but will trigger the abort logic and generate the required report.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Action Required |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Compliant** | Plan mandates `requirements.txt`, pinned seeds, and `data/` checksums. |
| **II. Verified Accuracy** | **Compliant** | All citations in `research.md` will be drawn *only* from the verified datasets block. If no dataset is found, the Negative Finding Report serves as the verified artifact for the data gap. |
| **III. Data Hygiene** | **Compliant** | Plan includes checksumming (`data/`), no in-place modification, and PII scan. |
| **IV. Single Source of Truth** | **Compliant** | All figures/tables generated from `data/processed` CSVs; no hand-typed stats. |
| **V. Versioning Discipline** | **Compliant** | Artifacts will carry content hashes in `state/projects/PROJ-496-the-influence-of-simulated-social-valida.yaml` and update `updated_at`. |
| **VI. Neural Outcome Fidelity** | **Compliant** | P300 is the designated outcome; extraction logic is explicitly defined. |
| **VII. Validation Condition Integrity** | **Compliant** | Data structures maintain `validation_type` (simulated vs. real) as a distinct categorical variable. |

## Project Structure

### Documentation (this feature)
```text
specs/main-feature-sim-social-validation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)
```text
projects/PROJ-496-the-influence-of-simulated-social-valida/
├── code/
│   ├── __init__.py
│   ├── search.py                # FR-001: Dataset search & categorization
│   ├── preprocess.py            # FR-003, FR-004: EEG filtering, ICA, P300 extraction
│   ├── analyze.py               # FR-005, FR-006: LMM, Holm-Bonferroni, Sensitivity
│   ├── report.py                # FR-007: PDF/HTML generation
│   └── utils.py                 # Logging, QC, checksum helpers
├── data/
│   ├── raw/                     # Downloaded raw EEG (parquet/edf)
│   ├── processed/               # Cleaned epochs, P300 metrics
│   └── results/                 # Model outputs, sensitivity plots, reports
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── docs/
└── .github/workflows/
    └── ci.yml
```

**Structure Decision**: Single project structure selected to align with the research pipeline nature of the spec. Directories `code`, `data`, `tests`, `docs` are created explicitly to satisfy Constitution Principle I (Reproducibility) and Principle III (Data Hygiene).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Meta-analysis Logic** | If no single dataset contains both conditions, the system must abort. | A meta-analytic approach using separate datasets is scientifically invalid for testing the interaction term (validation_type * anxiety) and is therefore excluded. |
| **Sensitivity Sweep** | FR-006 requires a sweep of artifact thresholds (75, 100, 150 µV). | A single-threshold analysis would violate the robustness requirement and fail SC-003 (stability check). |
| **Negative Finding Report** | T015/T016 require a formal report if data is missing. | Simply aborting without a report violates the "Verified Accuracy" and "Data Hygiene" principles by leaving the project state undefined. |

## Task Definitions

*Explicit definitions for all referenced tasks (T015, T016b/c/d, etc.) to ensure implementation fidelity.*

- **T001a**: Create project root directory (`projects/PROJ-496-the-influence-of-simulated-social-valida/`). Verification: `os.path.exists(project_root)`.
- **T001b**: Create `data/`, `code/`, `tests/`, `docs/` directories. Verification: `os.path.exists(dir)` for each.
- **T001c**: Create `tests/` directory with `.gitkeep`. Verification: `os.path.exists(tests/.gitkeep)`.
- **T001d**: Create `docs/` directory with `.gitkeep`. Verification: `os.path.exists(docs/.gitkeep)`.
- **T003**: Create `github/workflows/lint.yml` with valid CI configuration. Verification: File exists and passes YAML lint.
- **T004**: Create `.gitkeep` files in `data/raw`, `data/processed`, `data/results`. Verification: Files exist.
- **T007**: Create `contracts/*.schema.yaml` files with valid schema definitions. Verification: Files exist and pass YAML lint.
- **T014**: Implement dataset categorization logic to produce six lists (Eligible, Sim-Only, Real-Only, Partial-EEG, Partial-Anxiety, None). Verification: Script outputs lists.
- **T015**: Implement abort logic: If no eligible dataset found, trigger Negative Finding Report. Verification: Report generated.
- **T016b**: Generate "Negative Finding Report" (PDF/HTML) for "No Data" scenario. Verification: Report file exists.
- **T016c**: Generate "Negative Finding Report" (PDF/HTML) for "Partial Data" scenario. Verification: Report file exists.
- **T016d**: Generate "Negative Finding Report" (PDF/HTML) for "QC Failure" scenario. Verification: Report file exists.
- **T017**: Implement error-handling for missing anxiety measures (log ID, categorize, abort). Verification: Log file generated.
- **T024**: Implement epoching logic (baseline pre-stimulus to post-stimulus window). Verification: Epochs generated.
- **T025**: Implement P300 extraction: find peak amplitude (early-to-mid post-stimulus window) at Pz and CPz electrodes per trial. Verification: P300 values extracted.
- **T026**: Implement QC validation: check trial retention (>80%) and amplitude range (2–15 µV); exclude participants failing QC. Verification: Exclusion log generated.
- **T027**: Generate CSV with columns: `subject_id`, `condition`, `p300_amplitude`, `p300_latency`, `trial_count`, `rejected`. Verification: CSV matches schema.
- **T028a**: Implement logging for excluded participants (log file path, format, message structure). Verification: Log file generated.
- **T029**: Unit test for LMM model fitting (test function name, input data, expected assertions). Verification: Test passes.
- **T030**: Implement Holm-Bonferroni correction (exact function/library, output format). Verification: Corrected p-values generated.
- **T031**: Implement Bayes Factor calculation (exact function, parameters, output format). Verification: BF generated.
- **T033**: Generate CSV with fixed effects, p-values, effect sizes, and BF (exact column names, data types). Verification: CSV matches schema.
- **T034**: Implement conditional logic: If Phase 0 or Phase 1 aborted, return early or raise exception. Verification: Logic executes correctly.
- **T035**: Implement ERP waveform plots (exact plot type, labels, output file format). Verification: Plots generated.
- **T036**: Implement table generation for LMM results and sensitivity analysis (exact table format, columns). Verification: Tables generated.
- **T038**: Ensure all figures/tables in reports trace back to `data/processed` CSVs (verification script or comment). Verification: Paths match.
- **T042**: Additional unit tests for edge cases (test function names, inputs, expected outputs). Verification: Tests pass.
- **T043**: Security hardening: PII scan on data commits (tool, configuration). Verification: Scan passes.
- **T044**: Run quickstart.md validation (exact command, expected output). Verification: Validation passes.

## Phases

### Phase 0: Dataset Discovery & Eligibility (FR-001, FR-002, SC-001)

**Goal**: Search for and verify a single dataset containing both validation types and anxiety measures.

- **Phase 0.1: Search Execution (FR-001)**
  - Execute `code/search.py` with keywords "social", "feedback", "validation", "anxiety".
  - Output: `data/raw/dataset_catalog.csv` with candidate datasets.
  - Task: T014 (Categorization Logic).

- **Phase 0.2: Eligibility Verification (FR-002)**
  - Verify each candidate dataset includes (a) social-feedback manipulation (simulated vs. real) and (b) a validated social-anxiety scale (e.g., LSAS, SPIN).
  - Task: T017 (Error Handling for missing measures).

- **Phase 0.3: Success Criterion Validation (SC-001)**
  - Check if at least one dataset meets both criteria OR if two separate datasets are identified for meta-analysis (Note: Meta-analysis is now invalid; only single dataset is acceptable).
  - If no eligible dataset found, trigger T015 (Abort Logic).

- **Phase 0.4: Manual Review Protocol (Spec Assumption)**
  - If no eligible dataset found in Phase 0.3, expand keywords and search alternative repos (e.g., Zenodo, Figshare) as per Spec Assumption.
  - If still no eligible dataset, trigger T015 (Abort Logic).

- **Phase 0.5: Power & Feasibility Check**
  - If eligible dataset found, perform power analysis to ensure N is sufficient for interaction effect.
  - If N < required, trigger T015 (Abort Logic).

### Phase 1: EEG Preprocessing & P300 Extraction (FR-003, FR-004, SC-002)

**Goal**: Preprocess raw EEG files and extract P300 amplitude and latency.

- **Phase 1.1: Data Ingestion**
  - Download raw EEG files from verified dataset.
  - Task: T004 (Create `.gitkeep` files in `data/raw`).

- **Phase 1.2: Preprocessing (FR-003)**
  - Apply band-pass filter (high-pass, low-pass).
  - Apply average reference.
  - Perform ICA-based ocular artifact removal.
  - Epoch from pre-stimulus baseline to post-stimulus window around feedback onset.
  - Task: T024 (Epoching Logic).

- **Phase 1.3: P300 Extraction (FR-004)**
  - Compute peak P amplitude (maximum positive voltage) within 250-550ms at electrodes Pz and CPz for each trial.
  - Task: T025 (P300 Extraction).

- **Phase 1.4: Data Export**
  - Export tidy dataset containing `subject_id`, `condition`, `p300_amplitude`, `p300_latency`, `trial_count`.
  - Task: T027 (Generate CSV).

- **Phase 1.5: QC Validation (SC-002)**
  - Check trial retention (>=80% per condition) and amplitude range (2-15 µV).
  - Exclude participants failing QC.
  - Task: T026 (QC Validation), T028a (Logging).

### Phase 2: Statistical Modeling (FR-005)

**Goal**: Fit mixed-effects regression testing main effect and moderation.

- **Phase 2.1: Model Fitting**
  - Fit LMM with `p300_amplitude` as dependent variable, `validation_type` and `social_anxiety_score` as fixed effects, and `validation_type * social_anxiety_score` as interaction.
  - Random intercepts for `subject_id`.
  - Task: T029 (Unit Test for LMM).

- **Phase 2.2: Correction & Effect Size**
  - Apply Holm-Bonferroni correction for fixed effects.
  - Calculate Cohen's d and Bayes Factor.
  - Task: T030 (Holm-Bonferroni), T031 (Bayes Factor).

- **Phase 2.3: Data Export**
  - Export model summary CSV with fixed effects, adjusted p-values, effect sizes, and BF.
  - Task: T033 (Generate CSV).

### Phase 3: Sensitivity Analysis (FR-006, SC-003)

**Goal**: Perform sensitivity analysis on artifact rejection thresholds.

- **Phase 3.1: Sensitivity Sweep (FR-006)**
  - Sweep artifact rejection voltage threshold over {±75, ±100, ±150 µV}.
  - Task: T042 (Sensitivity Loop).

- **Phase 3.2: Stability Check (SC-003)**
  - Report how effect-size estimates and adjusted p-values change across thresholds.
  - Task: T044 (Stability Check).

- **Phase 3.5: Success Criterion Validation (SC-003)**
  - Check if model yields Holm-adjusted p-value < 0.05 for interaction OR Bayes factor > 3.
  - Check if sensitivity sweep shows stable conclusions.
  - If criteria not met, flag in report.

### Phase 4: Reporting (FR-007)

**Goal**: Generate reproducible reports (PDF & HTML).

- **Phase 4.1: Report Generation**
  - Generate PDF & HTML reports containing ERP waveforms, model summary tables, sensitivity plots, and discussion.
  - Task: T035 (ERP Plots), T036 (Table Generation).

- **Phase 4.2: Traceability Check**
  - Ensure all figures/tables in reports trace back to `data/processed` CSVs.
  - Task: T038 (Traceability).

- **Phase 4.3: Final Output**
  - Output `data/results/final_report.pdf`, `data/results/final_report.html`.

## Negative Finding Protocol

If Phase 0 (Search) or Phase 1 (Preprocessing) fails to produce eligible data:

1. **Trigger T015 (Abort Logic)**: Halt execution.
2. **Generate Report**:
   - If no data found: T016b (No Data Report).
   - If partial data found: T016c (Partial Data Report).
   - If QC failure: T016d (QC Failure Report).
3. **Log**: Record failure in `data/results/negative_finding_report_v1.pdf`.
