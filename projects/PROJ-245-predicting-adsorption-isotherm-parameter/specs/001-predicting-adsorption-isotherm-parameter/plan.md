# Implementation Plan: Predicting Adsorption Isotherm Parameters from Molecular Features

**Branch**: `001-predict-adsorption-isotherm-params` | **Date**: 2026-07-14 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-predict-adsorption-isotherm-params/spec.md`

## Summary

This feature implements a machine learning pipeline to predict thermodynamic adsorption isotherm parameters (Langmuir capacity, Henry's constant) from molecular descriptors (polarizability, van der Waals volume) and adsorbent properties. The approach involves curating a dataset from the verified **MOF-177 Benchmark** (HuggingFace), calculating descriptors via RDKit, training baseline regression models (Linear, RF, GB) with material-level separation to prevent leakage, and interpreting results via SHAP analysis with rigorous statistical validation (FDR correction, cluster-aware permutation testing).

**Critical Data Constraint**: If no verified real-world adsorption dataset is found, the pipeline **HALTS** with a "Data Unavailable" error. Synthetic data is used **only** for logic verification (User Story 1 & 2) and is explicitly excluded from scientific claims.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `rdkit`, `scikit-learn`, `pandas`, `numpy`, `shap`, `xgboost`, `lightgbm`, `pyyaml`, `datasets` (HuggingFace)  
**Storage**: Local filesystem (CSV/Parquet), `data/` directory for artifacts  
**Testing**: `pytest` (unit tests for descriptor calculation, integration tests for pipeline flow)  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7GB RAM)  
**Project Type**: Data Science CLI / Research Pipeline  
**Performance Goals**: Full pipeline execution ≤ 4 hours on CPU; R² > 0.2 improvement over Material-Only Baseline  
**Constraints**: No GPU available on default runner; data must be streamed or sampled to fit memory; strict separation of training/test sets by material ID  
**Scale/Scope**: ~500-800 data points (target N > 500 per spec assumption); A set of molecular descriptors  

> **Dataset Note**: The primary data source is the **MOF-177 Benchmark** (HuggingFace `ethanolivertroy/mof-177-benchmark`). If this dataset is unavailable, the pipeline halts immediately. Synthetic data is generated **only** for logic testing (US-1) and is marked "Provisional" to ensure it does not contribute to the scientific claim or violate the Single Source of Truth principle.

## Constitution Check

*Gates determined based on constitution file*

| Principle | Status | Action/Comment |
|-----------|--------|----------------|
| **I. Reproducibility** | **Pass** | Plan mandates pinned `requirements.txt`, fixed random seeds, and explicit data fetching logic from MOF-177. |
| **II. Verified Accuracy** | **Conditional Pass** | Plan uses a verified dataset (MOF-177). If unavailable, the project halts; no synthetic substitution allowed for scientific claims. |
| **III. Data Hygiene** | **Pass** | Plan mandates checksumming, immutable raw data, and distinct transformation steps. |
| **IV. Single Source of Truth** | **Pass** | Results from synthetic data (logic tests) are marked "Provisional" and do not contribute to SSoT. Only results from MOF-177 (real data) are SSoT. |
| **V. Versioning Discipline** | **Pass** | Artifacts will carry content hashes. |
| **VI. Physicochemical Descriptor Integrity** | **Pass** | Descriptors MUST be calculated via RDKit in `code/`, not external sources. |
| **VII. Physicochemical Plausibility** | **Pass** | Plan includes comparison against `LiteratureConsensusList` and validation of feature importance directionality. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-adsorption-isotherm-params/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── model_output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-245-predicting-adsorption-isotherm-parameter/code/
├── data/
│   ├── raw/             # Downloaded raw files (if any)
│   ├── processed/       # Cleaned CSVs
│   └── benchmarks/      # runtime_log.json
├── models/
│   ├── train.py         # Training loop, CV, hyperparameter tuning
│   ├── predict.py       # Inference
│   └── evaluate.py      # Metrics, null model comparison
├── features/
│   ├── descriptors.py   # RDKit calculation logic
│   └── preprocess.py    # Filtering, unit normalization
├── analysis/
│   ├── shap_analysis.py # SHAP plots, permutation testing
│   └── report_gen.py    # Final report generation
├── utils/
│   ├── logging.py       # Runtime logging
│   └── config.py        # Paths, seeds, constants
├── tests/
│   ├── test_descriptors.py
│   └── test_pipeline.py
├── requirements.txt
└── run_pipeline.py      # Main entry point
```

**Structure Decision**: Single project structure under `code/` as it is a linear research pipeline. No frontend/backend split required.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Cluster-aware permutation testing** | Required by FR-007 to handle multicollinearity within material clusters. | Standard permutation would shuffle across materials, ignoring the hierarchical structure and inflating false positives. |
| **FDR Correction** | Required by FR-006 to control false discoveries in high-dimensional descriptor space. | Uncorrected p-values would lead to spurious feature selection. |
| **Material-level Split** | Required by FR-003 to prevent data leakage (same material in train/test). | Random split would allow the model to "memorize" material properties rather than learn generalizable physics. |
| **Top-3 Feature Retraining** | Required by SC-003 to validate the predictive power of the minimal descriptor set. | Using the full-model hyperparameters on a reduced feature set would be suboptimal and invalidate the SC-003 metric. |

## Implementation Phases

### Phase 1: Data Curation & Validation
1.  **1.1 Fetch Data**: Load `ethanolivertroy/mof-177-benchmark` from HuggingFace. **If unavailable, HALT with "Data Unavailable" error.**
2.  **1.2 Generate Synthetic Logic Test Data**: Create a small synthetic dataset (N=50) with known linear relationships to validate pipeline logic (US-1, FR-001). **Note**: This data is for logic testing only, not scientific claims.
3.  **1.3 Filter & Clean**: Retain only Type I isotherms. Remove entries with missing `K_H` or `Q_max`.
4.  **1.4 Descriptor Calculation**: Compute RDKit descriptors (MW, PSA, Polarizability, VdW Volume, H-bond counts).
5.  **1.5 Unit Normalization**: Convert all surface area to `m²/g`.

### Phase 2: Modeling & Validation
1.  **2.1 Split**: Group by `material_id`. A standard Train/Test split (Train/Test) ensuring no material overlap.
2.  **2.2 Baseline Models**: Train Linear Regression, Random Forest, Gradient Boosting on the **full feature set**.
3.  **2.3 Cross-Validation**: K-fold CV, stratified by material ID.
4.  **2.4 Hyperparameter Tuning**: Grid search on RF and GB (full feature set) to identify the best architecture.
5.  **2.5 Model Interpretation (SHAP)**: Generate SHAP summary plots and partial dependence plots for the best-performing model (from 2.4). Identify the **Top 3 Features** by mean absolute SHAP value.
6.  **2.6 Top-3 Feature Model Validation (SC-003)**:
    *   **Trigger**: Executed after 2.5 (SHAP Analysis).
    *   **Action**: Extract the Top 3 features identified in 2.5.
    *   **Retraining**: Retrain the **best-performing model architecture** (from 2.4) using **ONLY** these 3 features.
    *   **Tuning**: Perform a **new, independent hyperparameter grid search** specifically for this 3-feature subset to ensure optimal performance (addressing SC-003 rigor).
    *   **Evaluation**: Evaluate this reduced model on the held-out test set. Calculate R² and compare against the **Material-Only Baseline** (predicting mean per material).
    *   **Success Metric**: Report R² and confidence intervals.; verify if R² ≥ 0.2 improvement over Material-Only Baseline.
7.  **2.7 Null Baseline**: Train "Material-Only" model (predict mean per material ID) for comparison.

### Phase 3: Statistical Validation
1.  **3.1 Permutation Test (Feature)**: Shuffle feature values *within* material clusters (FR-007).
    *   **Algorithm**: For each feature, permute its values among rows sharing the same `material_id`. Calculate the resulting drop in model performance to generate a null distribution for that feature's importance.
2.  **3.2 Permutation Test (Model)**: Shuffle target `y` *between* materials to generate null distribution for R².
    *   **Algorithm**: Permute the target variable values across different `material_id` groups to break the relationship between descriptors and the target while preserving the cluster structure of the features.
3.  **3.3 FDR Correction**: Apply Benjamini-Hochberg to p-values (FR-006).
4.  **3.4 Collinearity Check**: Calculate VIF; pre-filter features with VIF > 5 (if not already done in 2.6).

### Phase 4: Interpretation & Reporting
1.  **4.1 Final Report Generation**: Compile metrics, **adjusted p-values (q-values)** for all top features (SC-005), and plots into `data/reports/final_report.md`.
2.  **4.2 Literature Consensus Report**: Compare top descriptors against `LiteratureConsensusList`. Discuss alignment/divergence and novel drivers (FR-008).
3.  **4.3 Runtime Logging**: Ensure `data/benchmarks/runtime_log.json` is generated with start/end times and status (FR-009).

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **No verified adsorption dataset** | High (Cannot validate scientific hypothesis) | Use MOF-177 (verified). If unavailable, halt with "Data Unavailable" error. |
| **Data leakage (material ID)** | High (Overfitting) | Enforce group-based split (FR-003). |
| **Multicollinearity** | Medium (Unreliable feature importance) | Cluster-aware permutation testing (FR-007) and VIF pre-filtering. |
| **Runtime > 4 hours** | Medium | Profile early; limit CV folds if needed. |
| **Suboptimal Reduced Model** | Medium (Invalid SC-003) | Explicitly re-tune hyperparameters for the 3-feature subset in Phase 2.6. |