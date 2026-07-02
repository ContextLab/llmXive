# Implementation Plan: The Effects of Gamified Habit Tracking on Long-Term Behavioral Change

**Branch**: `001-gamification-effects` | **Date**: 2026-06-24 | **Spec**: `specs/001-the-effects-of-gamified-habit-tracking-o/spec.md`
**Input**: Feature specification from `/specs/001-the-effects-of-gamified-habit-tracking-o/spec.md`

## Summary

The project investigates the association between gamified habit tracking (points/badges/leaderboards) and long‑term adherence, and how this is moderated by personality traits (Conscientiousness, Need for Achievement). Because the MyPersonality dataset is cross‑sectional, the analysis will use a **cross‑sectional logistic regression with interaction terms** and bootstrap‑based robustness checks. All methods are CPU‑only and fit within the free‑tier GitHub Actions constraints.

## Technical Context

- **Language/Version**: Python 3.11  
- **Primary Dependencies**: pandas, numpy, statsmodels, scikit-learn, pyyaml, seaborn, matplotlib  
- **Storage**: Local CSV/Parquet files in `data/` and `data/interim/`  
- **Testing**: pytest (contract validation, unit tests)  
- **Target Platform**: Linux (GitHub Actions free‑tier runner)  
- **Constraints**: No GPU, no deep learning, strict reproducibility, observational framing only.  

> **Dataset Variable Fit Verification**  
> Required columns: `gamified_app_usage` (or equivalent), `habit_tracking_method`, `habit_duration` (or `entry_frequency`), `conscientiousness`, `need_for_achievement` (optional), `user_id`.  
> The pipeline aborts with a **Data Insufficiency** report if any of these are missing.

## Constitution Check

| Principle | Compliance Status | Action / Justification |
|-----------|-------------------|------------------------|
| **I. Reproducibility** | **Compliant** | All code uses pinned versions in `requirements.txt`; random seeds are set globally (`np.random.seed(42); random.seed(42)`). |
| **II. Verified Accuracy** | **Compliant** | Citations reference the verified HuggingFace URL and standard statistical texts. |
| **III. Data Hygiene** | **Compliant** | Raw data stored in `data/raw/` with SHA‑256 checksum; all transformations write new files. |
| **IV. Single Source of Truth** | **Compliant** | Every statistic in the final report is generated programmatically from `data/processed/` and `code/`. |
| **V. Versioning Discipline** | **Compliant** | Content hashes are recorded in the project state file; pipelines fail on hash mismatch. |
| **VI. Ethical Data Handling** | **Compliant** | A `data/consent/` directory is **created during Phase 1** and populated with any consent documentation supplied with the dataset. |
| **VII. Psychometric Validity** | **Compliant** | Cronbach’s α for the Big Five is computed in `code/ingest.py` and reported in the final HTML report (Methods → Psychometrics). |

## Project Structure

### Documentation (this feature)

```text
specs/001-the-effects-of-gamified-habit-tracking-o/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    └── output.schema.yaml
```

### Source Code

```text
projects/PROJ-138-the-effects-of-gamified-habit-tracking-o/
├── data/
│   ├── raw/               # Read‑only parquet
│   ├── processed/         # Cleaned CSV, results JSON
│   ├── interim/           # Bootstrap samples, model artifacts
│   └── consent/           # Populated in Phase 1
├── code/
│   ├── __init__.py
│   ├── config.py          # Paths, seeds, hyper‑parameters
│   ├── ingest.py          # Loading, validation, psychometric checks
│   ├── modeling.py        # Logistic regression, bootstrapping, output generation
│   ├── viz.py             # Plot creation
│   └── main.py            # Orchestration
├── tests/
│   ├── contract/          # Schema validation tests
│   ├── unit/              # Logic tests (e.g., adherence flag)
│   └── integration/       # End‑to‑end test on synthetic data
├── docs/                  # Final report and plots
└── requirements.txt       # Pinned dependencies
```

**Structure Decision**: A single linear pipeline is appropriate; no separate backend/frontend needed.

## Phase Plan

### Phase 0: Research & Feasibility
*Goal: Confirm dataset suitability and define statistical approach.*

1. **Ingest & Inspect**: Load `data/raw/mypersonality.parquet`. Verify presence of required columns (`gamified_app_usage`, `habit_tracking_method`, `habit_duration`, `conscientiousness`, `need_for_achievement` if present). If any are missing, **halt** and generate a “Data Insufficiency” report.
2. **Gap Analysis**: Document any missing variables; if critical columns are absent, flag for spec kick‑back.
3. **Method Selection**: Choose cross‑sectional logistic regression with interaction terms; justify exclusion of mixed‑effects and survival analysis due to lack of longitudinal data.
4. **Output**: Updated `research.md` with dataset strategy and methodological rationale.

### Phase 1: Data Model & Contracts
*Goal: Define schemas, cleaning, and psychometric validation.*

1. **Schema Definition**: `contracts/dataset.schema.yaml` (input) and `contracts/output.schema.yaml` (results).  
2. **Cleaning Logic**: Implement in `code/ingest.py` – creates `Gamified_Binary`, derives `Long_Term_Adherence`, drops rows with missing primary variables. **Validate** the resulting CSV against `dataset.schema.yaml` using `jsonschema`.  
3. **Consent Handling**: Create `data/consent/` and copy any consent PDFs or metadata from the dataset source (per Principle VI).  
4. **Psychometric Check**: Compute Cronbach’s α for the Big Five (or subset) in `ingest.py`; store the value in `data/processed/psychometrics.json` and reference it in the final report (Principle VII).  
5. **Output**: `data-model.md`, `quickstart.md`, contract files.

### Phase 2: Implementation
*Goal: Build the end‑to‑end pipeline.*

1. **Ingestion Script** (`code/ingest.py`): Load, validate, compute reliability metrics, write `cleaned_data.csv`.  
2. **Modeling Script** (`code/modeling.py`):  
   - Fit logistic regression: `long_term_adherence ~ gamified_binary * conscientiousness (+ achievement_score if present)`.  
   - Compute VIF; if VIF > 5 for any moderator, drop the collinear trait (prioritise conscientiousness).  
   - Apply Bonferroni/FDR correction for multiple personality tests.  
   - Perform 5‑fold cross‑validation; report mean AUC.  
   - Run a sufficient number of bootstrap resamples; store effect‑size CI.  
   - Conduct sensitivity analysis over adherence thresholds; report **p‑value stability** (replaces false‑positive rate).  
   - Write results to `data/processed/results.json` **conforming to `output.schema.yaml`**.  
3. **Visualization** (`code/viz.py`): Adherence distribution, interaction plots, bootstrap effect‑size histogram.  
4. **Orchestration** (`code/main.py`): Sequentially run ingestion → modeling → viz → report generation.

### Phase 3: Validation & Reporting
*Goal: Produce a reproducible, standards‑compliant report.*

1. **Robustness**: Execute bootstrapping (1,000 iterations) and sensitivity analysis; ensure runtime < 1 hour.  
2. **Report Generation** (`docs/report.html`):  
   - Methods: dataset description, psychometric reliability, modeling approach, multiple‑comparison correction, power limitation note.  
   - Results: interaction coefficient, CI, p‑value, bootstrap CI, cross‑validation AUC, p‑value stability table.  
   - Visuals: adherence histogram, interaction plot, bootstrap distribution.  
3. **Compliance Check**: Run `pytest` contract tests; ensure all schemas pass.  
4. **Kick‑back Note**: Document that the original spec’s longitudinal requirements and SC‑005 must be revised to align with the cross‑sectional design.

## Compute Feasibility Assessment

- **Memory**: < 200 MB for the raw parquet; ≤ 1 GB during bootstrapping.  
- **CPU**: Logistic regression and bootstrap are fast; total runtime [deferred] on 2‑core runner.
- **No GPU**: All libraries run on CPU.  
- **Risk Mitigation**: Early dataset‑fit check prevents wasted compute.

## Kick‑back Summary (for Spec Authors)

- Replace mixed‑effects logistic regression and survival analysis with cross‑sectional logistic regression.  
- Update SC‑005 to require “p‑value stability” instead of false‑positive rates.  
- Redefine the `Behavioral Log` entity to a single‑row‑per‑user schema.  
- Ensure the spec explicitly notes the cross‑sectional nature of the MyPersonality data.
