# Implementation Plan: Investigating the Correlation Between Gut Microbiome Composition and Cognitive Function in Aging Using UK Biobank Data

**Branch**: `001-gut-microbiome-cognitive` | **Date**: 2025-01-10 | **Spec**: `specs/001-gut-microbiome-cognitive/spec.md`
**Input**: Feature specification from `/specs/001-gut-microbiome-cognitive/spec.md`

## Summary

This project implements a computational pipeline to investigate associations between gut microbiome composition (16S rRNA sequencing) and cognitive function in aging, utilizing UK Biobank data. The technical approach involves downloading and preprocessing microbiome and cognitive data, filtering for antibiotic use and missingness, applying Isometric Log-Ratio (ILR) transformation to handle compositional constraints, and fitting multivariate linear models with confounder control (age, sex, BMI, diet, activity, medication). The analysis includes Benjamini-Hochberg correction for multiple testing, interaction analysis for age-dependency, and sensitivity checks for over-control bias. All analysis is designed to run on CPU-only CI resources.

## Technical Context

**Language/Version**: Python 3.10  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `seaborn`, `matplotlib`, `pyarrow`, `requests`, `zCompositions` (for zero-replacement), `huggingface_hub` (mock testing only)  
**Storage**: Local temporary files (streamed/processed in batches), output Parquet/CSV/JSON in `data/` and `results/`  
**Testing**: `pytest` (unit tests for data transformation, integration tests for pipeline steps)  
**Target Platform**: Linux (GitHub Actions free-tier runner: limited CPU, limited RAM, ~ GB disk, no GPU)  
**Project Type**: Data analysis / Computational biology pipeline  
**Performance Goals**: Complete end-to-end analysis within 6 hours; memory usage < 7 GB via streaming/sampling; no GPU utilization.  
**Constraints**: No deep learning models; no 8-bit/4-bit quantization; no CUDA; strict handling of compositional data (ILR); explicit causal disclaimer (`causality_claim: false`).  
**Scale/Scope**: UK Biobank cohort (subset with both microbiome and cognitive data); genus-level taxonomy; multiple cognitive metrics; multiple confounders.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **Reproducibility**: Plan mandates pinned `requirements.txt`, random seed setting in code, and streaming data fetching from canonical sources. Intermediate files are processed and removed to ensure clean reruns.
2.  **Verified Accuracy**: The plan explicitly restricts dataset sources to those verified in the `research.md` section. Citations for cognitive instruments (UK Biobank tests) and ILR methodology will be validated against primary sources. **Task Added**: Explicit retrieval and validation of cognitive instrument validation papers (FR-009) before analysis.
3.  **Data Hygiene**: Raw data will be checksummed upon download. Transformations (filtering, ILR) will produce new files with documented derivation. PII checks are enforced via repository hygiene.
4.  **Single Source of Truth**: All figures and statistics will be generated programmatically from `data/` artifacts and `code/` scripts. No hand-typed values in reports.
5.  **Versioning**: Content hashes will be recorded for all data artifacts. **Explicitly mapped** to the `state` file path `projects/PROJ-354-investigating-the-correlation-between-gu/state/projects/PROJ-354-investigating-the-correlation-between-gu.yaml` and the `artifact_hashes` map, ensuring traceability for Principle V.
6.  **Compositional Data Analysis Integrity**: The plan explicitly requires ILR transformation (FR-003) before any statistical modeling. **Mapping**: ILR is explicitly identified as the "equivalent compositional data method" satisfying Constitution Principle VI, as it produces orthonormal coordinates that break the sum-to-zero constraint, making standard linear regression valid.
7.  **Confounder Control Rigor**: The linear models (FR-004) are mandated to include age, sex, BMI, diet, activity, and medication. A sensitivity analysis (FR-010) will compare full vs. reduced models to assess over-control. **Clarification**: Diet/Medication control is framed as mediation analysis to address collider bias risks.

## Project Structure

### Documentation (this feature)

```text
specs/001-gut-microbiome-cognitive/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── results.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Paths, seeds, constants
├── download.py          # Data fetching scripts
├── preprocess.py        # Filtering, ILR transformation, zero-replacement
├── analysis.py          # Lasso/Ridge models, BH correction, interaction tests
├── visualize.py         # Manhattan plots, sensitivity analysis
├── power_analysis.py    # Synthetic dataset generation and power validation
└── main.py              # Orchestration script

data/
├── raw/                 # Downloaded raw data (checksummed)
├── processed/           # ILR-transformed, filtered data
└── interim/             # Temporary batch files

results/
├── associations/        # AssociationResult tables
├── plots/               # Generated figures
├── sensitivity/         # Sensitivity analysis outputs (Threshold Sweep Report)
└── power/               # Power analysis reports

tests/
├── test_preprocess.py
├── test_analysis.py
├── test_power.py        # Tests for synthetic dataset generation
└── test_integration.py
```

**Structure Decision**: Single project structure (`code/`, `data/`, `results/`) selected for a linear data pipeline. This minimizes overhead and aligns with the CPU-only, batch-processing nature of the analysis. The separation of `raw` and `processed` data ensures data hygiene and reproducibility.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| ILR Transformation | Required by Constitution Principle VI and Spec FR-003 to handle compositional constraints. | Standard log-ratio or raw abundance analysis produces spurious associations and violates mathematical soundness for linear models. |
| Interaction Terms (Age * Taxon) | Required by Spec FR-006 to assess age-dependency without splitting the sample (preserving power). | Stratification would reduce sample size in the 65+ group, potentially invalidating the power for detecting weak effects. |
| Sensitivity Analysis (Over-control) | Required by Spec FR-010 and Constitution Principle VII to check for signal masking by diet/medication. | Omitting this step would fail to address the ambiguity of whether diet/medication are confounders or mediators. |
| Lasso/Ridge Regularization | Required to handle high-dimensional data (hundreds of taxa) and prevent overfitting/multicollinearity. | Standard OLS is unstable when predictors > samples or highly correlated; Lasso provides feature selection and stability. |
| Bayesian Zero-Replacement | Required to avoid bias from fixed pseudocounts in low-abundance taxa. | Fixed 1e-6 can create spurious correlations; Bayesian-multiplicative is statistically superior for compositional data. |

## Implementation Phases

### Phase 0: Data Acquisition & Validation
- **Task 0.1**: Verify UK Biobank 16S and Cognitive data availability (Data Availability Gate).
- **Task 0.2**: Validate cognitive instrument citations (FR-009) against primary sources.
- **Task 0.3**: Download/Provision data (official `ukbiobank` tool or local files).
- **Task 0.4**: Generate checksums and record in `state` file.

### Phase 1: Preprocessing & Power Analysis
- **Task 1.1**: Filter cohort (antibiotics, missingness).
- **Task 1.2**: Apply Bayesian-multiplicative zero-replacement and ILR transformation.
- **Task 1.3**: Pre-screen taxa by prevalence (min [deferred]).
- **Task 1.4**: **Power Analysis**: Generate synthetic dataset (beta=0.1), run power script, validate against theoretical values (SC-003), and generate Power Report.

### Phase 2: Statistical Analysis
- **Task 2.1**: Fit Lasso-regularized linear models for main effects.
- **Task 2.2**: Apply Benjamini-Hochberg correction for main effects.
- **Task 2.3**: Fit interaction models (Age * Taxon).
- **Task 2.4**: Apply Benjamini-Hochberg correction for interaction terms.
- **Task 2.5**: Perform mediation analysis (Diet/Medication inclusion/exclusion).

### Phase 3: Sensitivity & Visualization
- **Task 3.1**: Generate Threshold Sweep Report (p < 0.01, 0.05, 0.1) (SC-005).
- **Task 3.2**: Generate Manhattan plots with effect size annotations.
- **Task 3.3**: Generate k-fold cross-validation stability report.

## Dependency Order
1. Data Acquisition -> 2. Preprocessing -> 3. Power Analysis (Gate) -> 4. Statistical Analysis -> 5. Sensitivity/Visualization.
*Note: Power Analysis must pass validation before Statistical Analysis proceeds.*