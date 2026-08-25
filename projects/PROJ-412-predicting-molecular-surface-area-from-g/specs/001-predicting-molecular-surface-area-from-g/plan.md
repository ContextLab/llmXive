# Implementation Plan: Predicting Molecular Surface Area from Graph Convolutional Networks

**Branch**: `001-predict-molecular-surface-area` | **Date**: 2026-07-14 | **Spec**: `specs/001-predicting-molecular-surface-area/spec.md`
**Input**: Feature specification from `/specs/001-predicting-molecular-surface-area/spec.md`

## Summary

This project implements a pipeline to predict molecular surface area (SASA) using Graph Convolutional Networks (GCNs) trained on 2D topological features. The core research question investigates whether 2D graph topology contains sufficient information to predict 3D geometric properties, compared against a Geometry-Based Baseline that explicitly uses 3D conformer data (volume, shape indices, moment of inertia) but NOT 3D coordinates. The implementation prioritizes CPU-first execution on GitHub Actions free-tier runners with limited CPU and RAM resources, utilizing a canonical ZINC15 dataset (streaming) and a stratified sample size determined by a pilot study to ensure feasibility within 6 hours.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: PyTorch (CPU wheel), PyTorch Geometric (CPU), RDKit, pandas, scikit-learn, datasets (HuggingFace), pyarrow, ruff, pytest
**Storage**: Local filesystem (CSV/Parquet), HuggingFace Datasets (streaming)
**Testing**: pytest (unit, integration, contract), ruff (linting)
**Target Platform**: Linux (GitHub Actions free-tier runner)
**Project Type**: Computational Research / Machine Learning Pipeline
**Performance Goals**: Complete full pipeline (ingest -> preprocess -> train -> eval -> report) within 6 hours on CPU.
**Constraints**: 
- Max limited RAM, 14 GB disk.
- No local GPU (GPU tasks offloaded to Kaggle if triggered).
- Dataset must be open and directly downloadable (ZINC15 via HuggingFace canonical repo).
- Ground truth is RDKit-computed SASA of a specific generated conformer.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*Gates determined based on constitution file*

| Principle | Status | Evidence/Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | `requirements.txt` pins all deps. Random seeds fixed in `code/`. Data fetched from canonical HF sources (`zinc15`). |
| **II. Verified Accuracy** | **Pass** | All dataset URLs in `research.md` cite the canonical HuggingFace repository `zinc15`. No user-uploaded URLs. |
| **III. Data Hygiene** | **Pass** | Pipeline includes checksum generation (`data/raw/checksums.json`). Raw data preserved; derivations written to new files. |
| **IV. Single Source of Truth** | **Pass** | All metrics (MAE, R²) traced to specific output artifacts in `results/`. `contracts/evaluation_schema.schema.yaml` is SSoT for baseline metrics. `contracts/output.schema.yaml` is DEPRECATED. |
| **V. Versioning Discipline** | **Pass** | Artifact hashes recorded in state file upon generation. |
| **VI. Geometric Fidelity** | **Pass** | Plan explicitly compares GCN (2D) vs. Geometry Baseline (3D descriptors only) via paired t-test. Baseline uses independent 3D descriptors (Volume, Shape). No 3D coordinates used. |
| **VII. Conformational Sampling** | **Pass** | `conformer_params` stored in `data/processed/graphs_with_features.parquet` (column) and `data/processed/conformer_params.json` (summary). `failure_report.csv` logs excluded molecules for bias analysis. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-molecular-surface-area/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── data_schema.schema.yaml
    ├── dataset.schema.yaml        # Active: SSoT for Parquet dataset
    ├── dataset_schema.schema.yaml
    ├── evaluation_schema.schema.yaml  # Active: SSoT for baseline metrics
    ├── gcn_output.schema.yaml
    ├── molecule.schema.yaml
    ├── output.schema.yaml (DEPRECATED: Legacy 2D baseline schema)
    ├── prediction.schema.yaml
    └── sensitivity.schema.yaml      # Active: SSoT for sensitivity results
```

### Source Code (repository root)

```text
code/
├── data/
│   ├── ingest.py            # Download & checksum ZINC15
│   ├── preprocess.py        # 2D graph feat + 3D SASA gen + Bias Analysis
│   └── utils.py             # RDKit helpers
├── models/
│   ├── gcn.py               # GCN Model definition
│   └── baseline.py          # Geometry Baseline (RF on 3D desc)
├── train/
│   └── train_gcn.py         # Training loop, early stopping
├── eval/
│   ├── evaluate.py          # MAE, RMSE, R², t-test
│   └── sensitivity.py       # Threshold sweep + Conformer Noise Check
├── utils/
│   └── logger.py
└── requirements.txt

tests/
├── contract/
│   └── test_schemas.py      # Validates parquet against YAML
├── unit/
│   ├── test_ingest.py
│   └── test_preprocess.py
└── integration/
    └── test_pipeline.py

results/
├── reports/                 # Final comparison tables, sensitivity, runtime
├── plots/                   # Sensitivity curves
├── predictions/             # Parquet of predictions
└── baseline/                # Baseline metrics

data/
├── raw/                     # Downloaded parquet, checksums.json
├── processed/               # Graph features, SASA labels, splits, failure_report.csv
└── schemas/                 # JSON schema for validation

logs/
```

**Structure Decision**: Single project structure selected. Separation of `data`, `models`, `train`, and `eval` ensures modularity and clear data flow from ingestion to reporting. This aligns with the computational nature of the project and the need for reproducible pipelines.

**Contract References**:
- **Ground Truth (SASA)**: `contracts/dataset.schema.yaml` (column `sasa`) and `contracts/molecule.schema.yaml`.
- **Baseline Metrics**: `contracts/evaluation_schema.schema.yaml` (object `baseline`). *Note: `contracts/output.schema.yaml` is DEPRECATED as it defines a 2D baseline, not the required Geometry-Based Baseline.*
- **Sensitivity Results**: `contracts/sensitivity.schema.yaml`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **3D Baseline vs 2D GCN** | Required by Spec FR-004 & Constitution Principle VI to quantify info loss. | A pure 2D baseline would fail to address the core hypothesis (2D -> 3D prediction). |
| **Streaming Dataset** | ZINC exceeds 7 GB RAM if fully loaded. | Loading full dataset would cause OOM on CI runner. Streaming is mandatory for feasibility. |
| **Sensitivity Analysis** | Required by Spec FR-006 to avoid cherry-picking thresholds. | Single threshold evaluation lacks robustness and fails methodological rigor. |
| **Conformer Noise Analysis** | Required to ensure thresholds are valid (larger than noise floor). | Without this, success rates may reflect conformer generation noise rather than model performance. |

## Implementation Phases

### Phase 1: Data Ingestion & Preprocessing (FR-001, FR-002)
**Goal**: Create a validated, paired dataset of 2D graphs and 3D SASA labels.
**Inputs**: Canonical ZINC15 dataset (HuggingFace `zinc15`).
**Outputs**: `data/processed/graphs_with_features.parquet`, `data/raw/checksums.json`, `data/processed/failure_report.csv`, `data/processed/conformer_params.json`.

1.  **Ingest**: Download ZINC15 using `datasets.load_dataset('zinc15', streaming=True)`. Write `data/raw/checksums.json` (Task T057).
2.  **Parse & Filter**: Convert SMILES to RDKit `Mol`. Exclude invalid SMILES and molecules >100 atoms.
3.  **Conformer Gen**: Generate 3D conformers (ETKDG). If >10% fail, halt and log to `failure_report.csv` (Task T015a).
4.  **Bias Analysis**: Compare MW distribution of excluded vs. included molecules.
    - **Action**: If KS test p-value < 0.05 (bias detected), halt with "Bias Critical" flag OR re-sample using stratified exclusion until p > 0.05.
5.  **Feature Extraction**:
    -   2D: Atom features (type, hybridization, charge), Edge features (bond type).
    -   3D: Compute SASA, Volume, Shape Indices, Moment of Inertia.
6.  **Pilot & Sample**: Run a pilot on a representative sample of molecules to estimate runtime. Select a stratified sample (by MW) such that total estimated runtime < 5.5 hours.
7.  **Conformer Noise Check**: Calculate SASA variance across multiple conformers for a subset. Verify thresholds (representative magnitudes) > noise floor.
    - **Clarification**: Ground truth is SASA of a SINGLE conformer. Noise is variance across multiple conformers.
8.  **Split**: Stratified split by Molecular Weight (KS test p-value > 0.05).
9.  **Write**: Save to `graphs_with_features.parquet` (Task T014). `conformer_params` stored as JSON string in Parquet column.

### Phase 2: GCN Model Training (FR-003)
**Goal**: Train a lightweight GCN on 2D features.
**Inputs**: `data/processed/graphs_with_features.parquet` (train split).
**Outputs**: `results/models/gcn_model.pt`, `results/reports/training_log.json`.

1.  **Model**: 2-3 Graph Convolutional layers + Global Pooling + MLP.
2.  **Train**: Max 50 epochs, Early Stopping (patience=5), CPU-only.
3.  **Validate**: Track MAE on validation set.

### Phase 3: Geometry-Based Baseline Training (FR-004)
**Goal**: Train a Random Forest on 3D geometric descriptors (Volume, Shape, Moment) to predict SASA.
**Inputs**: `data/processed/graphs_with_features.parquet` (train split).
**Outputs**: `results/models/baseline_model.pkl`.

1.  **Features**: Extract 3D descriptors (Volume, Shape Indices, Moment of Inertia) from the *same* conformers used for SASA. **Do NOT use 3D coordinates.**
2.  **Train**: Random Forest Regressor.
    - **Clarification**: This is a learned model with expected non-zero error, NOT an oracle.
3.  **Validate**: Track MAE on validation set.
    - **Constraint**: Must use the exact same test split indices as the GCN (Phase 4) to ensure paired comparison.

### Phase 4: Sensitivity Analysis & Reporting (FR-005, FR-006, FR-007, SC-004)
**Goal**: Compare models and assess robustness.
**Inputs**: `results/models/gcn_model.pt`, `results/models/baseline_model.pkl`, `data/processed/graphs_with_features.parquet` (test split).
**Outputs**: `results/reports/comparison_report.json`, `results/reports/sensitivity_analysis.json`, `results/predictions/gcn_predictions.parquet`.

1.  **Predict**: Generate predictions for GCN and Baseline on test set.
2.  **Metrics**: Calculate MAE, RMSE, R² for both.
3.  **Stat Test**: Paired t-test on errors (GCN vs. Baseline). Report p-value, Cohen's d.
4.  **Sensitivity**:
    -   Sweep thresholds: **{1.0, 5.0, 10.0} Å²** (physically realistic, > conformer noise).
    -   Calculate success rates (error < threshold) for both models.
    -   Perform **McNemar's test** for paired proportions at each threshold.
    -   Apply **Bonferroni correction** to the resulting p-values and record in `adjusted_p_value` field of `contracts/sensitivity.schema.yaml`.
5.  **Report**: Save results to `sensitivity_analysis.json` (schema: `contracts/sensitivity.schema.yaml`). This is a hard gate for SC-004.

### Phase 5: Runtime Measurement & Verification (SC-005)
**Goal**: Verify computational feasibility.
**Inputs**: All pipeline logs.
**Outputs**: `results/reports/runtime.json`.

1.  **Measure**: Record total runtime (ingest + preprocess + train + eval).
2.  **Verify**: Check if total < 6 hours.
3.  **Report**: Save to `runtime.json` (schema: `contracts/gcn_output.schema.yaml`). This is a hard gate for SC-005.

## Verification & Testing

-   **Unit Tests**: `test_ingest.py` (checksum), `test_preprocess.py` (feature extraction).
-   **Contract Tests**: `test_schemas.py` validates `parquet` against `contracts/*.yaml`.
-   **Integration Tests**: `test_pipeline.py` runs full flow on a small subset.
-   **Hygiene**: `ruff` linting (Task T003a). `pytest` coverage.

## Risk Management

-   **Risk**: Conformer generation fails for >10%. **Mitigation**: Halt pipeline, report bias.
- **Risk**: OOM on 7 GB RAM. **Mitigation**: Streaming, sample size fixed by pilot study.
-   **Risk**: Thresholds too small (noise floor). **Mitigation**: Conformer Noise Analysis in Phase 1.
-   **Risk**: Baseline tautology. **Mitigation**: Use independent 3D descriptors (Volume, Shape), NO coordinates.
-   **Risk**: Bias in excluded molecules. **Mitigation**: Bias Analysis + Re-sampling or Halt.
