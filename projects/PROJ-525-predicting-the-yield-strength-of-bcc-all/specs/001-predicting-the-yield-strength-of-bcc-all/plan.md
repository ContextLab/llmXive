# Implementation Plan: Predicting Yield Strength of BCC Alloys

**Branch**: `001-bcc-yield-strength` | **Date**: 2024-05-21 | **Spec**: `specs/001-bcc-yield-strength/spec.md`
**Input**: Feature specification from `specs/001-bcc-yield-strength/spec.md`

## Summary

This feature implements a machine learning pipeline to predict the yield strength of Body-Centered Cubic (BCC) alloys using public data. The approach involves downloading and filtering a multi-principal element alloy (MPEA) database for BCC-phase entries, engineering compositional descriptors (atomic radius mismatch, VEC, mixing entropy/enthalpy), applying log-ratio transformations to address compositional closure, and training/evaluating regression models (Random Forest, Gradient Boosting, Ridge) on a CPU-constrained CI environment. The plan ensures strict adherence to the project constitution regarding reproducibility, data hygiene, and verified accuracy.

**Critical Methodological Update**: To address statistical rigor in small data regimes (N < 1000) and prevent data leakage, the evaluation strategy has been revised. The plan utilizes a **Stratified Train-Test Split

The research question is to determine the generalizability of the model across different data strata. The method involves a stratified split of the dataset into training and testing subsets to maintain class distribution. References: [Insert DOI/arXiv/author-year here].** (as mandated by FR-004) for the outer evaluation layer, with **Nested Cross-Validation** performed strictly within the training set. Confidence Intervals are derived from a **Repeated Stratified K-Fold** (5x5) distribution to ensure statistical validity.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `numpy`, `periodictable`, `pyyaml`, `requests`, `scipy`, `skbio`  
**Storage**: Local CSV/Parquet files under `data/` (checksummed); no external database.  
**Testing**: `pytest` (unit tests for feature engineering, integration tests for pipeline).  
**Target Platform**: GitHub Actions Free Tier (Linux, 2 CPU, 7GB RAM, No GPU).  
**Project Type**: Data Science / Computational Materials Science Library  
**Performance Goals**: Full pipeline execution < 6 hours; Feature engineering < 5 minutes for N=500.  
**Constraints**: No GPU usage; No large-LLM inference; Dataset must be sampled if > 14GB; Strict memory management (<7GB).  
**Scale/Scope**: Dataset size variable, but expected < 1000 entries after BCC filtering.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

1.  **Principle I (Reproducibility)**: Plan mandates pinned `requirements.txt`, fixed random seeds in all ML steps, and deterministic data fetching.
2.  **Principle II (Verified Accuracy)**: The plan defines a 'Verified Source' as one that is either programmatically fetchable OR manually placed with a verified checksum. The Reference-Validator Agent will verify the checksum of the manually placed file against the DOI's known hash. If the DOI is unverified, the pipeline requires manual placement; this is a valid compliance path.
3.  **Principle III (Data Hygiene)**: Plan includes checksum generation for raw and derived data; no in-place modifications; distinct files for raw vs. processed data.
4.  **Principle IV (Single Source of Truth)**: **Traceability Mechanism**: All performance metrics are generated via `code/` execution logs (JSON lines format) and written to `state/projects/PROJ-525...yaml` in a strict JSON format defined by `contracts/model_output.schema.yaml`. A specific script (`code/traceability.py`) extracts metrics from logs and updates the state file. Manual entry is forbidden by the pipeline design.
5.  **Principle V (Versioning)**: Plan explicitly details the content hashing strategy for `state/` artifacts. The SHA-256 hash of the `state/projects/PROJ-525...yaml` file is calculated on the content *excluding* the `content_hash` field itself, and this hash is stored in a separate `state/manifest.yaml` file to avoid recursive definitions.
6.  **Principle VI (Compositional Feature Integrity)**: Plan specifies exact formulas for δ, VEC, entropy, enthalpy in **research.md -> Feature Engineering Strategy**. This section is explicitly referenced here for traceability.
7.  **Principle VII (Crystal-Structure Specificity)**: Plan mandates explicit filtering for "BCC" phase before any modeling; mixed-phase entries are excluded.

## Project Structure

### Documentation (this feature)

```text
specs/001-bcc-yield-strength/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-525-predicting-the-yield-strength-of-bcc-all/
├── data/
│   ├── raw/                 # Downloaded raw data (checksummed)
│   ├── processed/           # Filtered BCC data, feature-engineered data
│   └── logs/                # Rejected entries, error logs
├── code/
│   ├── __init__.py
│   ├── config.py            # Paths, seeds, constants
│   ├── data_ingestion.py    # FR-001, FR-002
│   ├── feature_engineering.py # FR-003, FR-003.1, FR-003.2 + Pre-Analysis Independence Check
│   ├── modeling.py          # Nested CV, FR-005, FR-006
│   ├── traceability.py      # Extracts logs, updates state/manifest.yaml
│   ├── utils.py             # Logging, checksumming
│   └── main.py              # Pipeline orchestrator
├── tests/
│   ├── unit/
│   │   ├── test_feature_engineering.py
│   │   └── test_data_ingestion.py
│   └── integration/
│       └── test_pipeline.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure chosen for simplicity. Data is local to the repo to ensure reproducibility on CI. `code/` contains modular scripts for each functional requirement.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Nested Cross-Validation | Required to avoid high variance in performance estimation for N < 1000 and prevent data leakage from a single holdout split. | A single train-test split (e.g., 80/20) yields unstable metrics for small N and risks overfitting the validation set. |
| Repeated Stratified K-Fold | Required to generate a sufficient distribution of scores for valid Confidence Interval calculation., avoiding the instability of bootstrapping only a small number of points. | Bootstrapping only 5-fold scores is statistically invalid and produces meaningless intervals. |
| Pre-Filter Dimensionality Reduction (PCA) | Required to mitigate overfitting risk for N < 80 by reducing the effective dimensionality of the feature space before model training. | Standard RFE/L1 may not be sufficient for extremely small N with high-dimensional compositional features. |
| Residualization | Required to mitigate multicollinearity between scalar descriptors and ILR coordinates, ensuring geometric independence. | Standard RFE/L1 does not address the structural geometric constraints of the combined feature space. |
| Pre-Analysis Independence Check | Required to detect potential circular validation between thermodynamic parameters and yield strength. | Assuming independence without verification risks data leakage and invalid scientific claims. |

## Statistical Rigor & Success Criteria Alignment

- **Power Limitation**: For N < 80, the plan explicitly acknowledges that statistical power is limited. The success criterion MAE ≤ 50 MPa (SC-002) is conditional: it is only considered met if the model's performance is statistically significantly better than a null model (predicting the mean) and the confidence intervals do not include the null performance.
- **Multiple Comparisons**: When comparing 3 models, a correction (e.g., Bonferroni) will be applied if hypothesis testing on model differences is performed.
- **Causal Inference**: This is an observational study. Claims will be framed as "associational" or "predictive," not causal. No randomization exists in the dataset.
- **Collinearity**: Addressed via Residualization of scalar descriptors against ILR coordinates and PCA for dimensionality reduction.
- **Measurement Validity**: Yield strength values are assumed to be measured under comparable conditions (room temp, standard strain). No normalization for testing conditions is applied (per Assumptions).
- **Confidence Intervals**: Calculated from the distribution of scores (repeats of 5-fold CV) using the percentile method, ensuring statistical validity for small N.