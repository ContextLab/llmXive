# Implementation Plan: The Effects of Gamified Habit Tracking on Long-Term Behavioral Change

**Branch**: `001-gamification-effects` | **Date**: 2026-06-24 | **Spec**: `specs/001-the-effects-of-gamified-habit-tracking-o/spec.md`
**Input**: Feature specification from `/specs/001-the-effects-of-gamified-habit-tracking-o/spec.md`

## Summary
This project implements a **Simulation Study** pipeline to validate the statistical methodology for detecting the efficacy of gamified habit-tracking elements (points, badges) on long-term adherence, moderated by personality traits (Conscientiousness, Need for Achievement). 
**Crucial Scope Note**: Because no open longitudinal dataset exists with both personality traits and gamified habit logs, this study does **not** attempt to discover a real-world empirical effect. Instead, it validates the **methodology** (mixed-effects models, survival analysis) by generating synthetic data with **known ground-truth parameters** (random assignment, defined interaction effects) and verifying the pipeline can accurately **recover** these parameters. The research question is reframed to: *"Can the statistical pipeline accurately recover known moderation effects in a simulated RCT-style environment?"*

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `statsmodels` (mixed-effects, survival), `scikit-learn` (cross-validation), `seaborn`/`matplotlib` (plotting), `pyyaml` (parsing), `jsonschema` (runtime validation), `numpy`, `lifelines` (survival)  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/reports`)  
**Testing**: `pytest` (unit tests for data ingestion logic, model convergence checks, parameter recovery)  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, 7GB RAM)  
**Project Type**: Data Science / Statistical Analysis Pipeline (Simulation Study)  
**Performance Goals**: Complete full pipeline (ingestion to report) within 6 hours on CPU; memory usage < 6GB.  
**Constraints**: CPU-first execution; no GPU required for classical statistics; strict adherence to "3 consecutive weeks" dropout definition; minimum 100 valid user records (target N=500 for power) required to proceed.  
**Scale/Scope**: A simulated dataset of user records; approximately one year of simulated data per user.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action Required |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All scripts will include `random.seed(42)` and `requirements.txt` pins. Synthetic generator logic is the SSoT for behavioral patterns. |
| **II. Verified Accuracy** | **PASS** | For synthetic data, the `synthetic_generator.py` code is the verified source of truth. For personality distributions, the Hugging Face dataset card is the verified source. |
| **III. Data Hygiene** | **PASS** | Raw data checksummed; derivations written to new files (`data/processed/`). |
| **IV. Single Source of Truth** | **PASS** | All stats in report derived programmatically from `data/processed/merged_data.csv`. |
| **V. Versioning Discipline** | **PASS** | `state.yaml` will be updated with content hashes of final artifacts. |
| **VI. Ethical Data Handling** | **PASS** | Pipeline requires `data/consent/` directory. For the public MyPersonality dataset, the Hugging Face license and dataset card serve as the verified consent record. |
| **VII. Psychometric Validity** | **PASS** | Cronbach's α calculated for personality scales; validated scales (Big Five) used. |

## Project Structure

### Documentation (this feature)

```text
specs/001-gamification-effects/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── model_output.schema.yaml
    └── report.schema.yaml
```

### Source Code (repository root)

```text
code/
├── data/
│   ├── ingestion.py          # FR-001: Load, validate, aggregate
│   ├── synthetic_generator.py # FR-001: Generate test data (Ground Truth)
│   └── consent_checker.py    # FR-010: Verify consent artifacts
├── analysis/
│   ├── modeling.py           # FR-002: Mixed-effects, VIF check
│   ├── survival.py           # FR-003: KM, Cox, Log-rank
│   ├── robustness.py         # FR-004: Bootstrapping, LOO-CV
│   └── psychometrics.py      # FR-011: Cronbach's α calculation
├── reporting/
│   ├── report_generator.py   # FR-005: HTML/PDF generation
│   └── sensitivity.py        # FR-005: Threshold stability
├── utils/
│   ├── versioning.py         # FR-033: Hashing artifacts
│   └── config.py             # Constants (MIN_RECORDS, etc.)
└── main.py                   # Orchestration script

data/
├── raw/                      # Downloaded/Synthetic raw data
├── consent/                  # Consent documentation (required)
├── processed/                # Merged, aggregated data
└── reports/                  # Final HTML/PDF reports

tests/
├── unit/
├── integration/
└── contract/
```

**Structure Decision**: Single project structure selected to align with the statistical pipeline nature of the work. No separate frontend/backend required. `code/` contains all logic; `data/` contains all artifacts.

**Data Flow Traceability**:
1.  `code/data/synthetic_generator.py` generates `data/raw/synthetic_data.csv` (Behavioral Log Daily).
2.  `code/data/ingestion.py` aggregates this to `data/processed/merged_data.csv` (Weekly Aggregation).
3.  `code/analysis/modeling.py` and `survival.py` consume `merged_data.csv`.
4.  `code/reporting/report_generator.py` produces `data/reports/final_analysis.html`.

## Task List (Execution Order)

The following tasks map directly to Functional Requirements (FR) and Success Criteria (SC).

- [ ] **T001**: Setup environment and install dependencies (`requirements.txt`).
- [ ] **T002**: Verify consent artifacts (`data/consent/`).
- [ ] **T003**: Run `synthetic_generator.py` to create `data/raw/synthetic_data.csv` (N=500, Random Assignment).
- [ ] **T004**: Run `ingestion.py` to validate schema and aggregate to weekly bins.
- [ ] **T005**: Validate total records ≥ 100 (FR-001) and non-gamified group ≥ 30 (FR-008). **(T014)**
- [ ] **T006**: Calculate Cronbach's α for personality scales (FR-011). **(T011)**
- [ ] **T007**: Calculate VIF for predictors. If VIF > 5, drop lower-priority trait (FR-002). **(T021)**
- [ ] **T008**: Fit Mixed-Effects Logistic Regression using random-slope syntax `(gamified_status | user_id)` to resolve collinearity (FR-002). **(T020)**
- [ ] **T009**: Apply Benjamini-Hochberg (FDR) correction to interaction terms (FR-007). **(T023)**
- [ ] **T010**: Count dropout events. If < 10 per group, halt p-value calculation (FR-009). **(T024)**
- [ ] **T011**: Perform Survival Analysis (KM/Cox) if event threshold met (FR-003).
- [ ] **T012**: Run Bootstrapping (1000 iterations) and LOO-CV (FR-004).
- [ ] **T013**: Generate sensitivity analysis for adherence thresholds (FR-005).
- [ ] **T014**: Generate Final Report with visualizations (FR-005).
- [ ] **T015**: Hash artifacts and update `state.yaml` (FR-033).

**Dependency Note**: T008 (Model Fit) MUST strictly follow T007 (VIF Check) because T007 determines the final set of predictors passed to the model. T007 must complete before T008 begins.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Mixed-Effects Model (Random Slope) | Required for repeated measures and to separate between-subject fixed effects from random intercepts | Standard logistic regression ignores within-user correlation; Random Intercept-only models fail to identify between-subject group effects (gamified_status) due to collinearity. |
| Survival Analysis (Cox/KM) | Required to model "time-to-dropout" (3 consecutive weeks) | Binary classification cannot capture the temporal dynamics of dropout events. |
| Bootstrapping | Required for robustness (FR-004) | Single point estimates do not capture variance in small/medium samples. |
| Simulation Design | Required due to lack of open longitudinal data with personality + gamification | Real-world observational data would require complex confounding adjustments (IV, PSM) which are not feasible without a valid instrument. Simulation allows controlled validation of the *method*. |

## Power Analysis Justification
To address the concern of sample size adequacy for detecting interaction effects:
- **Target Effect Size**: Interaction effect size (f²) = 0.15 (medium).
- **Power**: [deferred] (0.80).
- **Alpha**: 0.05.
- **Test**: Mixed-Effects Logistic Regression (approximated by G*Power for logistic regression).
- **Result**: N ≈ 450-500 users required.
- **Decision**: The pipeline will generate **N=500** users to ensure adequate power for the simulation recovery test.

