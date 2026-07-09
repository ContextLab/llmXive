# Implementation Plan: Predicting Plant Stress Response from Publicly Available Proteomic Data

**Branch**: `001-predict-plant-stress-response` | **Date**: 2026-06-27 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-predict-plant-stress-response/spec.md`

## Summary

This project implements a machine learning pipeline to predict plant gene expression patterns from proteomic data under abiotic stresses (drought, salinity, heat). The approach involves ingesting public datasets from NCBI GEO and ProteomeXchange, harmonizing identifiers via biomaRt, imputing missing values using Left-Censored Missing (LCM) methods, and training Random Forest and Support Vector Regression (SVR) models.

**Critical Constraint**: The pipeline is designed to **HALT** biological modeling (SC-001, SC-002) if no valid paired plant proteomic/transcriptomic data is found in the verified sources. If data exists but is small (n < 50), the plan switches to Leave-One-Out Cross-Validation (LOOCV). The plan strictly adheres to CPU-only constraints (GitHub Actions free-tier) and ensures all Functional Requirements (FR-001 to FR-008) and Success Criteria (SC-001 to SC-005) are addressed with explicit mapping.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn`, `pandas`, `numpy`, `biomaRt` (via `rpy2` or R script invocation), `matplotlib`, `seaborn`, `wget`/`curl` (system).  
**Storage**: Local file system (`data/raw`, `data/processed`, `results`).  
**Testing**: `pytest` (unit tests for data pipelines, integration tests for model training).  
**Target Platform**: Linux (GitHub Actions free-tier runner: a low-resource CPU configuration with approximately 7 GB RAM and no GPU).  
**Project Type**: Data Science Pipeline / Research Tool.  
**Performance Goals**: Complete full pipeline (ingestion to reporting) within 6 hours; peak memory < 7 GB.  
**Constraints**: No GPU; no large model training from scratch; strict adherence to verified dataset URLs; no modification of raw data in place.  
**Scale/Scope**: Processing of public datasets (Arabidopsis, rice, wheat) under multiple stress conditions. **Note**: If no valid paired data is found, the project terminates with a 'Data Unavailable' report.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Principle | Compliance Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/`. Data fetched via deterministic scripts. `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **PASS** | Citations in `research.md` restricted to the provided "Verified datasets" block. No URLs invented. |
| **III. Data Hygiene** | **PASS** | Raw data stored in `data/raw` with checksums. Transformations create new files in `data/processed`. No PII expected in public plant data. |
| **IV. Single Source of Truth** | **PASS** | All figures generated from `code/` output. No hand-typed statistics in reports. |
| **V. Versioning Discipline** | **PASS** | Artifacts tracked via content hashes in `state/` YAML. |
| **VI. Cross-Validation Integrity** | **PASS** | Plan explicitly includes 5-fold CV (or LOOCV if n<50) for within-stress and held-out stress splits for cross-stress. |
| **VII. Computational Resource Discipline** | **PASS** | Models limited to `RandomForest` and `SVR` (CPU-optimized). Runtime metrics logged to `runtime_metrics.json`. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-plant-stress-response/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    └── model_output.schema.yaml
```

### Source Code (repository root)

```text
code/
├── data/
│   ├── ingest.py        # FR-001: Download and initial parsing
│   ├── preprocess.py    # FR-002, FR-003: Normalization, LCM, biomaRt merge
│   └── split.py         # FR-005: Train/test split logic
├── models/
│   ├── train.py         # FR-004, FR-005: RF/SVR training, CV, cross-stress eval
│   ├── evaluate.py      # FR-005: Null model, Raw Feature Baseline (T020), Shuffled Baseline (T021)
│   └── importance.py    # FR-006: Feature importance extraction
├── viz/
│   └── plots.py         # FR-007: Scatter, confusion, heatmaps
├── utils/
│   ├── checksums.py     # Constitution III
│   └── logger.py        # Logging setup
├── main.py              # Orchestration script
└── requirements.txt     # Dependency pinning

tests/
├── contract/            # Schema validation tests
├── integration/         # Pipeline end-to-end tests
└── unit/                # Individual function tests

data/
├── raw/                 # Downloaded raw files (checksummed)
└── processed/           # Cleaned, merged matrices
```

**Structure Decision**: A single `code/` directory structure is selected to minimize overhead and align with the "Data Science Pipeline" project type. This allows for straightforward data flow from `ingest` to `models` to `viz` without complex inter-service communication, ensuring the 6-hour runtime limit is met by reducing I/O latency.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **R (biomaRt) via rpy2** | FR-003 requires `biomaRt` for identifier mapping which is native to R. | Pure Python alternatives (e.g., `mygene`) lack the specific `biomaRt` version and reliability required for plant-specific mappings (UniProt to Ensembl). |
| **LCM Imputation** | FR-002 requires Left-Censored Missing imputation, which is standard in proteomics but not in generic `sklearn` imputers. | Generic imputation (mean/median) would violate FR-002 and introduce bias in low-abundance protein detection. |
| **Stress-Shuffled Baseline** | SC-002 requires measuring the 'drop in R²' to isolate stress-specificity. | A 'Raw Feature' baseline (ignoring stress) is a category error; it measures general proteome-expression links, not stress-specificity. The Shuffled Baseline (permuting stress labels) is required to test the null hypothesis that 'stress identity drives prediction'. |

## Plan Completeness & Methodological Rigor

### FR/SC Mapping

| ID | Type | Description | Plan Phase/Step Addressing It |
|:---|:---|:---|:---|
| **FR-001** | FR | Download GEO/ProteomeXchange, select largest n, break ties by date. | `code/data/ingest.py`: Implements selection logic; logs source and selection criteria. |
| **FR-002** | FR | Normalize, filter (<50% detection), LCM imputation. | `code/data/preprocess.py`: Implements filtering threshold and LCM algorithm (deferred numeric parameters). |
| **FR-003** | FR | Merge via biomaRt (-10), log drops. | `code/data/preprocess.py`: Calls `biomaRt`; logs unmatched row counts. |
| **FR-004** | FR | Train RF and SVR on CPU. | `code/models/train.py`: Uses `RandomForestRegressor` and `SVR` (no CUDA). |
| **FR-005** | FR | 5-fold CV, cross-stress eval, null model, shuffling control. | `code/models/train.py` (CV), `code/models/evaluate.py` (Cross-stress & Shuffled Baseline). |
| **FR-006** | FR | Feature importance plots (top-ranked features)

The research question remains: What are the most influential features driving the model's predictions?
The method remains: We will employ permutation-based feature importance analysis to rank and visualize the contribution of each input variable.
References: [Preserve existing citations verbatim]. | `code/models/importance.py`: Extracts and ranks; `code/viz/plots.py` renders. |
| **FR-007** | FR | Scatter, confusion, runtime metrics. | `code/viz/plots.py`: Generates PNGs; `main.py` logs metrics to `runtime_metrics.json`. |
| **FR-008** | FR | Record runtime/memory. | `main.py`: Uses `psutil` and `time` to log to JSON. |
| **SC-001** | SC | R² vs Null Model (mean). | `code/models/evaluate.py`: Calculates Null Model R²; compares to RF/SVR R². |
| **SC-002** | SC | Cross-stress R² drop (Stress-Specificity). | `code/models/evaluate.py`: **T020: Train Raw Feature Baseline** (features only, no stress conditioning). **T021: Train Stress-Shuffled Baseline**. Calculates `Drop = R²(Within-Stress) - R²(Raw Feature Baseline)` and `Drop = R²(Within-Stress) - R²(Shuffled Baseline)`. Uses Permutation Test for significance. |
| **SC-003** | SC | Runtime < 6h, RAM < 7GB. | `main.py`: Enforces early stopping if thresholds approached; logs final metrics. |
| **SC-004** | SC | Data completeness % (merged/initial). | `code/data/ingest.py` & `preprocess.py`: Logs counts at each stage; calculates percentage. |
| **SC-005** | SC | No circular dependencies. | `code/data/split.py`: Ensures stress labels are strictly separated in train/test splits. |

### Statistical Rigor & Dataset Fit

- **Dataset Variable Fit**: The plan explicitly acknowledges the risk that public datasets may lack matched proteomic/transcriptomic pairs. `research.md` will verify the availability of *paired* samples for Arabidopsis/Rice/Wheat under the specified stresses before modeling.
  - **Decision Tree**:
    1.  **No Valid Paired Data**: **HALT** biological modeling. Report "Data Unavailable" (SC-004).
    2.  **Valid Data Exists, n < 50 per fold**: Switch to **Leave-One-Out Cross-Validation (LOOCV)**. Flag results as "Exploratory/High-Variance".
    3.  **Valid Data Exists, n >= 50**: Proceed with **5-fold CV**.
- **Multiple Comparisons**: When evaluating cross-stress generalization across multiple stress pairs, a **Permutation Test** is used.
  - **Null Hypothesis**: The distribution of R² differences between within-stress and cross-stress splits is zero.
  - **Test Statistic**: Observed mean R² drop.
  - **Permutation Unit**: Stress labels are permuted *within* the paired sample set 1000 times to generate the null distribution.
  - **Correction**: Bonferroni correction applied to p-values derived from the permutation test.
- **Power & Sample Size**: Given the reliance on public data, sample sizes are fixed by availability. The plan explicitly defines the fallback to LOOCV for small datasets (n < 50) to ensure statistical validity, avoiding the instability of 5-fold CV on small samples.
- **Causal Inference**: The plan frames all results as **associational**. No claims of causality will be made.
- **Collinearity**: If predictors (proteins) are derived from the same pathway or are highly correlated, the plan will report feature importance descriptively and acknowledge the inability to isolate independent effects due to collinearity.
- **Baseline Validity (SC-002)**: The plan implements two distinct baseline controls to disentangle general proteome-expression links from stress-specific signatures:
  - **Task T020 (Raw Feature Baseline)**: Train a model using only protein features, ignoring stress labels entirely. This measures the general correlation between proteome and transcriptome.
  - **Task T021 (Stress-Shuffled Baseline)**: Train a model where stress labels are randomly shuffled *before* the cross-stress test. This tests the null hypothesis that "stress identity is the sole driver of prediction".
  - **Metric Calculation**: The "drop in R²" required by SC-002 is calculated by comparing the Within-Stress model performance against the **Raw Feature Baseline (T020)**. A significant drop indicates the model leverages stress-specific information beyond general proteome-expression correlation. The Shuffled Baseline (T021) serves as a secondary control for label leakage.

## Compute Feasibility

- **Hardware**: The plan assumes multiple CPU cores and sufficient RAM.
- **Libraries**: `scikit-learn` (CPU-optimized), `pandas` (chunked reading if necessary), `matplotlib`.
- **Methodology**:
  - **Data**: If raw data exceeds 7 GB, `preprocess.py` will implement on-disk streaming or sampling to fit into RAM.
  - **Models**: `RandomForest` and `SVR` are selected for their CPU efficiency. No deep learning or GPU acceleration is used.
  - **Runtime**: The pipeline is designed to complete within 6 hours. If training exceeds a predetermined duration threshold, an early-stopping mechanism will save partial results. (checkpointing).
  - **Data Availability**: If the ingestion step fails to find valid paired data, the pipeline terminates early, saving compute resources.

## Constitution Check (Final)

All principles are addressed. The plan includes a specific strategy for the unresolved concern regarding **SC-002** (Cross-Stress R² drop) by implementing a **Raw Feature Baseline (Task T020)** and a **Stress-Shuffled Baseline (Task T021)**. The plan also explicitly handles the **Data Availability** constraint by defining a "HALT" path if no valid data is found.