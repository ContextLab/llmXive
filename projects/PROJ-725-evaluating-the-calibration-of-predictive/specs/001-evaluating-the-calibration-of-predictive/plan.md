# Implementation Plan: Evaluating the Calibration of Predictive Uncertainty Intervals in Public Regression Benchmarks

**Branch**: `001-evaluating-the-calibration` | **Date**: 2026-06-17 | **Spec**: `specs/001-evaluating-the-calibration/spec.md`

## Summary

This feature implements a rigorous statistical pipeline to evaluate the calibration of predictive uncertainty intervals across four distinct methods (Quantile Regression, Bayesian Linear Regression, Gaussian Process Regression, and Split Conformal Prediction) on public regression benchmarks. The pipeline will download datasets, generate prediction intervals, and perform hypothesis testing (Beta-Binomial, permutation) to assess empirical coverage against nominal targets, while accounting for heteroscedasticity and sensitivity to threshold definitions.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn`, `statsmodels`, `pandas`, `numpy`, `scipy`, `datasets` (Hugging Face), `openml`, `pyyaml`  
**Storage**: Local filesystem (`data/` for raw/processed data, `artifacts/` for results)  
**Testing**: `pytest` (unit tests for interval logic, integration tests for pipeline flow)  
**Target Platform**: Linux (GitHub Actions Free Tier: Multi-core CPU, ~7 GB RAM, ~ GB Disk)  
**Project Type**: Data Science CLI / Research Pipeline  
**Performance Goals**: Complete analysis of ~10 public regression datasets within 6 hours; individual method fits < 15 mins; memory < 7 GB.  
**Constraints**: CPU-only execution; no GPU fallback required for these specific methods (GP exact inference on small data, sklearn estimators); strict adherence to / split; fixed random seeds.  
**Scale/Scope**: Target of multiple public regression datasets (selected dynamically from OpenML with verified regression targets); Multiple methods per dataset; variance bins; sensitivity thresholds. *Fallback: If fewer than a sufficient number of valid datasets are found, the study proceeds with the available subset as a descriptive benchmark, and the permutation test is skipped or adjusted accordingly.*

> Domain-specific empirical specifics (exact dataset counts, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action/Mapping in Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates fixed seeds in `code/`, pinned `requirements.txt`, and raw data checksums. |
| **II. Verified Accuracy** | **PASS** | Plan restricts dataset sources to the OpenML registry. The **Reference-Validator Agent** runs a metadata check against the primary OpenML source to confirm the task type is regression and the target is continuous *before* the dataset is added to the pipeline. This includes a title-token-overlap check against the primary source metadata to satisfy the verification requirements. |
| **III. Data Hygiene** | **PASS** | Plan enforces read-only raw data, checksummed artifacts, and no in-place modification. |
| **IV. Single Source of Truth** | **PASS** | All metrics (coverage, interval score) derived from `data/` artifacts; no hand-typed stats. |
| **V. Versioning Discipline** | **PASS** | Plan includes content hashing for all output schemas and data artifacts. Specifically, the **Advancement-Evaluator Agent** updates `state.yaml` with the content hash of every new artifact (including the Beta-Binomial dispersion parameters and variance model weights) to invalidate stale review records upon any change. |
| **VI. Calibration Fidelity** | **PASS** | Plan explicitly implements the ±2% deviation flag and Beta-Binomial test for every method-dataset pair. |
| **VII. Heteroscedasticity-Aware** | **PASS** | Plan includes a dedicated phase for independent variance modeling and stratified bin coverage analysis. |

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-the-calibration/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── prediction_interval.schema.yaml
│   └── result.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── main.py              # Entry point (CLI)
├── config.py            # Hyperparameters, seeds, paths
├── data/
│   ├── __init__.py
│   ├── loader.py        # Download & stream datasets from OpenML/HF
│   └── preprocessor.py  # Split, clean, validate
├── models/
│   ├── __init__.py
│   ├── base.py          # Abstract UncertaintyMethod
│   ├── quantile.py      # Quantile Regression (sklearn + GBT)
│   ├── bayesian.py      # Bayesian Linear Regression
│   ├── gaussian.py      # Gaussian Process (sklearn.gaussian_process)
│   ├── conformal.py     # Split Conformal Prediction
│   └── variance.py      # Robust Baseline Variance Model
├── analysis/
│   ├── __init__.py
│   ├── metrics.py       # Coverage, Interval Score, Width
│   ├── tests.py         # Beta-Binomial, Permutation, Sensitivity
│   └── heteroscedasticity.py  # Stratification logic
├── utils/
│   ├── __init__.py
│   ├── logging.py
│   └── checksum.py
└── output/
    └── reporter.py      # CSV/JSON generation

tests/
├── __init__.py
├── test_metrics.py
├── test_loader.py
└── test_pipeline.py
```

**Structure Decision**: Single-project structure (`code/`) chosen for simplicity and direct alignment with the research pipeline nature. No frontend/backend split required.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Four distinct UQ methods** | Required by FR-002 to compare different theoretical approaches (frequentist vs. Bayesian vs. conformal). | Using only one method would fail to answer the comparative research question. |
| **Heteroscedasticity Stratification** | Required by FR-006 and Constitution Principle VII to detect conditional mis-calibration. | Global coverage alone masks failures in high-variance regions. |
| **Permutation Tests** | Required by FR-005 for pairwise comparisons at small N (n=10 datasets). | Standard parametric tests (t-test/Wilcoxon) assumptions are violated with such small sample sizes. |
| **Sensitivity Sweep** | Required by FR-007 to defend against threshold cherry-picking. | A single threshold (±2%) is arbitrary; robustness must be demonstrated. |
| **Beta-Binomial Test** | Required to handle over-dispersion in prediction errors and avoid inflated Type I errors (Methodology R1). | Standard Binomial Test assumes i.i.d. errors, which is often violated in regression, leading to invalid p-values. |
| **Independent Variance Model** | Required to avoid circular dependency in heteroscedasticity analysis (Methodology R1). | Using residuals from the primary method to define strata contaminates the validation metric. |