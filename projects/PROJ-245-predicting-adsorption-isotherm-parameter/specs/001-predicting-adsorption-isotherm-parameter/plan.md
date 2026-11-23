# Implementation Plan: Predicting Adsorption Isotherm Parameters from Molecular Features

**Branch**: `001-predict-adsorption-isotherm-params` | **Date**: 2026-07-14 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-predict-adsorption-isotherm-params/spec.md`

## Summary
This project implements a machine learning pipeline to predict adsorption isotherm parameters (Henry's constant, Langmuir capacity) from molecular descriptors of adsorbates and properties of adsorbents. The approach involves curating data from the verified `matsci/qmof` dataset (with fallback to `coreshare/coref_mof_2019`), calculating RDKit descriptors, training baseline regression models (Linear, RF, GB) with material-level leakage prevention (GroupKFold), and interpreting results via SHAP analysis with rigorous statistical correction (Cluster-aware Permutation, FDR). The plan explicitly addresses dataset feasibility, target uncertainty propagation, and schema consistency.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `rdkit`, `pandas`, `scikit-learn`, `shap`, `numpy`, `matplotlib`, `seaborn`, `pyyaml`, `json`, `lightgbm`
**Storage**: Local file system (Parquet/JSON/CSV) under `data/`
**Testing**: `pytest` (unit tests for descriptor calculation, integration tests for pipeline flow)
**Target Platform**: Linux (GitHub Actions Free Tier: multiple CPU cores, sufficient RAM and disk space)
**Project Type**: Data Science Pipeline / Research Library
**Performance Goals**: Full pipeline execution ≤ 4 hours; Memory usage < 6GB during model training.
**Constraints**: Must run on CPU; no GPU acceleration. Must handle missing data via defined imputation or exclusion. Must not invent new constraints not in spec.
**Scale/Scope**: Dataset size N > 500 (estimated from QMOF); A set of molecular descriptors; baseline models.

> **Dataset Feasibility Note**: The plan uses the verified `matsci/qmof` dataset (HuggingFace) as the primary source. This dataset contains the required isotherm parameters (Henry's constant, Langmuir capacity) and molecular structures. It is open-access and programmatically downloadable, ensuring feasibility on CI.
> **Fallback Strategy**: If `matsci/qmof` yields insufficient Type I entries or is unavailable, the pipeline will automatically switch to `coreshare/coref_mof_2019` (CoRE MOF 2019), a verified open-access dataset. If the `isotherm_type` column is missing in either, the pipeline applies a physics-based filter (positive Henry/Langmuir values) to approximate Type I behavior, ensuring the research question remains answerable.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Strategy |
| :--- | :--- |
| **I. Reproducibility** | All random seeds pinned in `code/utils/seeding.py`. External datasets fetched via `datasets.load_dataset("matsci/qmof")` with explicit version tags. `requirements.txt` pins exact versions. |
| **II. Verified Accuracy** | Citations in `research.md` and `paper/` will be validated against the `Verified datasets` block. The `matsci/qmof` and `coreshare/coref_mof_2019` datasets are verified and accessible. |
| **III. Data Hygiene** | Raw data stored in `data/raw/` with checksums. Derivations in `data/processed/` with distinct filenames. No in-place modification. `exclusion_log.json` tracks all dropped rows. |
| **IV. Single Source of Truth** | All figures and stats in the final report will be generated directly from `data/results/` artifacts (e.g., `shap_summary.json`, `null_model_comparison.json`). The `contracts/dataset.schema.yaml` is the SSoT. |
| **V. Versioning** | Content hashes for all `data/` and `code/` artifacts stored in `state/projects/PROJ-245...yaml`. |
| **VI. Physicochemical Descriptor Integrity** | Descriptors calculated *only* via `code/data/descriptors.py` using RDKit. No external descriptor values allowed. |
| **VII. Physicochemical Plausibility** | Feature importance results will be cross-referenced with `LiteratureConsensusList`. A "Plausibility Check" step in `code/interpret/` will flag models that contradict known physics. An independent validation step using 'Kr on Carbon Nanotubes' data is included in Phase 2.6. |

## Project Structure

### Documentation (this feature)
```text
specs/001-predict-adsorption-isotherm-params/
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
│   ├── fetch.py             # Downloads QMOF data
│   ├── descriptors.py       # RDKit descriptor calculation
│   ├── preprocessing.py     # Filtering (Type I), unit normalization
│   ├── imputation.py        # Missing pore volume handling
│   └── split.py             # Material-level train/test split (uses adsorbent_id)
├── models/
│   ├── train.py             # RF, GB, Linear training loop (weighted by uncertainty)
│   ├── null_model.py        # Null model (mean) & Top3 null model
│   └── evaluate.py          # Metrics calculation (R2, RMSE, MAE)
├── interpret/
│   ├── shap_analysis.py     # SHAP plots, summary generation
│   ├── permutation.py       # Cluster-aware permutation testing
│   └── consensus.py         # Comparison with LiteratureConsensusList
├── config/
│   └── consensus_list.json  # LiteratureConsensusList (external benchmark)
├── utils/
│   ├── seeding.py           # Random seed management
│   ├── logging.py           # Runtime log generation
│   └── validators.py        # Schema validation
└── main.py                  # Pipeline orchestration

data/
├── raw/                     # Raw downloads (checksummed)
├── processed/               # Cleaned, imputed, split data
├── validation/              # Exclusion logs, missing descriptor reports
├── results/                 # Model metrics, SHAP summaries, null model results
└── benchmarks/              # runtime_log.json

tests/
├── unit/
├── integration/
└── contract/
```

**Structure Decision**: Single-project structure chosen for a research pipeline. Separation of `data/`, `models/`, and `interpret/` ensures modularity and traceability for the "Single Source of Truth" principle.

## Implementation Phases

### Phase 0: Data Ingestion & Validation
- **0.1 Fetch**: Load `matsci/qmof` via `datasets.load_dataset`.
  - *Fallback*: If empty or fails, load `coreshare/coref_mof_2019`.
- **0.2 Filter (FR-002)**: Filter for Type I isotherms.
  - *Primary*: Filter where `isotherm_type` == "Type I" (or numeric 1).
  - *Secondary*: If column missing, filter where `target_henry` > 0 AND `target_langmuir` > 0.
  - *Tertiary*: If neither, log "Mixed Isotherm" and retain all rows for robustness check.
  - *Exclusion*: Drop rows with missing targets. Log to `exclusion_log.json`.
- **0.3 Validate**: Check against `contracts/dataset.schema.yaml` (SSoT).

### Phase 1: Feature Engineering & Uncertainty Propagation
- **1.1 Descriptors (FR-001)**: Calculate RDKit descriptors (MW, polarizability, etc.).
  - *Merging*: Read `missing_descriptors_*.json` and write `data/validation/missing_descriptors_report.json`.
- **1.2 Uncertainty Capture**: Extract `target_henry_se` and `target_langmuir_se` from the source dataset.
  - *Fallback*: If missing, estimate uncertainty via bootstrap or set uniform weight (1/variance of target).
- **1.3 Imputation**: Handle missing `pore_volume` via group mean (by `adsorbent_id`). Log exclusions to `data/validation/exclusion_log.json`.
  - *Input*: `data/processed/target_filtered.parquet`.
  - *Output*: `data/processed/imputed_dataset.parquet`.
- **1.4 Split (FR-003)**: Use `GroupShuffleSplit` on `adsorbent_id` to ensure no material leakage.

### Phase 2: Modeling & Interpretation
- **2.1 Training (FR-004)**: Train Linear, RF, GB.
  - *Uncertainty Weighting*: Use `sample_weight` in training based on `target_se` (inverse variance weighting).
- **2.2 Null Model**: Train mean-predictor on train set; evaluate on test with 5-fold CV.
  - *Output*: `data/results/null_model_fold_rmses.json` and `data/results/null_model_comparison.json`.
- **2.3 Reduced Model (SC-003)**: Train a model using *only* the top 3 features from SHAP. Compare to null model.
  - *Input*: `data/results/shap_summary.json`.
  - *Output*: `data/results/null_model_top3_rmses.json` and `data/results/reduced_model_metrics.json`.
- **2.4 SHAP & Permutation (FR-005, FR-006, FR-007)**:
  - Generate SHAP summary.
  - **Permutation Strategy**: 
    - **Null Hypothesis**: Adsorbate descriptors have no predictive power for the target given the adsorbent identity.
    - **Cluster-aware Permutation**: For each adsorbent cluster, shuffle the *adsorbate index* (breaking the specific adsorbate-adsorbent pairing) while keeping the adsorbent fixed. This preserves the marginal distribution of targets and adsorbent properties but breaks the feature-target link.
    - Calculate p-values from the null distribution of performance.
    - Apply FDR correction to p-values.
  - *Output*: `data/results/shap_summary.json` and `data/results/permutation_pvalues.json` (containing adjusted p-values).
- **2.5 Consensus Check (FR-008)**: Compare top features to `code/config/consensus_list.json` (loaded from independent literature).
  - *Source*: `consensus_list.json` is curated from independent experimental studies (e.g., Smit et al., 2019) and is static, not derived from training data.
  - *Output*: Report highlighting alignment/divergence.
- **2.6 Independent Validation (Const. VII)**: Evaluate model on 'Kr on Carbon Nanotubes' dataset (verified open source).

### Phase 3: Reporting
- **3.1 Report**: Generate final report with alignment/divergence analysis.
- **3.2 Logging**: Write `data/benchmarks/runtime_log.json` with start time, end time, duration, and step status.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Cluster-aware Permutation** (FR-007) | Standard permutation breaks physical pairing. Cluster-aware (shuffling adsorbate index within adsorbent) tests if descriptors predict the target *beyond* the material context, handling multicollinearity. | Standard permutation ignores material clustering or breaks the adsorbate-adsorbent interaction, leading to invalid null distributions. |
| **Material-level Split** (FR-003) | Prevents data leakage where the model memorizes specific materials rather than learning physics. | Random split would allow the same material in train and test, inflating R² artificially. |
| **FDR Correction** (FR-006) | High-dimensional descriptor space increases false discovery risk. | Uncorrected p-values would likely yield spurious "significant" descriptors. |
| **Uncertainty Weighting** | Targets ($K_H$, $Q_{max}$) are fitted parameters with error. | Ignoring uncertainty leads to overfitting noisy targets and underestimating model error. |

## Data Model & Contracts
The Single Source of Truth for data is `contracts/dataset.schema.yaml`.
- **Key Column**: `adsorbent_id` (String) is used for all splitting and permutation logic.
- **Target Columns**: `target_henry`, `target_langmuir` (Float).
- **Uncertainty Columns**: `target_henry_se`, `target_langmuir_se` (Float).
- **Note**: `contracts/dataset_schema.yaml` is deprecated and contains conflicting field names; all code must use `dataset.schema.yaml`.

## Compute Feasibility
- **CPU-First**: All models (RF, GB) are CPU-tractable for N < 5000.
- **GPU Escape Hatch**: Not required. SHAP and RF/GB are efficient on CPU.
- **Runtime**: Estimated < 2 hours for N=2000.
- **Memory**: Streaming + batch processing ensures < 6GB usage.

## Risk Mitigation
- **Missing Data**: Impute pore volume with group mean (by `adsorbent_id`) or exclude. Log exclusions.
- **Poor Performance**: If R² < 0.2, generate diagnostic report (check for non-linearity, insufficient features).
- **Dataset Unavailability**: `matsci/qmof` is verified. If it fails, fallback to `coreshare/coref_mof_2019`.
- **Missing Uncertainty**: If `target_se` columns are missing, estimate via bootstrap or use uniform weights.
