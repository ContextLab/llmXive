# Implementation Plan: The Impact of Simulated Social Feedback on Self-Esteem Fluctuations

**Branch**: `001-the-impact-of-simulated-social-feedback-on-self-esteem-fluctuations` | **Date**: 2026-07-20 | **Spec**: `specs/001-the-impact-of-simulated-social-feedback-on-self-esteem-fluctuations/spec.md`
**Input**: Feature specification from `/specs/001-the-impact-of-simulated-social-feedback-on-self-esteem-fluctuations/spec.md`

## Summary

This project implements a computational pipeline to analyze social media interactions to determine if the *temporal volatility* of feedback (rate of change in sentiment) predicts the *Self-Esteem Indicator* (a lexicon-derived score from the user's own posts) more strongly than the *overall valence* of the feedback. The approach involves ingesting raw interaction data from the verified `pushshift_reddit` dataset, applying a pre-trained RoBERTa model for sentiment scoring, calculating rolling-window volatility metrics for replies, and running a multiple linear regression. Crucially, the model includes a control for the user's own post valence to statistically isolate the effect of feedback volatility from simple "social mirroring" (reciprocity), addressing the methodological concern that positive replies might merely predict positive posts.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `transformers` (CPU-optimized), `torch` (CPU-only), `datasets` (HuggingFace), `requests`, `tqdm`, `pydantic` (for schema validation)  
**Storage**: Local CSV/Parquet files (`data/raw/`, `data/processed/`)  
**Testing**: `pytest` (unit tests for metrics, integration tests for pipeline)  
**Target Platform**: Linux (GitHub Actions free-tier runner: multiple CPUs, substantial RAM)  
**Project Type**: Data Analysis Pipeline / Research Script  
**Performance Goals**: Complete full pipeline in < 6 hours on CPU; memory usage < 6GB.  
**Constraints**: No GPU access for model inference (CPU-only RoBERTa); strict adherence to data privacy (no PII in output); statistical validity (VIF < 5.0).  
**Scale/Scope**: Processing a substantial volume of interactions (estimated from source); generating final regression and sensitivity analysis reports.

## Constitution Check

*Gates determined based on `projects/PROJ-384-the-impact-of-simulated-social-feedback-/memory/constitution.md`*

| Principle | Status | Compliance Strategy |
|-----------|--------|---------------------|
| **I. Reproducibility** | **COMPLIANT** | All random seeds pinned in `code/utils.py`. External datasets fetched via fixed URLs (`pushshift_reddit` on HuggingFace). `requirements.txt` pins exact versions. |
| **II. Verified Accuracy** | **COMPLIANT** | Dataset URLs cited only from the verified block (`pushshift_reddit`). Model architecture (RoBERTa) cited from verified source. No fabricated URLs. |
| **III. Data Hygiene** | **COMPLIANT** | Raw data downloaded to `data/raw/` with checksum verification. Derived files (CSV/Parquet) written to `data/processed/` with new filenames. No in-place modification. |
| **IV. Single Source of Truth** | **COMPLIANT** | All statistics in the final report will be generated directly from the `statsmodels` output objects, not hand-typed. |
| **V. Versioning Discipline** | **COMPLIANT** | Content hashes for code and design docs are recorded in the state file *before* review. The Advancement-Evaluator Agent invalidates stale review records when the hashed artifact changes, ensuring versioning discipline is enforced pre-commit. |
| **VI. Distinct Actor Separation** | **COMPLIANT** | Code logic explicitly separates `post_text` (outcome source) from `reply_text` (predictor source). The regression model includes `post_valence` as a covariate to control for reciprocity, ensuring the `volatility` coefficient measures the unique impact of feedback dynamics on the self-esteem indicator. |
| **VII. Valence vs. Dynamics Isolation** | **COMPLIANT** | Regression model includes both `mean_reply_valence` and `reply_volatility` as distinct predictors. Sensitivity analysis (FR-006) explicitly tests stability of the volatility coefficient. |

## Project Structure

### Documentation (this feature)

```text
specs/001-the-impact-of-simulated-social-feedback-on-self-esteem-fluctuations/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
```

### Source Code (repository root)

```text
code/
├── 01_ingest.py           # Downloads pushshift_reddit, parses raw text, validates against interaction_schema.schema.yaml (hard gate), applies RoBERTa sentiment
├── 02_metrics.py          # Calculates rolling volatility and sign-change frequency for replies; calculates Self-Esteem Indicator from posts
├── 03_analysis.py         # Runs regression (controlling for post_valence), VIF checks, sensitivity analysis
├── 04_report.py           # Generates final PDF/Markdown report
├── utils/
│   ├── config.py          # Paths, seeds, thresholds
│   └── logger.py          # Logging setup
├── tests/
│   ├── test_metrics.py    # Unit tests for volatility calculations
│   └── test_ingest.py     # Unit tests for data parsing and schema validation
└── requirements.txt       # Pinned dependencies
```

**Structure Decision**: Single Python package structure (`code/`) with modular scripts for each pipeline stage. This ensures linear execution order (Ingest -> Metrics -> Analysis -> Report) and facilitates isolated testing of each stage. `01_ingest.py` MUST validate the raw data against `contracts/interaction_schema.schema.yaml` at runtime as a hard gate.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Sentiment Model on CPU** | Requires `transformers` + `torch` for RoBERTa inference. | A simple rule-based sentiment analyzer (e.g., VADER) was rejected because the spec requires a "pre-trained RoBERTa-based model fine-tuned on social media text" for validity (Assumption II). |
| **Self-Esteem Lexicon** | FR-004 mandates a validated self-esteem indicator. | Using raw post sentiment as the outcome was rejected because it conflates "mood" with "self-esteem" and fails to address the "social mirroring" concern without a distinct construct. |
| **Reciprocity Control** | To address the methodological concern that positive replies predict positive posts. | A simple regression of volatility on self-esteem was rejected because it would capture the general reciprocity effect; the model must control for `post_valence` to isolate the specific effect of *volatility*. |
| **Sensitivity Analysis** | FR-006 requires re-running regression for a range of window sizes. | Running only the primary window (5) was rejected because the hypothesis relies on the *stability* of the volatility effect, not just a single point estimate. |
| **VIF Check** | SC-005 requires VIF < 5.0. | Standard regression without collinearity checks was rejected because predictor variables (mean valence vs. volatility) may be mathematically correlated, risking spurious results. |
| **Schema Validation** | Constitution Principle III & IV require data integrity. | Skipping schema validation was rejected because the pipeline must halt if the dataset structure changes, preventing silent data corruption. |