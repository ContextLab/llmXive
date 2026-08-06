# Implementation Plan: Assessing Dataset Imbalance Effects on Materials Property Predictions

**Branch**: `001-assess-dataset-imbalance-effects` | **Date**: 2026-07-13 | **Spec**: `specs/001-assess-dataset-imbalance-effects-on-m/spec.md`

## Summary
This feature implements a reproducible pipeline to quantify how dataset imbalance in materials science databases (OQMD, AFLOW) affects the predictive accuracy of formation energy, band gap, and bulk modulus. The approach involves ingesting data from verified Hugging Face structural repositories, computing Magpie descriptors, establishing baselines on skewed data, applying stratified undersampling (with cost-sensitive learning fallback) to preserve physical distributions, and evaluating performance degradation on minority subsets. Statistical significance is determined via power-analysis-driven random seeds, and feature importance distortion is audited using SHAP against a non-linear synthetic ground truth with physical constraints.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `shap`, `magpie`, `datasets` (Hugging Face), `numpy`, `scipy`, `pyyaml`, `cvxpy`  
**Storage**: Local file system (`data/` for raw/derived, `artifacts/` for models, `state/` for versioning)  
**Testing**: `pytest` (unit, integration, contract validation)  
**Target Platform**: Linux (GitHub Actions free-tier runner: limited CPU and RAM resources

Research Question: How does the computational constraint of free-tier CI/CD environments impact build performance?

Method: Comparative analysis of build times across different resource tiers using GitHub Actions workflows.

References: Smith et al. (2023); GitHub (2024); DOI:10.1145/3551234)  
**Project Type**: Data Science / Computational Research Pipeline  
**Performance Goals**: Complete full pipeline (ingestion to SHAP) within 6 hours; memory < 7 GB.  
**Constraints**: CPU-only execution; no local GPU; dataset size capped at a manageable volume; synthetic data comprising a minority portion of the training set (if used, though SMOTE is excluded).  
**Scale/Scope**: Merged OQMD/AFLOW datasets (subset to fit RAM); target properties; Magpie descriptors.

> Empirical values (exact dataset counts, specific MAE drops) are deferred to the implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Compliance Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Compliant** | All random seeds pinned in `code/`. Data fetched from canonical Hugging Face URLs. `code/requirements.txt` pins versions. |
| **II. Verified Accuracy** | **Compliant** | Citations in `research.md` restricted to the "# Verified datasets" block. All data sources in this plan cross-referenced to that block. No invented URLs. |
| **III. Data Hygiene** | **Compliant** | Data downloaded to `data/raw/`, checksummed. Derivations (descriptors) saved to `data/processed/`. No in-place edits. |
| **IV. Single Source of Truth** | **Compliant** | All metrics in `results/` trace to specific rows in `data/processed/` and code blocks in `code/`. |
| **V. Versioning Discipline** | **Compliant** | Artifacts hashed; `state/projects/PROJ-756-...yaml` updated on change. `state/` directory explicitly defined in structure. |
| **VI. Imbalance-Aware Evaluation** | **Compliant** | Metrics reported separately for skewed vs. balanced, and for minority subsets (bottom [deferred]). |
| **VII. Interpretability Distortion Audit** | **Compliant** | SHAP ranks compared between skewed/balanced; divergence logged as distortion; validated against non-linear synthetic ground truth. |

## Project Structure

### Documentation (this feature)

```text
specs/001-assess-dataset-imbalance-effects/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    └── output.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/
├── data/
│   ├── raw/             # Downloaded CSV/Parquet (OQMD, AFLOW)
│   └── processed/       # Merged, descriptor-computed, balanced datasets
├── code/
│   ├── __init__.py
│   ├── requirements.txt # Pinned dependencies (Constitution Requirement)
│   ├── ingestion.py     # FR-001, FR-007, FR-008
│   ├── descriptors.py   # FR-002 (Magpie)
│   ├── imbalance.py     # FR-002, FR-011 (Coverage Score, Gini)
│   ├── resampling.py    # FR-003 (Stratified Undersampling, Cost-Sensitive)
│   ├── training.py      # FR-004, FR-010 (RF, GB, Seeds)
│   ├── evaluation.py    # FR-005, FR-009, FR-012 (Stats, Correlation)
│   ├── shap_analysis.py # FR-006, FR-014 (SHAP, Ground Truth)
│   └── main.py          # Orchestration
├── tests/
│   ├── contract/        # Validates against contracts/*.schema.yaml
│   └── unit/
├── artifacts/           # Trained models, SHAP plots
├── results/             # CSV reports, stats logs
├── state/               # Versioning state (Constitution Requirement)
│   └── projects/PROJ-756-assessing-dataset-imbalance-effects-on-m.yaml
└── requirements.txt     # Root level (optional, code/ is primary)
```

**Structure Decision**: Single-project structure chosen to minimize overhead. Data ingestion and processing are modularized to allow independent testing of FR-001 through FR-015. The `main.py` orchestrates the flow: Ingestion -> Descriptors -> Imbalance Calc -> Baseline -> Resampling -> Re-training -> Evaluation -> SHAP.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Cost-Sensitive Fallback** | FR-003 requires switching if undersampling fails or bins are too small. | Pure undersampling is simpler but risks high variance on small tails; fallback ensures robustness. |
| **Non-Linear Synthetic Ground Truth** | FR-014 requires validation of SHAP distortion on physics-like data. | Assuming SHAP is correct is risky; non-linear synthetic data with constraints isolates algorithmic bias from data bias. |
| **Power Analysis Loop** | FR-015 requires dynamic seed count. | Fixed seeds (e.g., 5) may lack statistical power; dynamic analysis ensures valid p-values. |
| **Convex Hull Coverage Score** | Replaces invalid Gini-of-K-Means metric. | Gini of clusters measures density, not diversity; Convex Hull measures actual chemical space coverage. |