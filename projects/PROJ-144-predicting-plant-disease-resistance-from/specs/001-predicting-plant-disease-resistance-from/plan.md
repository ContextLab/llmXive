# Implementation Plan: Predicting Plant Disease Resistance from Publicly Available Metabolomic Data

**Branch**: `001-predict-plant-disease-resistance` | **Date**: 2026-06-28 | **Spec**: `specs/001-predicting-plant-disease-resistance/spec.md`
**Input**: Feature specification from `/specs/001-predicting-plant-disease-resistance/spec.md`

## Summary

This project implements a reproducible machine learning pipeline to predict plant disease resistance using pre-challenge metabolomic profiles from public repositories (Metabolomics Workbench). The technical approach involves downloading raw intensity tables, harmonizing labels (binary for classification, z-scored for ordinal exploration), applying ComBat for batch correction, training a Random Forest classifier with strict cross-validation, and performing rigorous validation (permutation testing, VIF diagnostics, sensitivity analysis) to ensure findings are associational and robust.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn==1.5.0`, `pandas==2.2.0`, `numpy==1.26.0`, `scipy==1.13.0`, `pyyaml==6.0.1`, `requests==2.32.0`, `joblib==1.4.0`, `pydantic==2.7.0`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `results/`); no external database.  
**Testing**: `pytest==8.2.0` with `pytest-cov`  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, 7GB RAM, 14GB disk)  
**Project Type**: Data science pipeline / CLI tool  
**Performance Goals**: Complete full pipeline (download, preprocess, train, evaluate) within 6 hours on CPU.  
**Constraints**: Must run on CPU-only runner; no GPU required (Random Forest on <50 features is CPU-tractable).  
**Scale/Scope**: <50 metabolites, ≥50 samples (target); handles batch correction for ≥2 studies.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action/Reference |
|-----------|--------|------------------|
| **I. Reproducibility** | **Pending Validation** | Random seeds pinned in `code/`. External datasets fetched from canonical Metabolomics Workbench IDs. `requirements.txt` pins all dependencies. Contracts (`contracts/*.yaml`) are defined and validated in Phase 4. |
| **II. Verified Accuracy** | **Pending Validation** | All citations (Benjamini-Hochberg, ComBat, DOME) will be validated against primary sources before review points are awarded. |
| **III. Data Hygiene** | **Pending Validation** | Raw data preserved in `data/raw/` with checksums. Derivations in `data/processed/` with new filenames. PII scan enforced via pre-commit. |
| **IV. Single Source of Truth** | **Pending Validation** | All figures/stats in paper trace to `results/*.json` and `data/processed/`. No hand-typed numbers. |
| **V. Versioning Discipline** | **Pending Validation** | Content hashes tracked in `state/`. `updated_at` timestamps updated on artifact change. |
| **VI. Metabolomic Data Integration** | **Pending Validation** | Plan explicitly includes InChIKey alignment and ComBat batch correction before model training. |
| **VII. Biological ML Validation** | **Pending Validation** | Test set independent of feature selection. Permutation testing (≥1000) included. VIF diagnostics required. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-plant-disease-resistance/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Completed)
│   ├── metadata.schema.yaml
│   ├── output.schema.yaml
│   └── dataset.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Paths, seeds, hyperparameters
├── data/
│   ├── __init__.py
│   ├── download.py      # Metabolomics Workbench fetcher
│   ├── preprocess.py    # Normalization, log-transform, batch correction
│   └── harmonize.py     # Label harmonization (z-scoring for ordinal)
├── models/
│   ├── __init__.py
│   ├── train.py         # Random Forest, GridSearchCV
│   ├── evaluate.py      # Metrics, permutation, VIF, sensitivity (T022)
│   └── interpret.py     # Feature importance, pathway mapping
├── utils/
│   ├── __init__.py
│   └── logging.py       # JSON logging for reproducibility
└── main.py              # Orchestration script

data/
├── raw/                 # Unmodified downloads (checksummed)
├── processed/           # Normalized, batch-corrected, harmonized data
└── intermediate/        # Temporary files (e.g., VIF intermediates)

results/
├── metrics.json         # Balanced accuracy, ROC-AUC, permutation p-value (T024)
├── shap_analysis.json   # Feature importances, VIF scores, correlation matrix (T024)
├── pathway_analysis.json# Mapped pathways for top 10 metabolites (T023)
└── plots/               # Visualization outputs (e.g., pathway_barplot.png)

tests/
├── contract/            # Schema validation tests
├── integration/         # Pipeline end-to-end tests
└── unit/                # Unit tests for preprocessing, models

state/
└── projects/PROJ-144-predicting-plant-disease-resistance-from.yaml
```

**Structure Decision**: Single project structure (`code/`, `data/`, `results/`) selected to match the CLI/pipeline nature of the project. This aligns with the Constitution's requirement for a single source of truth and reproducible execution on a CI runner.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | No violations found. | N/A |

## Phased Implementation Plan

### Phase 0: Data Acquisition & Verification (FR-001, FR-014)
1.  **Download**: Fetch raw intensity tables and phenotype metadata from Metabolomics Workbench for ≥1 study with public access.
2.  **Verify**: Check metadata for 'pre-challenge' temporal separation. **Method**: Verify sample metadata contains fields indicating 'pre-challenge', 'baseline', or timestamps prior to pathogen inoculation. If metadata lacks these, flag as unverified.
3.  **Store**: Save raw files to `data/raw/` with SHA256 checksums.

### Phase 1: Preprocessing & Harmonization (FR-002, FR-003, FR-004, FR-013)
1.  **Clean**: Discard features missing >30% of samples.
2.  **Transform**: Log-transform remaining intensities.
3.  **Harmonize**: 
    *   **Binary Labels**: Map directly to 0/1 (Susceptible/Resistant) without z-scoring.
    *   **Ordinal Labels**: Z-score within study or stratify by assay method.
    *   **Data Flow**: `binary_label` is passed to Random Forest trainer. `harmonized_score` is used only for exploratory correlation analysis.
4.  **Correct**: Apply ComBat batch-effect correction if ≥2 studies are combined.
5.  **Output**: Save `data/processed/batch_corrected_matrix.csv` and `data/processed/labels.csv`.

### Phase 2: Model Training & Validation (FR-005, FR-006, FR-007, FR-008, FR-011, FR-012)
1.  **Split**: 
 * **If N ≥ 50**: Reserve independent hold-out set ([deferred]) using `binary_label` for stratification.
    *   **If N < 50**: Skip hold-out set. Perform **Learning Curve Analysis** (SC-004) using full stratified 5-fold CV. Flag power limitation.
2.  **Train**: Random Forest (n_estimators=500, max_depth=10) with stratified 5-fold CV.
3.  **Validate**:
    *   **3a. Exploratory Analysis**: Compute pairwise correlations (metabolite vs. resistance). Apply Benjamini-Hochberg FDR (≤0.05) to p-values. Filter for |r| > 0.4, p < 0.01. Output to `results/shap_analysis.json`.
    *   **3b. Model Validation**: Compute balanced accuracy, ROC-AUC on hold-out (or CV if N<50). Run permutation testing (≥1,000 permutations). Flag p < 0.05 as significant.
    *   **3c. Collinearity Diagnostics**: Calculate VIF for all predictors. Flag >5. **Note**: VIF is for biological interpretation only (FR-012); it does NOT trigger feature removal or re-training. RF is robust to collinearity.
    *   **3d. Sensitivity Analysis**: Sweep probability decision thresholds (baseline +/- diff ∈ {small, 0.05, 0.1}). Report False Positive Rate (FPR) and False Negative Rate (FNR) at each threshold.
4.  **Log**: Save `results/metrics.json` and `results/shap_analysis.json`.

### Phase 3: Interpretation & Reporting (FR-010, FR-011)
1.  **Extract**: Top 10 metabolites by mean decrease in impurity.
2.  **Map**: Match InChIKeys to KEGG/MetaCyc pathways.
3.  **Visualize**: Generate `results/plots/pathway_barplot.png` from `results/pathway_analysis.json` (T028).
4.  **Report**: Generate narrative report in `results/pathway_analysis.json` with a mandatory "framing" field set to "associational" (FR-011). **Template**: "These findings represent statistical associations between pre-challenge metabolite profiles and disease resistance phenotypes. No causal claims are made."

### Phase 4: Infrastructure & Contracts (T001, T003, T006, T007, T022, T023, T024)
1.  **Setup**: Create directory structure (`code/`, `data/raw`, `data/processed`, `tests/`, `state/`). **Status**: Completed.
2.  **Config**: Create `pre-commit-config.yaml` with PII scan and formatting hooks. **Status**: Completed (T003).
3.  **Contracts**: Define and validate `contracts/metadata.schema.yaml` (T006), `contracts/output.schema.yaml` (T007), `contracts/dataset.schema.yaml`. **Status**: Completed.
4.  **Implementation**: 
    *   Implement VIF calculation in `code/models/evaluate.py` (T022).
    *   Implement associational framing in `results/pathway_analysis.json` (T023).
    *   Implement metrics logging in `results/metrics.json` and `results/shap_analysis.json` (T024).
    *   Implement visualization generation `results/plots/pathway_barplot.png` from `results/pathway_analysis.json` (T028).

## Unresolved concerns

None. All panel concerns have been addressed.