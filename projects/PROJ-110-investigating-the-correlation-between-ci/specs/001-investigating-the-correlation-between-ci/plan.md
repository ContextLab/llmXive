# Implementation Plan: Investigating the Correlation Between Circadian Gene Expression and Metabolic Syndrome Risk

**Branch**: `001-circadian-metabolic-correlation` | **Date**: 2023-10-27 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-investigating-the-correlation-between-ci/spec.md`

## Summary

This project implements a statistical analysis pipeline to investigate the correlation between the expression of core circadian genes (e.g., *PER1*, *BMAL1*) and Metabolic Syndrome (MetS) risk using the GTEx v8 dataset. The technical approach involves: (1) downloading and parsing GTEx v8 RNA-seq TPM matrices and phenotype data; (2) **Data Availability Gate**: verifying the presence of critical clinical variables (BMI, fasting glucose, BP, lipids) required for ATP-III classification; (3) **Power & Feasibility Gate**: performing a formal power analysis based on expected missingness rates to determine feasibility *before* full implementation; (4) classifying donors as "MetS" or "Control" using strict ATP-III criteria; (5) performing stratified Wilcoxon rank-sum tests with Benjamini-Hochberg FDR correction; (6) building a **global** multivariate logistic regression model (with 'tissue' as a covariate) with 5-fold cross-validation; (7) computing correlations with continuous traits; and (8) performing sensitivity analysis on ATP-III thresholds. The pipeline is designed to run on CPU-only GitHub Actions runners (free tier) using `pandas`, `scipy`, and `scikit-learn`.

**Critical Constraint**: If GTEx v8 Phenotype data lacks the required metabolic variables (fasting glucose, BP, lipids), the pipeline will halt and flag the study as "Exploratory - Insufficient Phenotype Data". **TCGA is NOT a valid fallback** for systemic metabolic syndrome due to cancer-specific confounds and missing systemic metabolic panels. If the formal power analysis indicates power < 0.8 (likely due to high missingness), the study is marked "Infeasible" and halted.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `scikit-learn`, `statsmodels`, `matplotlib`, `seaborn`, `pyyaml`  
**Storage**: Local file system (`data/raw`, `data/processed`); processed data written to schema-defined CSV/JSON formats matching `contracts/`.  
**Testing**: `pytest` (unit tests for classification logic, integration tests for pipeline execution).  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7GB RAM).  
**Project Type**: Data Analysis Pipeline / CLI  
**Performance Goals**: Complete analysis on sampled GTEx data within 6 hours; memory usage < 6GB.  
**Constraints**: No GPU usage; no deep learning; strict adherence to ATP-III thresholds; handling of missing data via exclusion; **gene filtering** to core panel only before loading to memory to mitigate overfitting and memory issues.  
**Scale/Scope**: ~15 core circadian genes; N depends on GTEx v8 phenotype completeness (expected < 100 complete cases).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Strategy | Status |
| :--- | :--- | :--- |
| **I. Reproducibility** | All random seeds pinned in `code/`; `requirements.txt` pins versions; data fetched from canonical sources; pipeline runnable end-to-end. | **Pass** |
| **II. Verified Accuracy** | All dataset URLs in `research.md` sourced strictly from the "# Verified datasets" block. **Status is conditional** pending runtime verification of GTEx Phenotype columns. | **Pending Verification** |
| **III. Data Hygiene** | Raw data downloaded to `data/raw` with checksums; processed data written to `data/processed` with derivation logs; no in-place modification. | **Pass** |
| **IV. Single Source of Truth** | All statistics in `paper/` (future) derived from `data/processed` tables; no hand-typed numbers. Output formats (CSV/JSON) match `contracts/` schema. | **Pass** |
| **V. Versioning Discipline** | Artifacts tracked via content hashes; **State Update Mechanism**: The `main.py` pipeline includes a `update_state_hash()` function that reads the content hash of `data/processed/` artifacts and writes them to `state/projects/PROJ-110-...yaml` upon successful completion. | **Pass** |
| **VI. Clinical Criteria & Gene Panel** | MetS classification strictly follows ATP-III (BMI, Glucose, BP, TG, HDL); Gene panel fixed to PER, CRY1-2, BMAL1, CLOCK, NR1D1, RORα. | **Pass** |
| **VII. Statistical Correction** | Benjamini-Hochberg FDR applied to all DE p-values; k-fold CV used for logistic regression. | **Pass** |

## Project Phases

### Phase 0: Data Ingestion & Verification
1. Download GTEx v8 RNA-seq TPM matrix and Phenotype file from verified sources.
2. **Data Availability Gate**: Verify presence of required columns (BMI, Glucose, Systolic/Diastolic BP, Triglycerides, HDL) in the Phenotype file.
   - *If missing*: Log fatal error, flag study as "Exploratory - Insufficient Phenotype Data", halt pipeline.
   - *If present*: Proceed.
3. **Gene Filtering**: Filter expression matrix to **only** the ~15 core circadian genes to reduce memory footprint and mitigate overfitting.
4. Merge Phenotype and Expression data on `sample_id`.

### Phase 0.5: Power & Feasibility Analysis
1. Apply strict listwise exclusion for missing values in the 5 clinical variables.
2. Count remaining samples (N).
3. **Formal Power Analysis**: Calculate statistical power based on expected effect sizes and the observed N, accounting for expected missingness rates in post-mortem data.
   - *If Power < 0.8*: Log "Feasibility Critical", flag study as "Infeasible", halt pipeline.
   - *If Power >= 0.8*: Proceed.
4. **Note**: This phase explicitly addresses the high likelihood of missing post-mortem data (Glucose/BP) and ensures the study does not proceed with insufficient power.

### Phase 1: Classification (ATP-III)
1. Classify each donor as "MetS" (>=3 criteria) or "Control" (<3 criteria).
2. Log excluded samples and criteria counts.
3. **Sensitivity Analysis (SC-005)**: Store the baseline classification for later robustness check.

### Phase 2: Differential Expression (Wilcoxon)
1. Group samples by `tissue`.
2. For each tissue with N >= 20 per group (MetS/Control):
   - Perform Wilcoxon rank-sum test for each of the ~15 core circadian genes.
3. Apply Benjamini-Hochberg FDR correction across all tests.
4. Record effect sizes and significance.

### Phase 3: Predictive Modeling (Logistic Regression)
1. **Global Model Strategy**: Fit a single logistic regression model on the full dataset: `MetS ~ Gene_Expression + Age + Sex + Tissue`.
   - *Note*: 'Tissue' is included as a covariate to control for tissue-specific baselines. This is distinct from the stratified DE analysis (Phase 2), where 'tissue' is constant within the stratum. This resolves the logical conflict of including 'tissue' as a predictor in a stratified model.
2. Perform k-fold cross-validation to evaluate AUC.
3. Calculate Odds Ratios (OR) with a confidence interval.
4. Check for collinearity (VIF > 5). If detected, flag and report descriptive joint relationship.

### Phase 4: Correlation Analysis (FR-007, SC-004)
1. For ALL core circadian genes, compute correlation with continuous traits (BMI, Glucose, TG, HDL, BP).
2. Method: Spearman by default; Pearson if Shapiro-Wilk p > 0.05.
3. Measure magnitude of `r` against null hypothesis (r=0).
4. Generate scatter plots for significant correlations.

### Phase 5: Sensitivity Analysis (SC-005)
1. Vary ATP-III thresholds by ±5% (e.g., BMI >= 28.5 vs 30.0).
2. Re-run classification and compare the resulting MetS/Control labels to the baseline.
3. Calculate robustness metrics (e.g., % of samples reclassified).

### Phase 6: Reporting & Versioning
1. Generate diagnostic plots (heatmap, ROC, scatter).
2. Write results to `data/processed/` in schema-defined formats.
3. **Versioning**: Compute content hashes of all `data/processed/` files and update `state/projects/PROJ-110-...yaml`.

## Project Structure

### Documentation (this feature)

```text
specs/001-circadian-metabolic-correlation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (created later)
```

### Source Code (repository root)

```text
projects/PROJ-110-investigating-the-correlation-between-ci/
├── data/
│   ├── raw/             # Downloaded GTEx/TCGA files (checksummed)
│   └── processed/       # Cleaned phenotype tables, expression matrices, results
├── code/
│   ├── __init__.py
│   ├── main.py          # Entry point for pipeline execution
│   ├── data/
│   │   ├── __init__.py
│   │   ├── loader.py    # Data download, parsing, and column verification
│   │   └── classifier.py # ATP-III classification logic
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── differential.py # Wilcoxon tests, FDR correction
│   │   ├── modeling.py   # Logistic regression, CV, diagnostics
│   │   └── correlation.py # Spearman/Pearson correlation analysis
│   ├── viz/
│   │   ├── __init__.py
│   │   └── plots.py     # Heatmaps, ROC, scatter plots
│   └── utils/
│       ├── __init__.py
│       └── logging.py
├── tests/
│   ├── unit/
│   │   └── test_classifier.py
│   └── integration/
│       └── test_pipeline.py
├── docs/
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure (`code/`, `data/`, `tests/`) selected to align with the CLI nature of the analysis pipeline and the requirement for end-to-end reproducibility on a single runner.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| None | The project scope is contained within standard statistical methods and fits within the CPU constraints. | N/A |

## Circadian Phase Confounding (Critical Limitation)

- **Issue**: GTEx samples lack collection timestamps (circadian phase). Circadian gene expression is highly time-dependent.
- **Impact**: A significant difference between MetS and Control groups could simply reflect that MetS donors were sampled at a different time of day than controls, rather than a true metabolic effect.
- **Mitigation**: The study will be framed as investigating "associations with metabolic status in a mixed-phase cohort". Results will not be interpreted as evidence of circadian *disruption* per se, but as associations in a heterogeneous sample.
- **Sensitivity Check**: If possible, the analysis will focus on tissues with known high circadian amplitude (e.g., Liver) as a sensitivity check, acknowledging the limitation remains.

## Assumptions

- The GTEx v8 dataset contains the specific clinical variables (fasting glucose, triglycerides, HDL, blood pressure) required to apply ATP-III criteria; if any variable is missing for a large portion of samples, the sample size will be significantly reduced, potentially affecting power.
- If GTEx v8 lacks sufficient complete cases (N < 100), **no suitable alternative dataset exists** for systemic Metabolic Syndrome. The study will be interpreted as exploratory with a noted power limitation or halted if power is insufficient.
- The "Core Circadian Genes" list (PER1-3, CRY1-2, BMAL1, CLOCK, NR1D1, RORα) is sufficient to capture the relevant biological signal; other circadian genes may be omitted.
- The GTEx tissue samples, though not time-stamped, contain sufficient biological variance in gene expression to detect associations with metabolic status, assuming the metabolic syndrome itself induces a disruption in circadian rhythm detectable in bulk tissue.
- The analysis will run on a CPU-only environment (GitHub Actions free tier); therefore, no GPU-accelerated deep learning models or 8-bit quantization will be used; only classical statistical methods (Wilcoxon, Logistic Regression) and standard libraries (scikit-learn, statsmodels, pandas) will be employed.
- The Benjamini-Hochberg correction is appropriate for the multiple testing burden of a moderate number of genes; if the list of genes were expanded to thousands, a more conservative method or different correction strategy would be needed.
- The ATP-III criteria, originally designed for clinical diagnosis, are valid proxies for "Metabolic Syndrome" in a research setting using post-mortem tissue samples.
- **The sample size of available GTEx samples with complete metabolic phenotypes is likely insufficient (N < 100) to achieve statistical power > 0.8 for detecting moderate effect sizes (OR ≈ 1.5).** If not, the results will be interpreted as exploratory with a noted power limitation.
- Tissue-specific stratification in FR-003 is sufficient to control for batch effects; if tissue composition differs significantly between MetS and Control groups, the logistic regression (FR-005) will account for residual confounding via the 'tissue' covariate.