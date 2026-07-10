# Implementation Plan: Predicting Plant Root System Architecture from Genomic Data

**Branch**: `001-predict-root-architecture` | **Date**: 2026-07-02 | **Spec**: `spec.md`

## Summary

This feature implements a reproducible, CPU-tractable machine learning pipeline to predict *Arabidopsis thaliana* root system architecture (RSA) traits from genomic variant data across different nutrient conditions. The approach harmonizes genomic (SNP) and phenotypic datasets, encodes genotypes as allele counts, and trains baseline models (Linear Regression with L/L2, Random Forest, Gradient Boosting) separately per nutrient condition. The plan strictly adheres to GitHub Actions free-tier constraints (limited CPU, constrained RAM, 6h runtime) by prioritizing dimensionality reduction (Lasso) and sampling over heavy deep learning, and ensures statistical rigor via nested permutation testing and stability selection.

**Critical Data Note**: The `# Verified datasets` block provided in the spec does not contain verified URLs for a dataset pair containing both Genomes SNPs and specific RSA phenotypes under nutrient conditions. Consequently, the primary implementation path for CI validation uses a **Mock Data Generator**. The final report will explicitly state that the biological hypothesis remains unverified due to data unavailability. This plan prioritizes *pipeline correctness* and *statistical rigor* over biological inference in the current iteration.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn`, `pandas`, `numpy`, `scipy`, `shap` (CPU-only), `matplotlib`, `seaborn`, `pyyaml`  
**Storage**: Local filesystem (data/ and code/ directories); no external database.  
**Testing**: `pytest` (contract tests against schemas, unit tests for preprocessing logic).  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Computational research pipeline / CLI.  
**Performance Goals**: Complete full pipeline (download -> preprocess -> train -> evaluate -> report) within 6 hours on 2 vCPU, 7GB RAM.  
**Constraints**: No GPU/CUDA; no 8-bit/4-bit quantization; memory < 7GB peak; strict adherence to FR-002 (no imputation unless sensitivity analysis).  
**Scale/Scope**: Processing of public *Arabidopsis* datasets (approx. accessions, ~200k SNPs) with sampling/PCA to fit memory.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Verification / Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates `requirements.txt` pinning, random seed fixing, and raw data checksumming. |
| **II. Verified Accuracy** | **WARN** | No verified URLs exist for the required data pair. The plan implements a verification check that logs "No Verified Source" and proceeds with Mock Data. No real citations are verified, so the "Verified Accuracy" gate is passed only for the *process* of checking, not the *result* of finding a source. |
| **III. Data Hygiene** | **PASS** | Plan enforces checksums in `state/` and immutable raw data; derivations written to new files. |
| **IV. Single Source of Truth** | **PASS** | All metrics (R², MAE) will be derived from `code/` output (real or synthetic) and stored in `data/`. Distinction is made between SSoT for real data (unavailable) and SSoT for synthetic data (current). |
| **V. Versioning Discipline** | **PASS** | Artifacts will be hashed; `state/` file updated on change. |
| **VI. Genomic-Phenotypic Alignment** | **PASS (Logic)** | The *pipeline logic* explicitly matches by Accession ID and enforces allele-count encoding. However, *data availability* is a known blocker; the verification text clarifies this distinction. |
| **VII. Nutrient-Condition Stratification** | **PASS** | Training and evaluation loops are explicitly split by nutrient condition. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-root-architecture/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── unified_dataset.schema.yaml
    └── model_output.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-410-predicting-plant-root-system-architectur/
├── data/
│   ├── raw/             # Downloaded raw files (checksummed) or mock data
│   ├── processed/       # Harmonized, split datasets
│   └── checksums.txt    # Hashes for raw files
├── code/
│   ├── __init__.py
│   ├── config.py        # Paths, seeds, hyperparameters
│   ├── download.py      # Data fetching (with fallbacks)
│   ├── preprocess.py    # Harmonization, encoding, splitting
│   ├── train.py         # Model training (RF, GB, LR with Lasso)
│   ├── evaluate.py      # Metrics, nested permutation tests, SHAP
│   └── visualize.py     # Plots (importance, scatter)
├── tests/
│   ├── contract/        # Schema validation tests
│   ├── unit/            # Preprocessing logic tests
│   └── integration/     # End-to-end pipeline test (small subset)
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure selected to minimize overhead. The `code/` directory contains modular scripts that can be run sequentially or via a main runner, ensuring reproducibility on CI.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **L1 Regularization (Lasso)** | Genomic data (p >> n) requires feature selection. PCA was rejected for linear models because it destroys marker identity (Constitution VI). Lasso preserves marker identity while handling collinearity. | PCA was rejected for linear models because it prevents identifying specific predictive markers (US-3). |
| **Nested Feature Selection** | To prevent data leakage in permutation tests (scientific soundness). Feature selection must occur inside the CV/Permutation loop. | Performing feature selection on the full dataset before splitting leads to circularly optimistic p-values. |
| **Stability Selection (multiple bootstraps)

The research question is to identify stable feature subsets. The method involves applying Stability Selection with repeated bootstrapping. References: Meinshausen and Bühlmann (2010).** | A small number of bootstraps may be statistically insufficient to estimate stability (methodology concern). A larger number provides a robust estimate of variance. | 10 samples yield high variance in stability metrics, rendering the claim invalid. |
| **Stratified Splits** | GxE interactions are central to the hypothesis; pooling conditions would mask biological signals. | Pooling data violates Principle VII and would render the "nutrient condition" analysis invalid. |
| **Mock Data Fallback** | No verified dataset pair exists for the required variables. The pipeline must run to validate logic. | Real data is unavailable; a mock generator is the only way to satisfy CI constraints and test the pipeline. |

## Implementation Phases

### Phase 1: Environment & Configuration (P0)
- Setup `requirements.txt` with pinned versions.
- Configure `config.py` with random seeds, paths, and hyperparameters.
- **Task**: Verify environment isolation on CI.

### Phase 2: Data Ingestion & Verification (P1)
- **Task (FR-001)**: Implement `download.py` to attempt fetching from 1001 Genomes and ATRDB.
- **Task (SC-006)**: Implement `verify_fit.py` to programmatically check if downloaded data contains all required variables (SNP, Root Length, Nutrient Condition).
- **Task**: If verification fails (missing variables or no data), trigger `MockDataGenerator` to create a synthetic dataset with the correct schema.
- **Output**: `data/processed/unified_dataset.parquet` (real or synthetic) with a metadata flag indicating the source.

### Phase 3: Preprocessing & Splitting (P1)
- **Task**: Match accessions, encode genotypes (0, 1, 2), exclude markers with >5% missingness.
- **Task**: Stratified split (majority/minority/minority) by nutrient condition.
- **Output**: `data/processed/train.parquet`, `val.parquet`, `test.parquet`.

### Phase 4: Model Training (P2)
- **Task**: Train Linear Regression (Lasso/ElasticNet), Random Forest, Gradient Boosting for *each* nutrient condition.
- **Constraint**: If feature count > 5000, apply PCA *only* for tree-based models (noting interpretability loss) or use Lasso for linear models.
- **Output**: Trained model objects and initial metrics.

### Phase 5: Evaluation & Permutation Testing (P3)
- **Task (FR-007)**: Execute permutation tests (sufficient iterations) for each model.
  - **Critical**: Feature selection (variance filtering) and model training must be nested *inside* the permutation loop to prevent data leakage.
  - **Null Hypothesis**: Observed R² compared against distribution of R² from permuted targets.
- **Task**: Calculate p-values (proportion of permuted R² >= observed R²).
- **Task**: Apply Benjamini-Hochberg correction *only* to the set of model-level tests (one per condition), not per-marker.
- **Output**: `data/processed/model_metrics.csv` with R², CI, p-values, and significance flags.

### Phase 6: Feature Importance & Reporting (P3)
- **Task (US-3)**: Calculate feature importance using SHAP (for tree models) and Lasso coefficients (for linear models).
- **Task**: Perform Stability Selection with **a sufficient number of bootstrap samples** to rank marker stability.
- **Task**: Generate visualizations (scatter plots, importance plots).
- **Task**: Append standardized disclaimer (FR-009).
- **Output**: `data/processed/figures/`, `data/processed/results.json`.

### Phase 7: Validation & Cleanup (P0)
- **Task**: Run contract tests against schemas.
- **Task**: Verify runtime and memory constraints on CI.
- **Output**: Final report with explicit note on data availability status.