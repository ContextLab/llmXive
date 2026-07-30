# Implementation Plan: Predicting Molecular Surface Area from Graph Convolutional Networks

**Branch**: `001-predict-molecular-surface-area` | **Date**: 2026-07-14 | **Spec**: `specs/001-predict-molecular-surface-area/spec.md`
**Input**: Feature specification from `/specs/001-predict-molecular-surface-area/spec.md`

## Summary

This project implements a comparative study to determine if 2D Graph Convolutional Networks (GCNs) can predict 3D molecular surface area (SASA) with accuracy comparable to a direct 3D geometry computation. The technical approach involves ingesting SMILES from a verified Hugging Face dataset, generating 2D graph features and 3D conformers via RDKit, training a lightweight CPU-optimized GCN, and performing rigorous statistical comparisons (paired t-test/Wilcoxon, sensitivity analysis) under strict reproducibility and data hygiene constraints. The baseline is defined as the direct computation of SASA via RDKit on the test set (the "Geometry Oracle"), avoiding circular validation.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `rdkit` (2024.3.1), `torch` (2.2.0, CPU-only), `torch-geometric` (2.5.3, CPU-only), `pandas`, `scikit-learn`, `numpy`, `datasets` (Hugging Face)  
**Storage**: Local Parquet/CSV files under `data/`  
**Testing**: `pytest` with `conftest.py` for fixture isolation  
**Target Platform**: GitHub Actions Free Tier (Linux, 2 CPU, 7GB RAM, no GPU)  
**Project Type**: Computational research pipeline / CLI  
**Performance Goals**: Complete end-to-end pipeline (ingest -> train -> eval) in < 4 hours on CPU; memory usage < 6GB.  
**Constraints**: No GPU access on primary runner; dataset must be streamable or fit in 7GB RAM; no external API calls requiring credentials.  
**Scale/Scope**: Dataset subset (sampled to fit memory budget); model < 1M parameters.

> **Compute Strategy**: All methods selected are CPU-tractable. The GCN will use `torch_geometric` with CPU backend. No GPU escape hatch is required as the model architecture is lightweight (few GCN layers) and the dataset will be processed in chunks or sampled to fit RAM.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Verification Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/config.py`. Dataset source fixed to verified Hugging Face URLs. `requirements.txt` pins exact versions. |
| **II. Verified Accuracy** | **PASS** | All dataset citations restricted to the "Verified datasets" block. Community uploads validated via T003 (checksum/schema check). |
| **III. Data Hygiene** | **PASS** | Pipeline will compute SHA-256 checksums for raw and processed files. No in-place modifications; all derivations write new files. |
| **IV. Single Source of Truth** | **PASS** | Metrics (MAE, R²) will be written to a single `results/metrics.json` file, which the paper generation script reads directly. |
| **V. Versioning Discipline** | **PASS** | Artifact hashes recorded in `state/` YAML. Code changes trigger hash updates. |
| **VI. Geometric Fidelity** | **PASS** | Plan explicitly includes a comparison of GCN (2D) vs. Direct 3D Oracle (RDKit CalcSASA) to quantify information loss. |
| **VII. Conformational Sampling** | **PASS** | `data/processed/conformer_params.json` will log the exact RDKit parameters (e.g., `numThreads`, `maxAttempts`) used for 3D generation. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-molecular-surface-area/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── molecule.schema.yaml
    ├── prediction.schema.yaml
    ├── output.schema.yaml
    ├── sensitivity.schema.yaml
    └── conformer_params.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-412-predicting-molecular-surface-area-from-g/code/
├── config.py            # Seeds, paths, hyperparameters
├── ingestion.py         # Download & validate raw data
├── preprocessing.py     # SMILES -> Graph + 3D Conformer generation
├── models/
│   ├── gcn.py           # GCN model definition
│   └── oracle.py        # Geometry Oracle logic (direct SASA calc)
├── training.py          # Training loop with early stopping
├── evaluation.py        # Metrics, t-tests, sensitivity analysis
├── utils/
│   ├── rdkit_helpers.py # 3D generation wrappers
│   └── data_utils.py    # Streaming, chunking, checksums
└── main.py              # Orchestration script
```

**Structure Decision**: Single project structure chosen. The pipeline is linear (Ingest -> Preprocess -> Train -> Eval) and fits within a single module hierarchy. Separation of `models/` and `utils/` ensures testability and adherence to the "Single Source of Truth" principle by isolating logic from data paths.

## Complexity Tracking

*No violations detected. The complexity is managed by:*
1.  **CPU-First Design**: Avoiding heavy GPU models ensures the project runs on the free tier without needing complex offloading logic.
2.  **Streaming/Data Sampling**: Handling large datasets via `datasets` streaming or fixed-size sampling prevents memory overflow.
3.  **Strict Task Ordering**: Data ingestion and validation precede all model training tasks to prevent runtime failures.

## Implementation Tasks

### Phase 0: Setup & Verification
- [ ] **T001**: Initialize repository structure and `requirements.txt`.
- [ ] **T002**: Install dependencies using CPU-only wheels (`pip install torch --index-url https://download.pytorch.org/whl/cpu`).
- [ ] **T003**: **Dataset Verification**: Download raw dataset, compute SHA-256 checksum, validate schema against `dataset.schema.yaml`.
- [ ] **T004**: Pin random seeds in `code/config.py`.

### Phase 1: Data Ingestion & Preprocessing
- [ ] **T005**: **Dry-Run Verification (T047)**: Execute pipeline on a fixed sample of molecules. Generate `logs/dry_run_100.log` and `data/processed/dry_run_100.parquet` to verify streaming/chunking logic.
- [ ] **T012**: Ingest SMILES from verified source (streaming mode).
- [ ] **T013**: Extract 2D graph features (atom/bond features) from SMILES.
- [ ] **T014**: **3D Conformer Generation & SASA Calculation**: Generate 3D conformers using RDKit. Compute SASA using `rdkit.Chem.rdMolDescriptors.CalcSASA`. Log parameters to `conformer_params.json`.
- [ ] **T014c**: Calculate Molecular Weight and append to `data/processed/paired_dataset.parquet` (extends T013 artifact).
- [ ] **T015**: **Conformer Failure Analysis**: If failure rate > 10%, generate `data/processed/failure_report.csv` analyzing properties of failed molecules.
- [ ] **T016**: Split data into train/test sets (stratified by MW, KS test p > 0.05).

### Phase 2: Model Training
- [ ] **T022**: Train GCN model (CPU, a sufficient number of epochs with early stopping).
- [ ] **T050**: Implement Gradient Accumulation in training loop (moved before T022 execution).

### Phase 3: Baseline & Evaluation
- [ ] **T024**: **Geometry Oracle Evaluation**: Compute SASA for test set using RDKit directly (Ground Truth). This serves as the baseline performance limit.
- [ ] **T029**: **Primary Metric Calculation**: Calculate MAE, RMSE, R² for GCN and Oracle.
- [ ] **T030**: **Sensitivity Sweep**: Evaluate success rates at varying absolute thresholds. (Depends on T029, T040).
- [ ] **T031**: **Multiple Comparison Correction**: Apply Bonferroni correction to sensitivity analysis p-values.
- [ ] **T033**: **Statistical Assumption Check**: Perform Shapiro-Wilk test on error differences.
- [ ] **T034**: **Significance Testing**: If normality holds, run paired t-test; else, run Wilcoxon signed-rank test. Compare GCN error vs. Oracle error (zero).
- [ ] **T040**: Calculate and document mean SASA.
- [ ] **T035**: **Runtime Measurement**: Log total pipeline runtime to `logs/runtime.log`.

### Phase 4: Reporting
- [ ] **T041**: Generate `data/results/metrics.json` and `data/results/sensitivity_analysis.csv`.
- [ ] **T042**: Generate final report summarizing findings and limitations.
