# Implementation Plan: Predicting the Influence of Alloying on the Glass Transition Temperature of Metallic Glasses

**Branch**: `001-predict-tg-metallic-glasses` | **Date**: 2024-05-21 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-predicting-the-influence-of-alloying-on/spec.md`

## Summary

This project implements a CPU-tractable machine learning pipeline to predict the glass transition temperature ($T_g$) of metallic glasses based on alloy composition. The system ingests public datasets (contingent on verification), computes atomic-scale descriptors (radius mismatch, electronegativity difference, VEC), and trains a Gradient Boosting Regressor using Leave-One-Family-Out (LOFO) cross-validation. The plan strictly adheres to the constraint of running on free-tier GitHub Actions (limited CPU, 7GB RAM) and ensures all findings are framed as associational, with rigorous statistical validation (Bonferroni correction, iterative VIF remediation, bootstrapping). **Note: Data ingestion is conditional upon successful verification of the primary Zenodo DOI (10.5281/zenodo.10043838). If verification fails, the pipeline halts with a DATA_UNAVAILABLE error. No synthetic data is used.**

## Technical Context

**Language/Version**: Python 3.10  
**Primary Dependencies**: `pandas`, `scikit-learn`, `numpy`, `matplotlib`, `seaborn`, `mendeleev==0.31.0` (pinned for fixed periodic table data), `pyyaml`, `jsonschema`  
**Storage**: Local CSV/Parquet files in `data/` (raw and processed); model artifacts in `artifacts/`  
**Testing**: `pytest` (unit tests for descriptors, integration tests for pipeline)  
**Target Platform**: Linux (GitHub Actions runner)  
**Project Type**: Data Science / Computational Materials Science  
**Performance Goals**: Complete full pipeline (ingestion to reporting) within 6 hours on 2 vCPU; memory usage < 7 GB.  
**Constraints**: No GPU; no causal language; strict adherence to LOFO split; Bonferroni correction on correlations.  
**Scale/Scope**: Single dataset ingestion, descriptor computation, model training, and statistical reporting.

> Domain-specific empirical specifics (exact counts, dataset sizes) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Note |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/`; datasets fetched from canonical Zenodo DOIs; `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **BLOCKED** | **Status:** The project cannot proceed until the Reference-Validator confirms DOI 10.5281/zenodo.10043838 is reachable and contains valid Tg/composition data. If unreachable, the project halts. No review points can be awarded until this is resolved. |
| **III. Data Hygiene** | **PASS** | Raw data preserved in `data/raw/`; checksums recorded; derived data in `data/processed/` with derivation logs. |
| **IV. Single Source of Truth** | **PASS** | All metrics stored in `data/` JSON artifacts; figures generated directly from these artifacts. Schema enforcement via `jsonschema` in `ingest.py` and `analyze.py`. |
| **V. Versioning Discipline** | **PASS** | Content hashes tracked in `state/projects/PROJ-342-predicting-the-influence-of-alloying-on-.yaml`; artifacts versioned by commit hash. The Advancement-Evaluator Agent updates this file upon artifact changes. |
| **VI. Descriptor Consistency** | **PASS** | Descriptors computed by a single `code/descriptor_engine.py` using `mendeleev==0.31.0` (pinned) to ensure fixed periodic table data. |
| **VII. Model Evaluation Transparency** | **PASS** | Metrics (R², MAE) and CV splits stored in `data/`; plots generated from stored results. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-tg-metallic-glasses/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output (Loaded by code/ via relative path)
    ├── dataset.schema.yaml
    └── artifact.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-342-predicting-the-influence-of-alloying-on-/
├── code/
│   ├── __init__.py
│   ├── ingest.py               # Data loading and cleaning (FR-001) - Enforces dataset.schema.yaml
│   ├── descriptors.py          # Atomic property computation (FR-002, VI)
│   ├── train.py                # Model training, LOFO, GridSearch (FR-003)
│   ├── analyze.py              # Sensitivity, VIF (iterative), Bonferroni, Bootstrapping (FR-006-009) - Enforces artifact.schema.yaml
│   └── report.py               # Report generation (FR-004)
├── data/
│   ├── raw/                    # Downloaded datasets (checksummed)
│   └── processed/              # Cleaned CSVs, descriptor tables
├── artifacts/
│   ├── models/                 # Pickled sklearn models
│   └── metrics/                # JSON logs of performance
├── tests/
│   ├── unit/                   # Descriptor logic tests
│   └── integration/            # Pipeline end-to-end tests
├── specs/001-predicting-the-influence-of-alloying-on/contracts/
│   ├── dataset.schema.yaml     # Validation schema for data
│   └── artifact.schema.yaml    # Validation schema for results
└── requirements.txt
```

**Structure Decision**: Single project structure selected. The workflow is linear (Ingest -> Describe -> Train -> Analyze -> Report), making a monolithic `code/` directory with modular scripts optimal for CI execution. Contracts are located in `specs/.../contracts/` and loaded by scripts via relative path resolution (e.g., `../specs/.../contracts/`).

**Contract Enforcement**: The `ingest.py` and `analyze.py` scripts will enforce these schemas using `jsonschema` to ensure the 'Single Source of Truth' (Principle IV) is maintained at the data ingestion and artifact generation stages.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **LOFO Split** | Essential for generalization to unseen alloy families (FR-003). | Standard K-Fold would leak family information, inflating performance metrics and violating the research goal. |
| **Bonferroni Correction** | Required for multiple hypothesis testing on correlations (FR-008). | FDR is statistically weak for N=3 tests; Bonferroni is more appropriate for small hypothesis sets. |
| **Iterative VIF Remediation** | Required to ensure model stability (FR-007). | A simple diagnostic flag without action leaves the model unstable and results invalid. |

## FR/SC Coverage Map

| Requirement ID | Plan Phase/Step | Description |
| :--- | :--- | :--- |
| **FR-001** | `ingest.py` | Load Zenodo 10.5281/zenodo.10043838. Halt if unreachable. Drop missing Tg/composition. |
| **FR-002** | `descriptors.py` | Compute radius mismatch, electronegativity diff, VEC. Log mean radius (diagnostic only). |
| **FR-003** | `train.py` | Train GradientBoostingRegressor with LOFO. Grid search (≤10 combos). |
| **FR-004** | `report.py` | Explicitly state "These findings are associational only". |
| **FR-005** | Pipeline Config | Runtime < 6h, RAM < 7GB. |
| **FR-006** | `analyze.py` | Sensitivity sweep `max_depth` ∈ {3, 5, 7}. Report variance. |
| **FR-007** | `analyze.py` | Calculate VIF. If >5, drop highest VIF feature iteratively until all <5. |
| **FR-008** | `analyze.py` | Apply Bonferroni correction (α ≤ 0.05) to 3 pairwise correlations. |
| **FR-009** | `analyze.py` | Calculate Pearson/Spearman correlations. |
| **SC-001** | `analyze.py` | Compare R² against null model (mean prediction). |
| **SC-002** | `analyze.py` | Bootstrap multiple resamples for feature importance stability. |
| **SC-003** | `ingest.py` | Log retention rate (valid records / raw records). |
| **SC-004** | CI Logs | Monitor CPU time and RAM peak. |