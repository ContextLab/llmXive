# Implementation Plan: Predicting Plant Disease Resistance from Publicly Available Metabolomic Data

**Branch**: `001-predict-plant-disease-resistance` | **Date**: 2026-06-26 | **Spec**: `specs/001-predict-plant-disease-resistance/spec.md`
**Input**: Feature specification from `/specs/001-predict-plant-disease-resistance/spec.md`

## Summary

This feature implements a machine learning pipeline to predict plant disease resistance using pre-challenge metabolomic profiles sourced from public repositories (Metabolomics Workbench). The approach involves downloading and harmonizing multi-study metabolomics data, applying batch-effect correction (ComBat) with covariate residualization, training a constrained Random Forest classifier with rigorous stratified cross-validation and permutation testing, and mapping top features to biological pathways using SHAP values. The implementation strictly adheres to the project constitution regarding reproducibility, data hygiene, and statistical rigor (associational framing, FDR correction, SHAP diagnostics).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `pyyaml`, `requests`, `statsmodels`, `shap`, `biopython`, `matplotlib`, `seaborn`.  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `code/`). No external database.  
**Testing**: `pytest` (unit tests for data loaders, model wrappers; integration tests for pipeline execution).  
**Target Platform**: Linux (GitHub Actions free-tier: Multiple CPUs, 7GB RAM, 14GB disk).  
**Project Type**: Computational biology research pipeline.  
**Performance Goals**: Complete full pipeline (download, preprocess, train, evaluate) within 6 hours on CPU-only runner; memory usage < 6GB.  
**Constraints**: No GPU; no deep learning; sample size may be limited (requires power analysis); strict separation of train/test sets; all findings framed as associational.  
**Scale/Scope**: Multi-study integration (≥2 studies if available); ≤50 metabolites after filtering; A moderate number of samples (approximately 200).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Principle | Compliance Strategy | Status |
| :--- | :--- | :--- |
| **I. Reproducibility** | Random seeds pinned in `code/` (e.g., `random_state=42`); external data fetched from canonical Metabolomics Workbench IDs; `requirements.txt` pins versions. | ✅ Pass |
| **II. Verified Accuracy** | All dataset citations in `research.md` reference the Metabolomics Workbench general source and specific Study IDs found during execution. The plan acknowledges no verified URLs exist in the prompt's provided list for this domain and does not fabricate them. | ✅ Pass |
| **III. Data Hygiene** | Raw data stored in `data/raw` with checksums recorded in state file; transformations write to `data/processed` with new filenames; no in-place modification. | ✅ Pass |
| **IV. Single Source of Truth** | All metrics (balanced accuracy, AUC, SHAP values) logged to a single JSON artifact; paper figures generated directly from this artifact. | ✅ Pass |
| **V. Versioning Discipline** | Content hashes for data artifacts tracked in `state/...yaml`; code changes trigger `updated_at` updates. | ✅ Pass |
| **VI. Metabolomic Data Integration** | Plan explicitly includes InChIKey alignment, covariate residualization, and ComBat batch correction for multi-study data (FR-004, FR-014). | ✅ Pass |
| **VII. Biological ML Validation** | Test set held out *before* feature selection; permutation testing (≥1000) for model and feature significance; SHAP diagnostics; FDR correction applied. | ✅ Pass |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-plant-disease-resistance/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── data/
│   ├── download.py          # FR-001: Fetch from Metabolomics Workbench (Direct HTTP)
│   ├── validate_temporal.py # FR-014: Verify pre-challenge timestamps vs challenge outcomes
│   ├── preprocess.py        # FR-002, FR-004, FR-013: Normalize, Align, Covariate Residualize, ComBat
│   └── harmonize_labels.py  # FR-003, FR-013: Z-score/stratify resistance labels
├── modeling/
│   ├── train.py             # FR-005, FR-006: RF training, CV, hold-out
│   ├── evaluate.py          # FR-007, FR-008, FR-009, SC-004: Permutation, FDR, Sensitivity, Learning Curves
│   └── interpret.py         # FR-010: SHAP importance, Pathway mapping
├── utils/
│   ├── constants.py         # Seeds, thresholds, paths
│   └── io.py                # Checksumming, logging
├── main.py                  # Orchestrator
└── requirements.txt         # Pinned dependencies

tests/
├── unit/
│   ├── test_download.py
│   ├── test_temporal.py
│   ├── test_preprocess.py
│   └── test_modeling.py
└── integration/
    └── test_full_pipeline.py

data/
├── raw/                     # Unmodified downloads (checksummed)
└── processed/               # Normalized, aligned, batch-corrected data

contracts/                   # Technical Artifacts (Schemas)
├── metadata.schema.yaml
└── output.schema.yaml

state/
└── projects/PROJ-144-.../
    └── artifact_hashes.yaml
```

**Structure Decision**: Single Python package structure (`code/`) is selected to facilitate modular testing and execution on CI. Separation of `download`, `validate_temporal`, `preprocess`, `modeling`, and `interpret` ensures clear phase boundaries (Data Acquisition -> Temporal Validation -> Preprocessing -> Training -> Evaluation -> Interpretation) as required by the spec and constitution.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Multi-study integration** | Spec requires combining ≥2 studies for robustness (US-1, FR-004). | Single-study analysis would miss batch-effect dynamics and reduce generalizability, failing the "Publicly Available" scope. |
| **ComBat Correction + Covariate Residualization** | Essential for aligning metabolite intensities across different instruments/labs while controlling for biological confounders (FR-004, Constitution Principle VI). | Simple z-scoring per study is insufficient to remove batch-specific technical variance; ignoring biological covariates risks confounding. |
| **Permutation Testing** | Required to establish significance against null (FR-007, Constitution Principle VII) and for feature selection stability. | Standard p-values from RF are not well-defined; permutation provides a robust empirical p-value for both model and features. |
| **SHAP Diagnostics** | Required for biological interpretation (FR-012) as VIF is a linear metric unsuited for RF. | VIF is a category error for non-linear models; SHAP provides consistent feature attribution. |
| **Power Analysis** | Required to validate sample size sufficiency for the specific hypothesis (Balanced Accuracy > 0.75). | Learning curves alone do not confirm statistical power for a specific effect size; a formal calculation is needed to flag underpowered studies. |

## Implementation Phases

### Phase 0: Feasibility & Power Analysis
1.  **Power Calculation**: Calculate minimum N required to detect Balanced Accuracy > 0.75 vs Null 0.50 with Alpha=0.05, Power=0.80. (Target N ≈ a sample size sufficient for statistical power in the proposed experimental design.).
2.  **Data Availability Check**: Query Metabolomics Workbench for studies matching "plant", "disease", "pre-challenge".
    *   *Decision*: If no studies with paired pre-challenge + resistance data exist, **HALT** with "Data Unavailable" error. Do not proceed with mock data.
3.  **Output**: `power_analysis_report.md`, `data_availability_log.json`.

### Phase 1: Data Acquisition & Preprocessing
1.  **Download**: Fetch raw intensity and phenotype files for selected Study IDs (FR-001).
2.  **Temporal Validation**: Run `validate_temporal.py` to verify `sample_time < challenge_time` for all samples (FR-014). Fail if violated.
3.  **Preprocessing**:
    *   Log-transform and filter missing values (>30%) (FR-002).
    *   Align metabolites via InChIKey.
    *   **Covariate Adjustment**: Extract biological covariates (species, growth conditions) and residualize them from metabolite intensities (or include in ComBat design) to prevent confounding.
    *   Apply ComBat batch correction (FR-004).
4.  **Label Harmonization**: Z-score or stratify resistance labels (FR-003, FR-013).
5.  **Output**: `data/processed/batch_corrected_matrix.csv`, `data/processed/labels.csv`.

### Phase 2: Modeling & Evaluation
1.  **Split**: Reserve % hold-out set *before* any feature selection (FR-006).
2.  **Training**: Random Forest (n_estimators=500, max_depth=10) with Stratified -Fold CV (FR-005).
3.  **Feature Selection**: Use **Permutation Importance** calculated *within* CV folds. Establish significance threshold via null distribution (A sufficient number of permutations).
4.  **Evaluation**:
    *   Compute Balanced Accuracy, ROC-AUC on hold-out set (SC-001).
    *   **Permutation Test**: permutations of labels to assess model significance (FR-007, SC-003).
    *   **Sensitivity Analysis**: Sweep decision cutoffs over absolute diff ∈ {0.01, 0.05, 0.1} and report FP/FR rates (FR-009, SC-005).
    *   **Learning Curve**: Generate learning curve to assess sample size sufficiency (SC-004).
5.  **Interpretation**:
    *   Compute SHAP values for top features.
    *   Map top metabolites to KEGG/MetaCyc (FR-010).
    *   **Exploratory Correlation**: Compute pairwise correlations on training data only (FR-008, SC-002). **Do not use for feature selection.**
6.  **Output**: `results/metrics.json`, `results/shap_analysis.json`, `results/learning_curve.png`.
