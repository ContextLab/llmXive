# Specification: The Impact of Nostalgia on Cognitive Flexibility in Aging Adults

## 1. Introduction
This specification defines the requirements for a research pipeline analyzing the effect of nostalgia on cognitive flexibility in adults aged 65 and older.

## 2. User Stories

### US1: Data Ingestion and Pre-processing
As a researcher, I want to ingest WCST data and validate it so that I can proceed with analysis on a clean, age-verified dataset.
- **Acceptance Criteria**:
 - Data is fetched from a real source or generated via Methodological Simulation.
 - `data/raw/metadata.json` includes `simulation_methodology` if in simulation mode.
 - Age filter (>=65) is applied.
 - MMSE exclusion (>=24) is applied if data exists.

### US2: Statistical Analysis
As a researcher, I want to perform statistical tests (Welch's t-test) to determine if nostalgia significantly impacts cognitive flexibility.
- **Acceptance Criteria**:
 - Welch's t-test is performed on `perseverative_errors` and `categories_completed`.
 - Bonferroni correction is applied.
 - Effect sizes (Cohen's d) and power analysis are calculated.
 - Assumption checks (Shapiro-Wilk, Levene) are logged.

### US3: Sensitivity and Robustness
As a reviewer, I want to see sensitivity analysis and robustness checks to ensure the results are not artifacts of specific thresholds or exclusions.
- **Acceptance Criteria**:
 - Sensitivity sweep across thresholds (0.01, 0.04, 0.05, 0.06, 0.10).
 - Robustness comparison (with vs. without MMSE exclusion).
 - `data/results/robustness_summary.md` is generated.

## 3. Data Model
- **Participant**: `participant_id`, `age`, `stimulus_type`, `perseverative_errors`, `categories_completed`, `MMSE` (optional).
- **Stimulus**: `stimulus_id`, `type`, `checksum`.

## 4. Verification & Accuracy Gates

### 4.1 Real Data Source Assertion
The system must verify the presence of `data/verified_source.json`. If it exists, the loaded dataset must match the defined package and config. Mismatches trigger a warning and fallback to simulation.

### 4.2 Simulation Transparency
When simulation is used, `data/raw/metadata.json` MUST include a `simulation_methodology` object containing:
- `random_seed`: The integer seed used.
- `distribution_parameters`: Means, stds, and ranges for generated variables.
- `sample_size`: The number of simulated records.
- `generation_logic`: A brief description of the generation algorithm.

### 4.3 Statistical Assumption Validation
Before running t-tests, normality and homogeneity of variance must be checked and logged in `data/results/assumption_checks.json`.

### 4.4 Robustness Summary
A human-readable summary (`data/results/robustness_summary.md`) must compare primary and robustness analyses, explicitly stating if conclusions hold across conditions.

## 5. Output Artifacts
- `data/raw/raw_dataset.csv`
- `data/processed/cleaned_dataset.csv`
- `data/results/statistical_report.json`
- `data/results/sensitivity_report.json`
- `data/results/robustness_summary.md`
- `data/raw/metadata.json` (with `simulation_methodology` if applicable)
