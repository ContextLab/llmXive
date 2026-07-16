# Implementation Plan: Quantifying the Association of Grain Boundary Character with Diffusivity

**Branch**: `001-grain-boundary-diffusivity` | **Date**: 2024-01-15 | **Spec**: `specs/001-quantifying-the-impact-of-grain-boundary/spec.md`
**Input**: Feature specification from `specs/001-quantifying-the-impact-of-grain-boundary/spec.md`

## Summary

This feature implements a data-driven pipeline to **quantify the association** between grain boundary (GB) character and atomic diffusivity in polycrystalline materials. The approach involves downloading atomistic simulation structures and potential files from open repositories (Materials Project, OpenKIM, NIST), parsing geometry files to extract crystallographic descriptors (misorientation, boundary plane, Σ value, boundary width, excess volume), and training a gradient-boosted tree (XGBoost) model to predict diffusivity. 

**Critical Note on Causality**: This study is **observational**. Grain boundaries are not randomly assigned; their character is determined by processing history. Therefore, findings will be framed strictly as **associational** (e.g., "Sigma value is associated with diffusivity") rather than causal. No causal identification strategy (e.g., instrumental variables) is employed.

The plan strictly adheres to the project constitution's requirements for reproducibility, data hygiene, and model interpretability (SHAP), while ensuring all computations fit within the GitHub Actions free-tier CPU constraints (≤2 CPU cores, ≤7 GB RAM).

## Technical Context

**Language/Version**: Python 3.10  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `xgboost`, `shap`, `matplotlib`, `requests`, `pymatgen` (for geometry parsing)  
**Storage**: Local filesystem (`data/raw/`, `data/processed/`, `models/`) with checksums recorded in `state/`.  
**Testing**: `pytest` for unit tests on data parsers and model metrics; `pytest` integration tests for pipeline execution.  
**Target Platform**: Linux (GitHub Actions free-tier runner: **2 CPU cores**, ~7 GB RAM).  
**Project Type**: Computational research pipeline / CLI.  
**Performance Goals**: End-to-end pipeline execution ≤ 6 hours; peak RAM ≤ 7 GB; R² ≥ 0.7 (hypothesis target).  
**Constraints**: No GPU/CUDA; no large-LLM inference; dataset must be sampled if >7 GB; strict handling of missing data (halt if n < 500).  
**Scale/Scope**: Target ≥ 500 valid GB records; A variable number of records depending on available open data.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Note |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All scripts will use pinned random seeds (`np.random.seed`, `xgb.set_seed`). External datasets are fetched via specific API endpoints or static URLs stored in `data/metadata.yaml`. |
| **II. Verified Accuracy** | **PASS** | Citations in `research.md` and `paper/` will be validated against primary sources by the **Reference-Validator Agent**. The R² ≥ 0.7 target is framed as a hypothesis based on community standards, not an absolute guarantee. |
| **III. Data Hygiene** | **PASS** | Raw data files will be checksummed upon download. Transformations (e.g., Rodrigues vector calculation) will write new files. No in-place modification of raw data. |
| **IV. Single Source of Truth** | **PASS** | All figures (SHAP plots, bias test graphs) and statistics (R², RMSE) will be generated programmatically from `code/` and stored in `artifacts/`. No hand-typed numbers in reports. |
| **V. Versioning Discipline** | **PASS** | Artifacts will carry content hashes. The `state` YAML will be updated upon successful pipeline completion. |
| **VI. Dataset Provenance** | **PASS** | `data/metadata.yaml` will record source (Materials Project/OpenKIM/NIST), **exact version identifier** (release tag or commit hash), and retrieval date. |
| **VII. Model Transparency** | **PASS** | SHAP analysis is a mandatory step (FR-005). Feature importance claims will strictly reference `code/interpretability/` outputs. |

## Project Structure

### Documentation (this feature)

```text
specs/001-grain-boundary-diffusivity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── grain_boundary_record.schema.yaml
│   ├── model_output.schema.yaml
│   └── validation_report.schema.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-117-quantifying-the-impact-of-grain-boundary/
├── code/
│   ├── __init__.py
│   ├── download.py              # Data acquisition (Materials Project, OpenKIM, NIST)
│   ├── geometry_parser.py       # NEW: Parse POSCAR/CIF for boundary width, excess volume
│   ├── preprocess.py            # Feature engineering (Rodrigues vectors, Miller indices, collinearity check)
│   ├── train.py                 # XGBoost training with RandomizedSearchCV
│   ├── diagnostics.py           # NEW: Mutual Information and collinearity diagnostics
│   ├── validate.py              # K-fold CV, bias tests, FWER correction
│   ├── interpret.py             # SHAP analysis and sensitivity sweeps
│   └── utils.py                 # Common helpers (checksums, logging)
├── data/
│   ├── raw/                     # Downloaded raw files (checksummed)
│   ├── processed/               # Cleaned, feature-engineered CSVs/Parquet
│   └── metadata.yaml            # Provenance and version info
├── models/
│   └── best_model.json          # Trained XGBoost artifact
├── artifacts/
│   ├── figures/                 # SHAP plots, bias test graphs
│   └── reports/                 # Validation reports (JSON/Markdown)
├── tests/
│   ├── unit/
│   └── integration/
├── requirements.txt             # Pinned dependencies
└── README.md                    # Project overview
```

**Structure Decision**: Single-project CLI structure chosen to align with the computational research nature. `code/` contains modular scripts for each pipeline stage, ensuring testability and reproducibility. `data/` is strictly separated into raw (immutable) and processed (derived) layers.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **K-fold CV + Bias Test + SHAP** | Required by FR-004, FR-005 to ensure scientific validity and interpretability. | A simple train/test split would not satisfy the statistical rigor requirements (bias detection, stability assessment) mandated by the spec. |
| **Rodrigues Vector Encoding** | Required by FR-002 to correctly handle crystallographic symmetry. | Simple angle/axis representation loses symmetry information and may introduce discontinuities in the feature space. |
| **Geometry Parsing** | Required by FR-002 to compute boundary width and excess volume. | These descriptors are not available in standard API aggregates and must be derived from raw simulation geometry. |
| **Collinearity Diagnostics** | Required by FR-007 to handle definitionally related predictors. | Ignoring collinearity would lead to unstable feature importance estimates and invalid scientific claims. |
| **Data Insufficiency Halt** | Required by FR-006 to prevent statistically invalid modeling on small datasets. | Graceful degradation (e.g., using a simpler model) is out of scope; the methodology (XGBoost) requires n ≥ 500 for valid k=5 CV. |

## Phase Plan

### Phase 0: Data Acquisition & Reality Check
1.  **Download**: Fetch raw structures (POSCAR, CIF) and potential files from Materials Project, OpenKIM, NIST.
2.  **Reality Check**: Log the count of retrieved records. If < 500 records with *all* required fields (including parsed geometry), **HALT** with exit code 1 and a 'Data Insufficiency' error.
3.  **Provenance**: Record exact version tags and checksums in `data/metadata.yaml`.

### Phase 1: Geometry Parsing & Feature Engineering
1.  **Parse Geometry**: Use `code/geometry_parser.py` to extract boundary width and excess volume from raw files.
2.  **Encode**: Convert misorientation to Rodrigues vectors, boundary plane to Miller indices.
3.  **Tag Simulation Method**: Add `simulation_method` (DFT, MD, KMC) and `potential_id` as features to control for systematic errors.
4.  **Collinearity Check**: Run `code/diagnostics.py` to compute Mutual Information (MI) between misorientation and Σ value. If MI > 0.8, flag for feature selection (retain only one or use a combined feature).

### Phase 2: Model Training
1.  **Split**: //15 Train/Val/Test split.
2.  **Tune**: `RandomizedSearchCV` with k=5 CV.
3.  **Train**: XGBoost on the training set.

### Phase 3: Validation & Interpretation
1.  **Bias Test**: Regression of y_true ~ y_pred.
2.  **SHAP**: Generate feature importance and summary plots.
3.  **Sensitivity Sweep**: Test R² thresholds within a moderate-to-strong range.
4.  **Report**: Generate `validation_report.json` and `threshold_sweep_report.json`.

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
| :--- | :--- | :--- | :--- |
| **Data Insufficiency** | High | Critical | Pipeline halts with code 1 and logs exact count (FR-006). |
| **API Rate Limiting** | Medium | Medium | Implement exponential backoff in `download.py`. |
| **Missing Variables** | High | Critical | Strict filtering; records with missing fields are excluded. If count < 500, halt. |
| **High CV Variance** | Medium | Medium | Report standard deviation of R². If > 0.1, flag in report as "Unstable Model." |
| **Heterogeneous Simulation Methods** | High | Medium | Include `simulation_method` as a feature to control for systematic bias. |