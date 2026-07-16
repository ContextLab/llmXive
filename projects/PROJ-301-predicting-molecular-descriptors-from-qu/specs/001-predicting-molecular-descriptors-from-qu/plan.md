# Implementation Plan: Predicting Molecular Descriptors from Quantum Chemical Calculations with Machine Learning

**Branch**: `001-predict-molecular-descriptors` | **Date**: 2026-07-08 | **Spec**: `specs/001-predict-molecular-descriptors/spec.md`
**Input**: Feature specification from `/specs/001-predict-molecular-descriptors/spec.md`

## Summary

This feature implements a comparative machine learning pipeline to predict molecular descriptors (dipole moment, HOMO, LUMO) from the QM9 dataset. The approach contrasts 2D topological representations (Morgan fingerprints) against 3D geometric representations (graph features derived from DFT-optimized coordinates) using Random Forest Regressors. The plan ensures strict adherence to the project's computational constraints (CPU-only, limited RAM, 6h runtime) and addresses the specific "failure boundary" hypothesis by quantifying relative error increases between the two model families.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `rdkit`, `scikit-learn`, `pandas`, `numpy`, `pyarrow`, `huggingface_hub`, `matplotlib`, `seaborn`, `scipy`
**Storage**: Local filesystem (`data/raw`, `data/processed`, `artifacts`)
**Testing**: `pytest` (unit tests for feature extraction logic, integration tests for pipeline flow)
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, ~7 GB RAM)
**Project Type**: Data Science / Computational Chemistry Pipeline
**Performance Goals**: Complete end-to-end pipeline (download -> extract -> train -> evaluate) within 6 hours; peak memory < 7 GB.
**Constraints**: No GPU; no heavy deep learning; strict downsampling if memory exceeds available capacity.; all random seeds pinned.
**Scale/Scope**: Subset of QM9 (target a representative scale for tractability).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Spec Amendments & Overrides

**T009.1 - Data Source Amendment (Supersedes FR-001)**:
FR-001 mandates downloading from Harvard Dataverse (doi:10.7910/DVN/28075). Due to verified accuracy constraints and CI compatibility, this plan **amends FR-001** to use the verified HuggingFace mirror (`) as the canonical source. This amendment is recorded here to satisfy the "Single Source of Truth" principle. The HuggingFace dataset is a verified, direct mirror of the QM9 data structure and contains the required DFT properties.

**FR-007 Interpretation**:
The Spec refers to "theoretical lower bound". Scientifically, the true theoretical lower bound is the Bayes error rate. For this project, we interpret FR-007 as requiring the **Mean Predictor Error (Zero-Order Baseline)** (predicting the mean of the training set) to contextualize the 3D model's performance against a trivial baseline. This is explicitly documented as such.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Rationale / Action |
|-----------|--------|--------------------|
| **I. Reproducibility** | PASS | Plan mandates `random_state` pinning, explicit dataset versioning via HuggingFace commit hash, and isolated `requirements.txt`. |
| **II. Verified Accuracy** | PASS | Plan explicitly amends FR-001 (T009.1) to use the verified HuggingFace URL. All citations are restricted to this verified source. |
| **III. Data Hygiene** | PASS | Plan includes checksumming of raw downloads and separation of raw vs. processed data. |
| **IV. Single Source of Truth** | PASS | Metrics (MAE, RMSE) will be generated programmatically and stored in JSON/CSV artifacts; no hand-typed numbers in reports. |
| **V. Versioning Discipline** | PASS | Content hashes for artifacts will be recorded in the project state file upon completion. |
| **VI. Representation Fidelity Traceability** | PASS | The plan explicitly defines the "relative error increase" metric (SC-002) and maps it to the Failure Boundary task (T023). |
| **VII. Computational Resource Discipline** | PASS | The plan enforces a hard memory limit check and downsampling strategy before training begins. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-molecular-descriptors/
├── plan.md # This file
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
├── contracts/ # Phase 1 output
└── tasks.md # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-301-predicting-molecular-descriptors-from-qu/
├── data/
│ ├── raw/ # Downloaded QM9 parquet files
│ ├── processed/ # Extracted features (npy/csv), labels
│ └── checksums.json # Artifact integrity records
├── code/
│ ├── __init__.py
│ ├── requirements.txt
│ ├── download.py # FR-001 (Amended): Data acquisition
│ ├── extract.py # FR-002: Feature extraction (2D/3D)
│ ├── train.py # FR-003: RF Training + CV
│ ├── analyze.py # FR-004, FR-005, FR-007: Metrics & Plots
│ └── utils/
│ ├── memory_monitor.py # FR-006: Memory enforcement + logging
│ └── parsers.py # XYZ/SMILES parsing
├── tests/
│ ├── unit/
│ │ ├── test_extract.py
│ │ └── test_parsers.py
│ └── integration/
│ └── test_pipeline.py
├── artifacts/
│ ├── models/ #.pkl files
│ ├── metrics/ #.json,.csv
│ └── plots/ #.png (parity plots)
└── README.md
```

**Structure Decision**: Single-project structure (`code/`, `data/`, `tests/`) selected to minimize overhead and simplify CI/CD configuration for the data science pipeline.

## Contract Mapping

Every contract schema is exercised by a specific plan element:

| Contract Schema | Functional Requirement | Plan Element (Task) |
|-----------------|------------------------|---------------------|
| `dataset.schema.yaml` | FR-001 (Data Acquisition) | T009: Download & Verify |
| `feature_schema.schema.yaml` | FR-002 (Feature Extraction) | T011: Generate 2D/3D Features |
| `model_result.schema.yaml` | FR-003 (Model Training) | T015/T016: Train RF Models |
| `evaluation_result.schema.yaml` | FR-004, FR-005, FR-007 | T021/T023: Analysis & Failure Boundary |
| `molecule.schema.yaml` | FR-002 (Data Validation) | T010: Parse & Validate Molecules |

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **N/A** | The Constitution Check passed all gates. The computational constraints (7GB RAM) are handled by the downsampling strategy in `utils/memory_monitor.py` and the choice of Random Forest (CPU-tractable) rather than deep learning, which would violate resource constraints. | |

## Phase 1: Data Acquisition & Preparation

### Task T009: Download & Verify (Amended FR-001)
**Description**: Download the QM9 dataset from the verified HuggingFace source (T009.1 Amendment). Compute checksums and verify integrity.
**Dependencies**: None.
**Output**: `data/raw/qm9_full.parquet`, `data/checksums.json`, `artifacts/metrics/resource_usage.json` (logging memory/time).
**Success Criteria**: File exists; checksum matches; `resource_usage.json` logs peak memory < 7GB.

### Task T010: Parse & Validate
**Description**: Parse the parquet file, validate molecule structures, and drop rows with missing DFT labels (mu, homo, lumo) or invalid geometry.
**Dependencies**: T009.
**Output**: `data/processed/molecules_cleaned.parquet`.

### Task T011: Generate Features (FR-002)
**Description**: Generate 2D Morgan fingerprints and 3D graph features.
**Memory Constraint**: Monitor memory. If > 6.5 GB, perform **Stratified Random Sampling** (strata: atom count, polarity) to reduce sample size by [deferred] and re-run. This ensures chemical diversity is preserved while satisfying SC-004.
**Dependencies**: T010.
**Output**: `data/processed/2d_features.npy`, `data/processed/3d_graphs.pkl`, `data/processed/labels.npy`.

## Phase 2: Model Training & Validation

### Task T015: Train 2D Model (FR-003)
**Description**: Train Random Forest on low-dimensional features with k-fold cross-validation.
**Dependencies**: T011.
**Output**: `artifacts/models/2d_model.pkl`, `artifacts/metrics/cv_2d.json`.

### Task T016: Train 3D Model (FR-003)
**Description**: Train Random Forest on multi-dimensional spatial features with k-fold cross-validation.
**Dependencies**: T011.
**Output**: `artifacts/models/3d_model.pkl`, `artifacts/metrics/cv_3d.json`.

### Task T017: Aggregate Metrics
**Description**: Calculate mean MAE, RMSE, and std MAE per fold. Generate `stability_report.json`.
**Dependencies**: T015, T016.
**Output**: `artifacts/metrics/cv_metrics.json`, `artifacts/metrics/stability_report.json`.
**Note on SC-005**: The pipeline **measures** the stability ratio (std/mean). If > 5%, a flag is set in the report, but the pipeline **continues** to generate downstream artifacts (T021-T024) to allow for analysis of *why* stability failed. SC-005 is a success criterion for the *model*, not a hard gate for the *pipeline*.

## Phase 3: Analysis & Reporting

### Task T021: Compute Baselines (FR-007)
**Description**: Calculate the **Mean Predictor Error** (predicting the mean of the training set) for each descriptor. This serves as the practical lower bound (Zero-Order Baseline) to contextualize model performance.
**Dependencies**: T011.
**Output**: `artifacts/metrics/baseline_error.json`.

### Task T022: Generate Predictions
**Description**: Generate predictions for the test set (out-of-fold) for both models. Store per-molecule errors.
**Dependencies**: T015, T016.
**Output**: `artifacts/metrics/test_predictions.json` (includes `error_2d`, `error_3d` arrays per molecule).

### Task T023: Failure Boundary Report (FR-005, SC-002)
**Description**:
1. Calculate Relative Error Increase (REI) = (MAE_2D - MAE_3D) / MAE_3D for each descriptor.
2. Perform statistical testing on **per-molecule errors** (N~2000) using **Wilcoxon signed-rank test** (if normality violated) or **paired t-test**.
3. Apply **Bonferroni correction** (α = 0.05 / 3 ≈ 0.0167).
4. Determine "Failure Boundary": **REI ≥ 10% OR p-value < 0.0167**.
5. **Scope Qualification**: Explicitly state that this boundary applies to **DFT-optimized geometries** and may not generalize to noisy experimental geometries.
**Dependencies**: T022, T017.
**Output**: `artifacts/metrics/comparison_table.csv`, `artifacts/plots/parity_*.png`, `artifacts/metrics/failure_boundary.json`.

### Task T024: Generate Final Report
**Description**: Compile all metrics, plots, and logs into a final summary.
**Dependencies**: T021, T023.
**Output**: `artifacts/report.md`.

## Success Criteria Measurement Plan

| ID | Measurement | Source Artifact | Threshold/Action |
|----|-------------|-----------------|------------------|
| SC-001 | Prediction Error (MAE/RMSE) | `comparison_table.csv` | Measured against DFT. |
| SC-002 | Relative Error Increase | `comparison_table.csv` | Measured; triggers Failure Boundary flag if ≥ 10% or p < 0.0167. |
| SC-003 | Runtime | `resource_usage.json` | Must be ≤ 6 hours. |
| SC-004 | Peak Memory | `resource_usage.json` | Must be ≤ 7 GB (enforced by T011). |
| SC-005 | CV Stability | `stability_report.json` | Measured (std/mean). Flag if > 5%. Pipeline continues. |

## Limitations & Scope

- **DFT Self-Consistency**: The 3D model uses DFT-optimized geometries to predict DFT properties. The "Failure Boundary" identified is specific to this DFT-consistent context and may not hold for noisy experimental geometries.
- **Statistical Power**: The use of per-molecule errors (N~large-scale) ensures high power for the statistical test, unlike fold-aggregate tests (N=5).
- **Baseline Interpretation**: The "Theoretical Lower Bound" is implemented as the Mean Predictor Error (Zero-Order Baseline), not the Bayes error rate, due to data limitations.