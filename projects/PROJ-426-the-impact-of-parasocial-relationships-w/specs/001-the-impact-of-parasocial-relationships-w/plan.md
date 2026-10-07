# Implementation Plan: The Impact of Parasocial Relationships with AI Companions on Loneliness

**Branch**: `001-ai-companion-loneliness-impact` | **Date**: 2026-06-28 | **Spec**: `specs/001-the-impact-of-parasocial-relationships-w/spec.md`
**Input**: Feature specification from `/specs/001-the-impact-of-parasocial-relationships-w/spec.md`

## Summary

This feature implements a longitudinal observational study analyzing the association between AI companion usage and loneliness, controlling for pre-existing emotional coping styles. The technical approach involves ingesting the *Reddit Loneliness Longitudinal Dataset* (Zenodo) and *Pushshift* interaction logs, matching users via cryptographic hashed usernames, engineering features including an 'Emotional Coping Proxy' via the *ECAR Lexicon*, and fitting a linear mixed-effects model with bootstrap resampling. The implementation prioritizes CPU-first execution within GitHub Actions constraints (limited cores, constrained RAM) while strictly adhering to data hygiene and reproducibility principles. The study is contingent on the existence and accessibility of the required datasets.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `statsmodels` (mixed-linear models), `scikit-learn` (bootstrapping), `datasets` (HuggingFace), `requests` (Pushshift API), `pyyaml`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/results`); CSV/Parquet formats.  
**Testing**: `pytest` (unit tests for matching logic, feature extraction; integration tests for pipeline).  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, ~7 GB RAM).  
**Project Type**: Data Science Pipeline / Research Study.  
**Performance Goals**: Complete bootstrap resampling (1,000 iterations) within ≤6 hours; memory footprint <7 GB. Halt if N < 500 or if detectable effect size > 0.8 (power limitation).  
**Constraints**: No local GPU; no access to gated datasets (ADNI, etc.); strict PII handling (hashing only); observational framing only.  
**Scale/Scope**: Target ≥500 matched user records; 6-month longitudinal window.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Evidence / Action Required |
| :--- | :--- | :--- |
| **I. Reproducibility** | **COMPLIANT** | Plan mandates pinned `requirements.txt`, fixed random seeds, and canonical data sources (Zenodo DOI, Pushshift API). All scripts in `code/` are designed for end-to-end re-runs. |
| **II. Verified Accuracy** | **CONDITIONAL** | Compliance is contingent on the successful fetch of the Zenodo dataset. If the dataset is missing or lacks required fields, the plan halts, and Principle II is not applicable. |
| **III. Data Hygiene** | **COMPLIANT** | Plan includes checksumming of raw data, PII exclusion (hashing only), and immutable derivation logs. `data/` directory structure enforces raw vs. processed separation. |
| **IV. Single Source of Truth** | **COMPLIANT** | The `data/processed/matched_users.parquet` is the single source for all model inputs. `data/results/model_summary.json` is the sole source for paper statistics. |
| **V. Versioning Discipline** | **COMPLIANT** | Artifact hashes recorded in `state/` upon generation. Content hashes used to invalidate stale review records. |
| **VI. Longitudinal Analysis Integrity** | **COMPLIANT** | Random intercepts/slopes structure is pre-specified in the plan (FR-005). No post-hoc modification of fixed effects based on significance. |
| **VII. Self-Report Instrument Validation** | **COMPLIANT** | Plan includes a validation step for the UCLA Loneliness Scale (FR-001) checking for completion rates and missing data handling before model fitting. |

## Project Structure

```text
src/
├── __init__.py
├── config.py                # Configuration loading, path constants
├── main.py                  # Pipeline orchestrator
├── ingest/
│   ├── __init__.py
│   ├── fetch_zenodo.py      # Download & checksum Zenodo dataset
│   ├── fetch_pushshift.py   # Retry logic, API interaction
│   └── merge_sources.py     # Join logic
├── match/
│   ├── __init__.py
│   └── user_match.py        # SHA-256 hashing & matching logic
├── features/
│   ├── __init__.py
│   ├── attachment_proxy.py  # Emotional Coping Proxy scoring
│   └── usage_metrics.py     # Frequency & duration aggregation
├── models/
│   ├── __init__.py
│   ├── mixed_effects.py     # LME fitting & diagnostics
│   └── bootstrap.py         # Resampling logic
├── validation/
│   ├── __init__.py
│   ├── validate_match.py    # Verify match rates & PII safety
│   └── validate_data.py     # Schema & completeness checks
├── utils/
│   ├── __init__.py
│   ├── retry_policy.py      # Exponential backoff for API
│   └── logging.py
└── analysis/
    ├── __init__.py
    ├── power_analysis.py    # Power calculation
    ├── subgroup_analysis.py # Age ≥ 60 analysis
    └── bias_analysis.py     # Selection bias check

tests/
├── __init__.py
├── unit/
│   ├── test_user_match.py
│   └── test_attachment_proxy.py
├── integration/
│   └── test_pipeline.py
└── contract/
    └── test_schemas.py

data/
├── raw/                     # Downloaded Zenodo/Pushshift (immutable)
├── processed/               # Matched users, engineered features
└── results/                 # Model outputs, plots

docs/
├── constitution.md
└── methodology.md

contracts/
├── dataset.schema.yaml
├── model_output.schema.yaml
└── unified_dataset.schema.yaml
```

**Structure Decision**: Single project structure (`src/`) selected to facilitate tight integration between data ingestion, feature engineering, and statistical modeling within the constrained CI environment. This minimizes import overhead and simplifies dependency management for the `statsmodels` and `pandas` heavy pipeline.

## Implementation Phases

### Phase 0: Data Feasibility & Validation
- **0a: Lexicon Validation**: Check for the ECAR Lexicon. If missing/invalid, halt with "Lexicon Missing" error (FR-008).
- **0b: Dynamic Window Calculation**: Extract the earliest and latest survey timestamps from the Zenodo dataset to define the exact calendar window for Pushshift log retrieval (FR-002).
- **0c: Instrument Validation**: Validate the UCLA Loneliness Scale for completion rates and missing data handling (Constitution Principle VII).
- **0d: Dataset Fetch**: Download the Zenodo dataset and Pushshift logs. If the Zenodo dataset is missing or lacks required fields (`username`, `baseline_text`), halt with "Data Linkage Impossible" error.

### Phase 1: Data Processing & Matching
- **1a: Match Rate Calculation**: Match users via SHA-256 hashed usernames. Calculate and report the match rate. If < 80%, halt with "Power Insufficient" error (SC-001).
- **1b: Power Analysis**: If N < 500, calculate the detectable effect size (Cohen's d). If d > 0.8, halt with "Power Limitation" warning.
- **1c: Selection Bias Analysis**: Compare demographics of excluded users (missing text) to included users to assess selection bias.
- **1d: Feature Engineering**: Compute weekly usage metrics and extract the 'Emotional Coping Proxy' from baseline posts. Exclude users with missing text (FR-004b).

### Phase 2: Model Fitting
- **2a: Baseline Model Comparison**: Fit an intercept-only model and calculate the marginal R² (SC-002).
- **2b: Primary Model Fitting**: Fit the LMM with random intercepts and slopes. If convergence fails, fall back to random-intercept-only model and log a warning (Methodology Concern).
- **2c: Bootstrap Resampling**: Perform 1,000 bootstrap iterations to generate robust 95% CIs (FR-006).

### Phase 3: Subgroup & Robustness
- **3a: Subgroup Analysis (Age ≥ 60)**: Fit a separate model for users aged ≥ 60 (FR-007).
- **3b: Diagnostic Checks**: Check for normality, homoscedasticity, and collinearity.
- **3c: Result Aggregation**: Compile all results into `data/results/model_summary.json`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Bootstrap Resampling (1,000 iters)** | Required by FR-006 for robust CIs. | Standard asymptotic CIs are unreliable for mixed-effects models with small N or non-normal residuals; simulation-based inference is necessary. |
| **Pushshift Retry Policy** | Required by Edge Case handling. | Simple linear retry fails against rate limits; exponential backoff is standard for API resilience. |
| **Attachment Proxy (Lexicon)** | Required by FR-004 to control for confounding. | Imputing neutral scores (FR-004b) would introduce bias; excluding users is the only valid statistical control. |
| **Dynamic Window Calculation** | Required by FR-002. | Static window would not align with the survey dates, violating the lagged structure. |
| **Power Analysis** | Required by Assumptions. | Running on an underpowered sample would produce unreliable results. |
| **Selection Bias Analysis** | Required by Scientific Soundness. | Excluding users with missing text creates a selection bias that must be assessed. |
| **Model Convergence Fallback** | Required by Scientific Soundness. | Random-slope models often fail to converge on sparse data; a fallback ensures results are produced. |