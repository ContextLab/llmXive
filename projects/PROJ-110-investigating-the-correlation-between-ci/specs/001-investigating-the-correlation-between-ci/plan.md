# Implementation Plan: Investigating the Correlation Between Circadian Gene Expression and Metabolic Syndrome Risk

**Branch**: `001-circadian-metabolic-correlation` | **Date**: 2023-10-27 | **Spec**: [spec.md](../specs/001-circadian-metabolic-correlation/spec.md)  
**Input**: Feature specification from `specs/001-circadian-metabolic-correlation/spec.md`

## Scope Limitation & Data Gap Analysis
The primary cohort required by the specification (**METSIM**) and the independent validation cohort (**MESA**) are **not** currently available via a verified open‑source download. Consequently, binary MetS labeling, multivariate logistic regression, cross‑validation, and external validation cannot be performed on a fully integrated donor‑level dataset unless a suitable open dataset that provides **both** RNA‑seq TPM matrices **and** the full set of ATP‑III clinical variables becomes available.

**Data Cohort Compatibility**:  
- **GTEx v8 TPM matrices** provide expression data and donor covariates (age, sex, PMI, Time‑of‑Death) but **do not** contain ATP‑III clinical variables.  
- **METSIM** (required for binary MetS labels) and **MESA** (validation) contain the needed phenotype data but are not openly downloadable.  

Therefore, the pipeline is designed with **conditional execution paths**:
1. **Full‑binary‑label mode** – If an open dataset with matched expression + ATP‑III phenotypes is supplied, the full binary‑label workflow (FR‑002, FR‑005, FR‑006, FR‑010) will run.  
2. **Exploratory mode** – Otherwise, the pipeline runs using available GTEx expression and covariates, and binary classification steps are skipped with a logged INFO message.

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==1.26.*`, `scipy==1.13.*`, `statsmodels==0.14.*`, `scikit-learn==1.5.*`, `datasets==2.18.*`, `matplotlib==3.8.*`, `seaborn==0.13.*`.
- **Compute Mode**: **CPU‑first**. All statistical models (ANCOVA, mixed‑effects, Logistic Regression) run on 2 CPU cores.  
- **Storage**: `data/` hierarchy. Large datasets are streamed via `datasets` library to stay within the 14 GB disk limit.
- **Reproducibility**: Random seeds pinned (`seed=42`). All data fetched from verified URLs when they become available.  
- **CPU‑Only Enforcement (T060)**: `src/scripts/cpu_check.py` asserts `torch.cuda.is_available() == False`. A CI workflow (see CI Enforcement section) will invoke this script as a blocking step.

## Constitution Check

| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All scripts deterministic; data fetched from verified URLs; CI enforces CPU‑only environment. |
| II. Verified Accuracy | Only URLs from the "Verified datasets" block are used; no invented sources. |
| III. Data Hygiene | Raw files checksummed; transformations produce new files in `data/processed/`. |
| IV. Single Source of Truth | Figures and tables trace back to single rows in the corresponding CSV/Parquet files. |
| V. Versioning Discipline | Artifact hashes recorded in project state YAML. |
| VI. Clinical/Gene Integrity | Core circadian gene list fixed; ATP‑III criteria used for binary label where possible. |
| VII. Stat Correction | Global Benjamini‑Hochberg FDR applied to all p‑values. |

## Project Structure
```text
src/
├── pipelines/
│   └── run_pipeline.py      # Main execution flow
├── analysis/
│   ├── data_loader.py        # Verified URL fetching & merging (single‑source only)
│   ├── stats_engine.py       # ANCOVA, mixed‑effects, logistic regression
│   └── diagnostics.py        # Power analysis, PMI residualization
├── scripts/
│   └── cpu_check.py         # T060: Explicit CUDA check script
└── utils/
    └── validation.py        # Contract schema validator
tests/
├── contract/                 # Schema validation tests
└── unit/                    # Logic tests for risk score & stats
```

## Implementation Phases & FR/SC Mapping

| Phase | Description | FR / SC addressed |
|-------|-------------|-------------------|
| **0 – CI Enforcement (T060)** | GitHub Actions workflow runs `src/scripts/cpu_check.py` to abort if a GPU is detected. | T060, Constitution I |
| **1 – Phenotype & Expression Acquisition** | Load a **single open dataset** that contains both TPM matrices and the five ATP‑III clinical variables (or abort with INFO and continue in exploratory mode). Validate against `dataset.schema.yaml`. | FR‑001, FR‑026 (conditional) |
| **2 – MetS Binary Classification (FR‑002)** | For donors with **all five** ATP‑III variables present, apply ATP‑III thresholds (≥ 3 criteria) → `MetS` or `Control`. Missing any variable → donor excluded from binary analyses. Output `classification.csv` validated against `classification.schema.yaml`. | FR‑002, SC‑001 |
| **3 – Power Analysis (FR‑011)** | A priori power calculations for ANCOVA (f = 0.25), logistic regression (odds‑ratio = 1.5), and correlation (r = 0.3) using `statsmodels.stats.power`. Results stored in `power_summary.csv`. If any analysis has power < 0.80, `study_status` is set to `exploratory` with a warning. | FR‑011, SC‑007 |
| **4 – PMI Residualization (FR‑031)** | Fit a linear model `TPM ~ PMI` for each gene‑tissue combination; replace raw TPM with residuals before any downstream modeling. PMI is **not** included as a covariate thereafter. | FR‑031 |
| **5 – Covariate‑Adjusted Differential Expression (ANCOVA) (FR‑003, FR‑013, FR‑020)** | *Pre‑processing*: Use PMI‑residualized TPM. <br> *Model*: For each tissue with ≥ 20 donors per **binary** group, fit `TPM_resid ~ MetS + Age + Sex + Time‑of‑Death`. <br> *Fallback*: If a tissue fails the per‑group N ≥ 20, apply **hierarchical mixed‑effects ANCOVA** pooling biologically similar tissues (FR‑020). Tissues that still fail are excluded with a WARNING. Output `de_results.csv` validated against `de_results.schema.yaml`. | FR‑003, FR‑013, FR‑020, FR‑031, SC‑002 |
| **6 – Global DE Correction (FR‑004)** | Apply a single Benjamini‑Hochberg FDR correction across **all** gene‑tissue tests (q < 0.05). | FR‑004, SC‑002 |
| **7 – Gene‑Trait Mixed‑Effects Modeling (FR‑007, FR‑014, FR‑012)** | For each core gene‑trait pair, fit a linear mixed‑effects model `TPM_resid ~ Trait + (1|Tissue)`. Normality of residuals determines whether to report Pearson *r* (if normal) or Spearman ρ (if non‑normal). Apply a **global** BH correction across all tests. Significance requires adjusted p < 0.05 **and** |ρ| ≥ 0.2 (FR‑024). Output `correlation_results.csv` validated against `correlation_results.schema.yaml`. | FR‑007, FR‑012, FR‑014, FR‑024, SC‑004 |
| **8 – Univariate Logistic Odds Ratios (FR‑009)** | Using the binary MetS label, fit separate univariate logistic regressions for each metabolic trait (BMI, glucose, BP, triglycerides, HDL). Report odds ratio, 95 % CI, and p‑value in `univariate_logistic_results.csv`. | FR‑009, SC‑001 |
| **9 – Batch‑Effect Sensitivity (FR‑015)** | Re‑fit the multivariate logistic regression (Phase 11) with and without the sequencing‑batch covariate; compute coefficient stability. Report stability ≥ 90 % as required; otherwise flag instability in `batch_sensitivity.csv`. | FR‑015, SC‑008 |
| **10 – Predictive Multivariate Logistic Regression (FR‑005, FR‑006)** | **Conditional** on ≥ 100 donors with complete binary labels. Fit an L2‑regularized (λ = 1.0) logistic model using **≤ 10** most variable core genes (selected **inside** each training fold) plus age, sex, tissue, Time‑of‑Death, and batch. Perform 5‑fold CV; report mean AUC and 95 % CI in `cv_performance.csv`. Apply DeLong test vs. baseline (AUC = 0.5) (FR‑023). | FR‑005, FR‑006, SC‑003 (conditional) |
| **11 – External Validation (FR‑010)** | **Conditional** on the availability of a verified MESA muscle RNA‑seq + phenotype dataset. Repeat DE and logistic pipelines on MESA; compute gene‑level overlap (≥ 15 % of METSIM hits) and AUC delta (ΔAUC ≤ 0.05, two‑sided α = 0.05). Output `validation_results.csv`. | FR‑010, SC‑006 (conditional) |
| **12 – Diagnostics & Figures (FR‑008)** | Generate heatmaps of DE results, ROC curves for the logistic model (when fitted), and scatter plots for significant gene‑trait correlations. All figures reference rows in the corresponding CSV files. | FR‑008, SC‑008 |
| **13 – Success Metrics Consolidation** | Consolidate all SC‑related numbers into `success_metrics.csv` (counts, proportions, power summaries, stability reports). | SC‑001, SC‑002, SC‑004, SC‑005, SC‑007, SC‑008 (SC‑003 & SC‑006 reported as N/A when binary data unavailable) |

## Success Criteria Mapping

| SC | Metric | Implementation Check |
|----|--------|----------------------|
| SC-001 | Fraction of donors successfully classified as MetS or Control (vs. total with complete phenotype) | `classification.csv` completeness report |
| SC-002 | Proportion of core circadian genes with significant DE (FDR < 0.05) per tissue & overall | `de_results.csv` summary |
| SC-003 | AUC ≥ 0.6 and statistically > 0.5 baseline (DeLong test) | `cv_performance.csv` (only if binary labels exist; otherwise reported as N/A) |
| SC-004 | |ρ| ≥ 0.2 and adjusted p < 0.05 for gene‑trait pairs | `correlation_results.csv` |
| SC-005 | ≥ 90 % label stability under ±5 % ATP‑III threshold perturbation | `sensitivity_log.csv` |
| SC-006 | ≥ 15 % gene‑level overlap & ΔAUC ≤ 0.05 in MESA validation | `validation_results.csv` (reported as N/A if MESA unavailable) |
| SC-007 | Power analysis results ≥ 0.80 for each major analysis | `power_summary.csv` |
| SC-008 | All generated files pass schema validation (`dataset.schema.yaml`, `classification.schema.yaml`, `de_results.schema.yaml`, `correlation_results.schema.yaml`, `logistic_regression.schema.yaml`, `model.schema.yaml`, `validation_results.schema.yaml`, `cv_performance.schema.yaml`) | CI runs `pytest tests/contract` |

## Notes on Conditional Execution
- **Binary‑label dependent phases** (10, 11, 12) will be skipped with a logged INFO message if the required phenotype‑expression dataset is not present.
- All other phases run on the available GTEx expression data and covariates, producing exploratory results that are still scientifically valuable.

## CI Enforcement (T060)

A GitHub Actions workflow (`.github/workflows/ci.yml`) will be added to the repository. The workflow:

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Enforce CPU‑only
        run: python src/scripts/cpu_check.py
      - name: Run contract tests
        run: pytest tests/contract
```

This ensures the pipeline aborts if CUDA is available, satisfying the T060 requirement.
