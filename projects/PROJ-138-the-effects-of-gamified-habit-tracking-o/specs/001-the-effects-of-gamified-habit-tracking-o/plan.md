# Implementation Plan: The Effects of Gamified Habit Tracking on Long-Term Behavioral Change

**Branch**: `001-gamification-effects` | **Date**: 2026-10-27 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-gamification-effects/spec.md`

## Summary

This project implements a statistical analysis pipeline to investigate whether gamified habit-tracking (points, badges) yields higher long-term adherence than non-gamified methods, moderated by personality traits (Conscientiousness, Need for Achievement). The technical approach involves ingesting longitudinal event logs, aggregating them into weekly adherence metrics, and fitting mixed-effects logistic regression and survival analysis models. The pipeline is designed to run entirely on CPU-only CI (GitHub Actions) using `statsmodels` and `lifelines`, with robustness checks via bootstrapping.

**Critical Note on Data & Power**: Due to the absence of a verified public longitudinal dataset containing both habit logs and personality traits, the default execution path uses a **synthetic data generator**. This generator is designed to validate the *pipeline logic* and *statistical recovery* of known parameters, not to provide definitive empirical evidence. The sample size (N=100) is acknowledged as underpowered for detecting interaction effects in mixed models; therefore, findings on real data (if ever obtained) would be strictly **exploratory**.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `lifelines`, `seaborn`, `matplotlib`, `pyyaml`, `pingouin` (for Cronbach's α), `scipy`
**Storage**: Local CSV/Parquet files (intermediate), final artifacts in `data/processed/`
**Testing**: `pytest` (unit tests for data aggregation, model convergence checks, contract validation)
**Target Platform**: Linux (GitHub Actions Free Runner: Limited CPU, 7GB RAM)
**Project Type**: Computational Research Pipeline / Data Analysis
**Performance Goals**: Complete analysis of ~100-500 users with 52 weeks of data in < 30 minutes.
**Constraints**: No GPU usage; no deep learning models; memory usage < 6GB; strict handling of missing data and censoring.
**Scale/Scope**: ~100 valid user records (minimum viability), up to 500 if data permits; Longitudinal data per user over a one-year period.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action / Note |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/`. `requirements.txt` pins all versions. Data ingestion script fetches from canonical source (or synthetic generator) deterministically. |
| **II. Verified Accuracy** | **PASS** | **Reference-Validator Agent** runs as a pre-condition for `research_complete` stage. All citations in `research.md` are validated against the "Verified datasets" block. |
| **III. Data Hygiene** | **PASS** | Raw data preserved in `data/raw/` with checksums. Derivations written to `data/processed/`. PII scan will be enforced. |
| **IV. Single Source of Truth** | **PASS** | All statistics in the final report will be generated programmatically from `code/` outputs. No hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | **Post-run hook** (`code/utils/versioning.py`) calculates SHA-256 hashes of all artifacts and updates `state.yaml` automatically. |
| **VI. Ethical Data Handling** | **PASS** | **FR-010**: Pipeline halts if `data/consent/` is missing. Personality data anonymized. |
| **VII. Psychometric Validity** | **PASS** | **FR-011**: `code/data/validation.py` includes `calculate_cronbach_alpha` function. |

## Project Structure

### Documentation (this feature)

```text
specs/001-gamification-effects/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Inputs to implementation)
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── data/
│   ├── ingestion.py       # FR-001, FR-001a, FR-001b
│   ├── aggregation.py     # FR-001b
│   └── validation.py      # FR-010, FR-011, Group Balance Check
├── analysis/
│   ├── modeling.py        # FR-002, FR-007 (FDR Correction)
│   ├── survival.py        # FR-003, FR-009 (Event Count Check)
│   └── robustness.py      # FR-004, FR-005
├── reports/
│   └── generate_report.py # FR-005
├── utils/
│   ├── config.py          # Seed pinning
│   ├── versioning.py      # Constitution Principle V (Hashing)
│   └── logging.py
├── tests/
│   ├── test_ingestion.py
│   ├── test_modeling.py
│   └── test_contracts.py
└── requirements.txt
```

**Structure Decision**: Single `code/` directory structure selected for simplicity and ease of CI execution. All logic is modularized by function (ingestion, modeling, reporting) to ensure testability and adherence to the "Single Source of Truth" principle. `pyyaml` is explicitly used for reading `contracts/` schemas to validate data frames.

## Implementation Phases

### Phase 0: Data Ingestion & Validation (FR-001, FR-010)
1.  **Check Consent**: Verify `data/consent/` exists. Halt if missing.
2.  **Ingest/Generate**: If real data exists, ingest from source. If not, run `synthetic_generator.py` with pinned seed.
3.  **Schema Validation**: Load `contracts/dataset.schema.yaml` (via `pyyaml`) and validate raw data structure.
4.  **Group Balance Check (FR-008)**: Count `gamified` vs `non-gamified`. If `non-gamified` < 30, halt with "Group Imbalance" error.

### Phase 1: Aggregation & Feature Engineering (FR-001b)
1.  **Weekly Binning**: Aggregate daily logs to `week_number`.
2.  **Adherence Flag**: Set `weekly_adherence_flag` (1 if count >= 1).
3.  **Dropout Logic**: Calculate `last_active_date`. Define dropout as 3 consecutive weeks of non-adherence *without subsequent activity* within the observation window.
4.  **Merge**: Join personality traits with weekly data.

### Phase 2: Psychometric Validation (FR-011)
1.  **Reliability Check**: Calculate Cronbach's α for personality scales (using `pingouin` or `scipy`).
2.  **Report**: Log α value. If using synthetic data, log the theoretical value used in generation.

### Phase 3: Statistical Modeling (FR-002, FR-007)
1.  **Mixed-Effects Logistic**: Fit model with fixed effects (Gamification, Conscientiousness, Interaction) and random intercepts.
2.  **Collinearity Check**: Calculate VIF. If > 5, drop secondary trait.
3.  **Multiple Comparison Correction (FR-007)**: Apply Benjamini-Hochberg (FDR) to interaction term p-values.
4.  **LOUO Cross-Validation**: Report average AUC.

### Phase 4: Survival Analysis (FR-003, FR-009)
1.  **Event Count Check (FR-009)**: Count dropout events per group. If < 10, halt survival analysis and output descriptive stats only.
2.  **Kaplan-Meier**: Generate curves stratified by Conscientiousness quartiles.
3.  **Cox PH**: Fit model, report Hazard Ratios.

### Phase 5: Robustness & Reporting (FR-004, FR-005)
1.  **Bootstrapping**: A sufficient number of iterations to generate 95% CI.
2.  **Report Generation**: Create HTML/PDF with visualizations.
3.  **Versioning (Constitution V)**: Run `utils/versioning.py` to hash artifacts and update `state.yaml`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Mixed-Effects Models | Longitudinal data requires handling within-subject correlation. | Standard logistic regression would violate independence assumptions and inflate Type I error. |
| Survival Analysis | "Dropout" is a time-to-event metric (3 consecutive weeks). | Simple adherence rates ignore the timing of dropout and censoring. |
| Bootstrapping | Robustness validation required by SC-004. | Single point estimate does not account for sampling variability in small N. |
| Synthetic Data | No verified longitudinal dataset with personality + logs exists. | Public datasets are cross-sectional (MyPersonality) or lack personality traits. |