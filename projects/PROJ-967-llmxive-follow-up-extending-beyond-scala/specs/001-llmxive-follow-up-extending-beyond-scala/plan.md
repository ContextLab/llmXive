# Implementation Plan: llmXive Follow-up: Teacher Entanglement vs. Scalar Distillation Loss

**Branch**: `001-llmxive-entanglement-analysis` | **Date**: 2026-07-11 | **Spec**: `specs/001-llmxive-follow-up-extending-beyond-scala/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-follow-up-extending-beyond-scala/spec.md`

## Summary

This feature implements a statistical analysis pipeline to test the hypothesis that "structural entanglement" in teacher model score distributions (variance, entropy, eigenvalues across rubric dimensions) predicts the "dimensional fidelity loss" of a scalar-distilled student model. The approach involves ingesting the Z-Reward evaluation dataset, engineering statistical features from teacher outputs, calculating fidelity loss against human annotations, and training a CPU-based Random Forest regressor with cross-validation and permutation testing to quantify the relationship.

**FR-002 Interpretation Note**: The spec requires "dominant eigenvalue for each sample". Mathematically, a covariance matrix (and thus eigenvalues) cannot be computed for a single 4-dimensional vector (0 degrees of freedom). This plan explicitly **re-interprets** FR-002: the "dominant eigenvalue" is computed as a **global** statistic (eigenvalue of the covariance matrix of the 4 dimensions across the entire dataset) and treated as a **context-only** feature. The **per-sample** structural complexity is instead captured by the **Mahalanobis distance** of the sample's score vector from the global mean. This adaptation is necessary to satisfy the mathematical constraints while preserving the intent of measuring structural deviation.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas==2.2.0`, `numpy==1.26.0`, `scikit-learn==1.5.0`, `scipy==1.13.0`, `pyyaml==6.0.1`  
**Storage**: Local file system (CSV/JSON/Parquet) within `data/raw`, `data/processed`, `results`  
**Testing**: `pytest==8.2.0` with strict type checking via `mypy`  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7GB RAM)  
**Project Type**: Computational research pipeline (CLI scripts)  
**Performance Goals**: Complete ingestion, feature engineering, and model training within 6 hours on CPU; memory usage < 6GB.  
**Constraints**: No GPU available for training; must handle missing data gracefully; must not fabricate results.  
**Scale/Scope**: Analysis of the full available Z-Reward subset that fits in RAM; if larger, stratified sampling is applied.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*Gates determined based on constitution file*

| Principle | Status | Verification Method |
|-----------|--------|---------------------|
| **I. Reproducibility** | PASS | `requirements.txt` pins exact versions; random seeds set in `code/`; data fetched from canonical source. |
| **II. Verified Accuracy** | PASS | All citations in `research.md` will be validated against primary sources; no title-token-overlap < 0.7. |
| **III. Data Hygiene** | PASS | Raw data checksummed; derivations written to new files; PII scan passed. |
| **IV. Single Source of Truth** | PASS | All metrics in `results/results.json` trace to `data/processed` and `code/` scripts. |
| **V. Versioning Discipline** | PASS | Content hashes tracked in `state/` for all artifacts. |
| **VI. Distributional Entanglement Quantification** | ADAPTED | Per-sample covariance impossible; replaced with global covariance + per-sample Mahalanobis distance. Explicitly documented in FR-002 Interpretation Note. |
| **VII. Independent Ground-Truth Fidelity Validation** | PASS | Fidelity loss calculated *only* against human annotations; teacher scores used *only* as predictors. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-beyond-scala/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── features.schema.yaml
│   └── result.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/
├── data/
│   ├── raw/                 # Downloaded Z-Reward dataset files (immutable)
│   └── processed/           # Ingested JSON/Parquet, feature engineering outputs
├── code/
│   ├── __init__.py
│   ├── ingestion.py         # FR-001: Load and align data; FR-006: Exclusion logic
│   ├── features.py          # FR-002: Entanglement score calculation
│   ├── fidelity.py          # FR-003: Fidelity loss calculation
│   ├── train.py             # FR-004: Random Forest training & CV
│   ├── stats.py             # FR-005: Permutation test & metrics
│   └── main.py              # Orchestration script
├── tests/
│   ├── contract/            # Schema validation tests
│   ├── unit/                # Feature calculation unit tests
│   └── integration/         # End-to-end pipeline tests
├── results/
│   ├── model.pkl            # Trained model artifact
│   └── results.json         # Final metrics (R², MAE, p-value)
├── pyproject.toml           # Dependency pins (exact versions)
├── requirements.txt         # Installable list
└── .ruff.toml               # Linting configuration
```

**Structure Decision**: Single-project structure selected to minimize overhead and ensure all artifacts reside in a single, reproducible pipeline. This aligns with the research nature of the project and the constraint of a single CI runner.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The scope is strictly defined by the spec and fits within CPU constraints. | N/A |

## Phase Plan

### Phase 0: Research & Feasibility
- **Task**: Verify dataset availability and variable fit.
- **Action**: Confirm Z-Reward dataset contains all four rubric dimensions and human annotations.
- **Output**: `research.md` with dataset strategy and feasibility assessment.

### Phase 1: Data Model & Contracts
- **Task**: Define schemas for input data, features, and results.
- **Action**: Create YAML schemas in `contracts/`: `dataset.schema.yaml`, `features.schema.yaml`, `result.schema.yaml`.
- **Output**: `data-model.md`, `quickstart.md`, `contracts/*.schema.yaml`.

### Phase 2: Implementation
- **Task**: Implement ingestion, feature engineering, and modeling.
- **Action**: Write scripts in `code/` following the spec.
  - **T002a**: Ingestion (FR-001, FR-006).
  - **T002b**: Exclusion logic implementation (FR-006) - generate `data_quality_report.json`.
  - **T002c**: Feature Engineering (FR-002) - Compute per-sample variance/entropy/skewness/kurtosis; compute global dominant eigenvalue; compute per-sample Mahalanobis distance. Note: FR-002 eigenvalue requirement adapted to global constant.
  - **T002d**: Fidelity Loss (FR-003).
  - **T002e**: Training (FR-004).
  - **T002f**: Validation (FR-005).
- **Output**: Executable scripts, `results/results.json`, `results/model.pkl`, `data_quality_report.json`.

### Phase 3: Validation
- **Task**: Run full pipeline and validate results.
- **Action**: Execute `main.py` on CI runner; verify checksums and schema compliance. Generate `validation_report.json` (SC-005) containing `dimension_presence_matrix`.
- **Output**: Passing CI job, reproducible artifacts, `validation_report.json`.

## Compute Feasibility Strategy

- **CPU-First**: All operations (Random Forest, statistical calculations) are designed for CPU execution. `scikit-learn` is used with `n_jobs=1` or `2` to stay within the 2-core limit.
- **Memory Management**: The Z-Reward dataset (text-only) is estimated to be < 200MB, well within 7GB RAM. If the dataset is larger, chunked loading or streaming is used. If not feasible, a stratified random sample is taken with a fixed seed, and the limitation is documented.
- **No GPU**: No transformer fine-tuning or CUDA kernels are planned. The analysis is purely statistical on pre-computed scores.

## Data Availability Strategy

- **Dataset**: Z-Reward evaluation dataset.
- **Source**: HuggingFace Datasets `z-reward` (or fallback `Dahoas/full-hh-rlhf` if `z-reward` is unavailable).
- **Access**: Programmatic download via `datasets` library.
- **Handling**: If the dataset requires credentials, the pipeline halts. If no open substitute exists, the project is paused.

## Risk Mitigation

- **Missing Data**: Samples with missing human annotations are excluded from training (FR-006) and logged in `data_quality_report.json`.
- **Zero Variance**: Entropy and variance are set to 0 for constant distributions (Edge Case).
- **Collinearity**: Predictors (variance, entropy, etc.) are analyzed for multicollinearity; if high, PCA or feature selection is applied.
- **Fabrication**: No placeholder results are allowed. If training fails, the error is logged, and the pipeline halts.