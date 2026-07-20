# Implementation Plan: The Effects of Gamified Habit Tracking on Long-Term Behavioral Change

**Branch**: `001-gamification-effects` | **Date**: 2026-06-24 | **Spec**: `specs/001-the-effects-of-gamified-habit-tracking-o/spec.md`
**Input**: Feature specification from `/specs/001-the-effects-of-gamified-habit-tracking-o/spec.md`

## Summary

This project investigates whether gamified habit-tracking applications (points, badges, leaderboards) produce higher long-term adherence to self-defined behavioral goals compared to non-gamified tools, and how this effect is moderated by personality traits (Conscientiousness, Need for Achievement). The technical approach involves attempting ingestion from a verified longitudinal source (Habitica API), and if unavailable, generating a deterministic synthetic dataset that mimics the expected schema. The data is aggregated into weekly adherence metrics, and mixed-effects logistic regression models with survival analysis components are fitted. The study strictly adheres to the project constitution regarding ethical data handling, reproducibility, and psychometric validity. All statistical findings are framed as associational due to the observational (and synthetic) nature of the data.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `statsmodels`, `scikit-learn`, `seaborn`, `matplotlib`, `jinja2`, `pyyaml`, `pytest`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/reports`)  
**Testing**: `pytest` (unit tests for data ingestion, integration tests for modeling pipeline)  
**Target Platform**: Linux (GitHub Actions runner: 2 CPU, 7GB RAM)  
**Project Type**: Data Science Pipeline / Statistical Analysis  
**Performance Goals**: Full pipeline execution < 6 hours; memory usage < 6GB during bootstrapping  
**Constraints**: CPU-only execution (no GPU); minimum sample size N=100 (per SC-001); strict adherence to FR-010 (consent check) before processing; survival analysis halts if dropout events < 10 per group (per FR-009).  
**Scale/Scope**: Single dataset (simulated or API logs), 1,000 bootstrap iterations (per SC-004), 100+ user records (per SC-001).  

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**: Plan includes pinned `requirements.txt` and random seed setting in `code/`. External data source (synthetic generator or API) is deterministic based on seed or API state.
- **Principle II (Verified Accuracy)**: All citations in `research.md` will be validated against primary sources (e.g., Q113106917) before inclusion.
- **Principle III (Data Hygiene)**: Plan mandates checksumming of `data/` artifacts and immutable raw data processing.
- **Principle IV (Single Source of Truth)**: All statistics in the final report will be generated programmatically from the *pipeline code* acting on the *raw synthetic data* (or API logs), ensuring traceability.
- **Principle V (Versioning)**: `state.yaml` will be updated with content hashes of all final artifacts (Task T033).
- **Principle VI (Ethical Data Handling)**: Plan includes a mandatory `check_consent.py` step (T012a) that halts execution if *real* consent artifacts are missing. If synthetic data is used, a 'Simulated Consent Record' is generated *only after* confirming no real data exists, and is explicitly flagged as 'SIMULATED' in the report.
- **Principle VII (Psychometric Validity)**: Plan includes `calculate_cronbach_alpha.py` (T012c) to validate personality scales before modeling and report the result (FR-011).

## Project Structure

### Documentation (this feature)

```text
specs/001-gamification-effects/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── data/
│   ├── synthetic_generator.py   # Generates synthetic longitudinal logs (fallback)
│   ├── ingestion.py             # Loads and validates data (API or Synthetic)
│   └── consent_check.py         # Verifies consent artifacts
├── analysis/
│   ├── aggregation.py           # Daily -> Weekly binning
│   ├── modeling.py              # Mixed-effects & Survival models
│   ├── robustness.py            # Bootstrapping & Sensitivity analysis
│   └── correction.py            # FDR/Bonferroni logic (excludes time points)
├── reports/
│   ├── template.html            # Jinja2 template for final report
│   └── generate_report.py       # Report generation script (includes limitations)
├── utils/
│   ├── validation.py            # Schema validation & VIF checks
│   └── versioning.py            # Artifact hashing
└── tests/
    ├── test_data.py
    ├── test_modeling.py
    └── test_pipeline.py

data/
├── raw/
│   ├── synthetic_data.csv       # Generated logs (if API fails)
│   └── consent/
│       └── consent_record.json  # Real or Simulated consent artifact
├── processed/
│   └── merged_data.csv          # Analysis-ready dataset
└── reports/
    └── final_analysis.html      # Final output

state.yaml
requirements.txt
```

**Structure Decision**: Single project structure selected to align with the statistical analysis nature of the work, keeping data, code, and reports in a unified hierarchy for reproducibility.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Mixed-Effects Model | Required for repeated measures (weekly logs) per user | Standard logistic regression ignores within-user correlation, violating FR-002. |
| Survival Analysis | Required to model "time-to-dropout" (3 consecutive weeks non-adherence) | Simple adherence rates ignore the temporal dimension of dropout defined in US-2. |
| Stratified Bootstrapping | Required to maintain group balance (gamified vs. non-gamified) and preserve interaction structure | Simple bootstrapping may create empty groups in resamples, invalidating interaction tests. |
| FDR Correction | Required by FR-007 for multiple personality trait tests | Bonferroni is too conservative for correlated traits; FDR balances power and error control. Time points excluded per FR-007. |

## Phases and Tasks

### Phase 0: Data Source Verification (NEW - Addresses FR-001)
- [ ] **T001**: Attempt ingestion from verified longitudinal source (Habitica API).
- [ ] **T002**: If API ingestion fails (auth/availability), log failure and proceed to synthetic generation.

### Phase 1: Data Generation & Ingestion
- [ ] **T013a**: Generate synthetic data (if T001 failed) using `synthetic_generator.py` with specific parameters (null-hypothesis mode, AR(1) noise) and save to `data/raw/synthetic_data.csv`.
- [ ] **T013b**: Ingest data (API or Synthetic) via `ingestion.py`, validate `gamified_app_usage` tags, check `MIN_TOTAL_RECORDS` (≥100) and `MIN_NON_GAMIFIED_USERS` (≥30), and halt with "Data Insufficiency" if thresholds not met.
- [ ] **T012a**: Check for consent artifacts. If *real* data exists, halt if missing. If synthetic, generate `data/consent/consent_record.json` flagged as 'SIMULATED'.
- [ ] **T012b**: Calculate Cronbach's alpha for personality scales.
- [ ] **T012c**: Report Cronbach's alpha in final output (FR-011).
- [ ] **T014**: Aggregate daily logs into weekly bins (`week_number`, `weekly_adherence_flag`).
- [ ] **T017**: Generate `data/processed/merged_data.csv` and verify it contains required columns (User_ID, Gamified, Adherence, Personality Scores).

### Phase 2: Modeling & Robustness
- [ ] **T021**: Calculate VIF for predictors. If VIF > 5 for `need_for_achievement`, drop it (log structural change).
- [ ] **T020**: Fit mixed-effects logistic regression model (fixed effects: gamification, personality, interaction; random intercept: user_id).
- [ ] **T022a**: Apply Benjamini-Hochberg (FDR) correction to interaction terms and secondary traits. **Explicitly exclude time points (weeks)** from correction set (FR-007).
- [ ] **T029**: Execute stratified bootstrapping (multiple iterations) preserving joint distribution of (Gamification, Personality).
- [ ] **T029a**: Validate bootstrap variance < 0.01. Halt if variance > 0.01 (SC-004).
- [ ] **T031a**: Perform sensitivity analysis on adherence thresholds (set:,, 3 events/week) and report coefficient stability (SC-005).
- [ ] **T032a**: Generate final report with mandatory 'Data Limitations' section (observational nature, synthetic data) and Cronbach's alpha (FR-006, FR-011).

### Phase 3: Validation & Release
- [ ] **T033**: Hash all final artifacts and update `state.yaml`.
- [ ] **T034**: Update `README.md` and `quickstart.md` with project overview and execution instructions.
- [ ] **T038**: Run `bash quickstart.sh` and verify exit code 0 and existence of `data/processed/merged_data.csv`.

## Execution Order Verification
The pipeline enforces the following dependency graph:
1. T001 (API) -> T002 (Fallback) -> T013a (Gen)
2. T013a/T001 -> T013b (Ingest) -> T012a (Consent) -> T012b (Alpha) -> T014 (Agg) -> T017 (Merge)
3. T017 -> T021 (VIF) -> T020 (Model) -> T022a (FDR)
4. T017 -> T029 (Bootstrap) -> T029a (Variance Check)
5. T017 -> T031a (Sensitivity)
6. T020, T022a, T029a, T031a -> T032a (Report) -> T033 (Hash) -> T038 (Verify)
