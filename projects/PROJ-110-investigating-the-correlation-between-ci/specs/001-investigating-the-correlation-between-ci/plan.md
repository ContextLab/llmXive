# Implementation Plan: Investigating the Correlation Between Circadian Gene Expression and Metabolic Syndrome Risk

**Branch**: `001-circadian-metabolic-correlation` | **Date**: 2026-10-27 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-circadian-metabolic-correlation/spec.md`

## Summary

This feature implements a statistical pipeline to investigate the association between **static** expression levels of circadian genes and Metabolic Syndrome (MetS) using the GTEx v dataset. Due to the lack of time-of-day metadata in GTEx, the hypothesis is reframed from 'circadian expression' to 'static expression differences'. The system classifies donors into MetS/Control groups based on ATP-III criteria, performs differential expression analysis (Wilcoxon) with FDR correction, builds a multivariate logistic regression model with covariates (age, sex, tissue), and generates diagnostic plots (ROC, Heatmap, Exploratory Scatter). The implementation strictly adheres to the project constitution regarding reproducibility, data hygiene, and statistical rigor, running entirely on CPU-tractable methods suitable for the GitHub Actions free tier.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: pandas, numpy, scipy, statsmodels, scikit-learn, matplotlib, seaborn, pyyaml  
**Storage**: Local file system (`data/raw`, `data/processed`), Parquet/TSV formats  
**Testing**: pytest (unit tests for classification logic, integration tests for pipeline flow)  
**Target Platform**: Linux (GitHub Actions Runner)  
**Project Type**: Data Science Pipeline / Statistical Analysis  
**Performance Goals**: Complete analysis within 6 hours on 2 CPU cores, <7 GB RAM.  
**Constraints**: CPU-only execution; no GPU acceleration; strict adherence to ATP-III thresholds; handling of missing data via exclusion.  
**Scale/Scope**: GTEx dataset (large-scale cohort, but filtered by phenotype availability); A core set of circadian genes.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Compliance Status | Evidence/Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | `requirements.txt` pins versions; random seeds set in `code/`; data fetched from canonical HuggingFace URLs. |
| **II. Verified Accuracy** | **Pass** | All dataset URLs cited from the "Verified datasets" block; title-token-overlap check (threshold) implemented in `downloader.py`. |
| **III. Data Hygiene** | **Pass** | Plan includes `data/raw` (checksummed) and `data/processed` (derived) separation. No in-place modifications. |
| **IV. Single Source of Truth** | **Pass** | All statistics in `paper/` will trace to `data/processed` via `code/`. |
| **V. Versioning Discipline** | **Pass** | `code/utils.py` generates hashes after download (T016) and processing (T017), updating `state/` manifest before next phase. |
| **VI. Clinical Criteria** | **Pass** | MetS classification strictly follows ATP-III (BMI≥30, Glu≥100, TG≥150, BP≥130/85, HDL<40/34). |
| **VII. Statistical Correction** | **Pass** | Benjamini-Hochberg FDR applied to all DE tests; k-fold cross-validation for logistic regression. |

## Tasks.md Status

The `tasks.md` file exists in the repository root (generated in Phase 0). It currently lists T036 (Collinearity/VIF), T037 (ROC plot), and T038 (Heatmap) as unimplemented. This revision defines the implementation logic for these tasks in the 'Implementation Phases' section below.

## Project Structure

### Documentation (this feature)

```text
specs/001-circadian-metabolic-correlation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Schemas)
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-110-investigating-the-correlation-between-ci/
├── data/
│   ├── raw/             # Downloaded GTEx/TCGA files (checksummed)
│   └── processed/       # Cleaned labels, expression matrices, model outputs
├── code/
│   ├── __init__.py
│   ├── data/
│   │   ├── downloader.py        # Fetches GTEx/TCGA data, verifies titles
│   │   ├── classifier.py        # Implements ATP-III logic, stores baseline_labels.csv
│   │   └── utils.py             # Log handling, missing data exclusion, hashing
│   ├── analysis/
│   │   ├── differential.py      # Wilcoxon tests, FDR correction
│   │   ├── modeling.py          # Logistic regression, CV, VIF check
│   │   └── correlations.py      # Spearman/Pearson correlation matrix
│   ├── viz/
│   │   ├── plots.py             # ROC, Heatmap, Scatter plots (FR-008)
│   │   └── diagnostics.py       # VIF plots, residual checks
│   └── main.py                  # Pipeline orchestrator
├── tests/
│   ├── unit/
│   │   ├── test_classifier.py   # Tests US-01 logic (ATP-III)
│   │   └── test_stats.py        # Tests FDR and VIF logic
│   └── integration/
│       └── test_pipeline.py     # End-to-end run check
├── docs/
│   └── api.md
└── requirements.txt
```

**Structure Decision**: Selected the "Single Project" structure (Option 1) with a clear separation of `data`, `code` (split by functional domain), and `tests`. This aligns with the need for a linear statistical pipeline and ensures modularity for unit testing the specific logic in `classifier.py` (US-01) and `differential.py` (US-02).

## Implementation Phases

### Phase 0: Data Acquisition & Validation
*   **T016**: `code/data/downloader.py` fetches GTEx v8 data. Performs title-token-overlap check (threshold defined by prior literature) against primary source.
*   **T017**: `code/utils.py` generates SHA256 hashes for raw files and updates `state/` manifest.
*   **T018**: `code/data/classifier.py` validates columns (BMI, Glucose, BP, TG, HDL). If missing, attempts GTEx Portal fallback or triggers 'Exploratory' mode.

### Phase 1: Classification & Pre-processing
*   **T019**: Apply ATP-III criteria. Exclude samples with missing data. Log exclusions.
*   **T020**: If N < 100, calculate 'Partial Criteria Score' and switch to Linear Regression fallback.
*   **T021**: `code/utils.py` hashes processed `baseline_labels.csv` and updates `state/`.

### Phase 2: Statistical Analysis
*   **T036**: **Collinearity/VIF**. `code/analysis/modeling.py` calculates VIF for all predictors. Stores values in `logistic_regression.csv`. Flags if > 5.
*   **T022**: **Differential Expression**. Wilcoxon rank-sum tests (Static Expression) per tissue. FDR correction.
*   **T023**: **Predictive Modeling**. Logistic Regression (or Linear if fallback) with k-fold CV.
*   **T024**: **Correlation Analysis**. Spearman correlation. Generates exploratory scatter plots.

### Phase 3: Visualization & Reporting
*   **T037**: **ROC Plot**. `code/viz/plots.py` generates ROC curve for model performance.
*   **T038**: **Heatmap**. `code/viz/plots.py` generates heatmap of significant genes.
*   **T025**: **Scatter Plots**. `code/viz/plots.py` generates scatter plots for continuous traits (labeled 'Exploratory').
*   **T026**: Generate `sensitivity_analysis.csv` for SC-005.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Separate `data/raw` vs `data/processed`** | Constitution Principle III (Data Hygiene) requires raw data to be preserved unchanged. | Merging raw and processed data violates reproducibility and makes re-running with different cleaning logic impossible. |
| **Explicit VIF Diagnostics (T036)** | FR-005 and US-03 require detection of collinearity to avoid claiming independent effects for definitionally related predictors. | Skipping VIF checks risks invalid statistical inference; the spec explicitly mandates this diagnostic. |
| **Stratified Analysis by Tissue** | GTEx contains multiple tissue types; biological variance differs significantly. | Aggregating all tissues would introduce massive batch effects and confound the metabolic signal. |
| **Exploratory Scatter Plots (T025)** | FR-008 requires scatter plots. | Generating plots for tautological traits without a caveat would be scientifically unsound. The plan explicitly labels them as 'Exploratory'. |