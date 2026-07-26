# Implementation Plan: Predicting Molecular Permeability Coefficients via Graph Neural Networks

**Branch**: `001-predict-molecular-permeability` | **Date**: 2023-10-27 | **Spec**: [link]
**Input**: Feature specification from `/specs/001-predict-molecular-permeability/spec.md`

## Summary

This project implements a computational pipeline to predict general molecular permeability coefficients (ADMET) via Graph Neural Networks. The approach ingests public datasets (ChEMBL ADMET) containing SMILES strings and permeability data, converts them into molecular graphs using RDKit, and trains a 3-layer Graph Convolutional Network (GCN) with ≤500K parameters. The GNN performance is rigorously compared against Random Forest and Linear Regression baselines using k-fold scaffold-split cross-validation and a Wilcoxon signed-rank test. The plan ensures all Functional Requirements (FR-001 to FR-007) and Success Criteria (SC-001 to SC-004) are addressed, with specific attention to compute constraints (CPU-first, limited-core/memory) and data hygiene (checksums, no in-place modification).

## Technical Context

**Language/Version**: Python +
**Primary Dependencies**: `rdkit`, `torch`, `torch-geometric` (CPU version), `scikit-learn`, `pandas`, `numpy`, `pyyaml`, `datasets` (HuggingFace)
**Storage**: Local filesystem (`data/raw/`, `data/processed/`, `code/models/`)
**Testing**: `pytest` (unit tests for graph construction, integration tests for training pipeline)
**Target Platform**: Linux (GitHub Actions free-tier: Multiple CPU, sufficient RAM
Research Question: How can we optimize CI/CD pipelines for open-source projects?
Method: Comparative analysis of workflow execution times across different cloud providers.
References: Smith et al. (2023); DOI:10.1234/example)
**Project Type**: Computational research pipeline / CLI
**Performance Goals**: Graph construction < 15 mins (enforced by timeout); 5-fold CV training < 2 hours.
**Constraints**: No GPU available on primary runner; memory usage < 2GB for graph data; strict reproducibility via pinned seeds.
**Scale/Scope**: Dataset size [deferred: to be determined by available ChEMBL data]; 5-fold CV; model types.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Detail |
|-----------|--------|-----------------------|
| **I. Reproducibility** | **Compliant** | `code/` will contain `requirements.txt` with pinned versions. Random seeds will be set in `torch`, `numpy`, and `python` at the start of every script. External datasets will be fetched via `datasets.load_dataset` using specific revision IDs where available. |
| **II. Verified Accuracy** | **Compliant** | All citations in `research.md` and `data-model.md` will be restricted to the "Verified datasets" block provided in the spec. No URLs will be invented. ChEMBL ADMET is the only verified chemical source. |
| **III. Data Hygiene** | **Compliant** | Raw data files in `data/raw/` will be checksummed using a cryptographic hash algorithm upon download. Derived data in `data/processed/` will be new files. No PII (irrelevant for chemical data, but scan enabled). |
| **IV. Single Source of Truth** | **Compliant** | All metrics in the final report will be generated directly from `code/` outputs (CSVs of predictions). No hand-typed numbers in `paper/` or `plan.md`. |
| **V. Versioning Discipline** | **Compliant** | Artifacts (data files, model weights) will carry content hashes. The `state/` YAML will be updated upon successful run completion. |
| **VI. Graph-Based Fidelity** | **Compliant** | Primary model (GCN) will use `rdkit.Chem` to generate `Mol` objects and convert to `torch_geometric.data.Data` (nodes=atoms, edges=bonds). Baseline models use only computed descriptors. |
| **VII. Polymeric Membrane Specificity (Reframed)** | **Compliant** | Data ingestion logic will filter for general permeability (ADMET) targets. A prominent disclaimer will be included in the final report stating the domain shift from polymeric membranes to ADMET due to data availability. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-molecular-permeability/
├── plan.md # This file
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
├── contracts/ # Phase 1 output
└── tasks.md # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-522-predicting-molecular-permeability-coeffi/
├── data/
│ ├── raw/ # Downloaded parquet/jsonl files (immutable)
│ └── processed/ # Cleaned CSVs, graph adjacency lists, descriptor matrices
├── code/
│ ├── __init__.py
│ ├── requirements.txt
│ ├── ingestion.py # SMILES parsing, RDKit graph construction, descriptor calculation
│ ├── models/
│ │ ├── __init__.py
│ │ ├── gcn.py # 3-layer GCN definition
│ │ └── baselines.py # RF and LR wrappers
│ ├── training.py # 5-fold CV loop, scaffold splitting, metric aggregation
│ ├── analysis.py # Sensitivity sweep, permutation importance
│ └── report.py # Generates final report with required disclaimer
├── tests/
│ ├── contract/ # Validates output schemas
│ ├── unit/ # RDKit parsing, descriptor logic
│ └── integration/ # End-to-end pipeline on sample data
└── state/
 └── projects/PROJ-522-predicting-molecular-permeability-coeffi.yaml
```

**Structure Decision**: Single project structure (Option 1) selected. The workflow is linear: Ingestion -> Model Training -> Analysis -> Reporting. Separation into `data`, `code`, and `tests` ensures clear boundaries for reproducibility and testing.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **GPU Escape Hatch** | GNN training on graphs can be memory intensive, but the constraint (≤500K params, [deferred] samples) is designed for CPU. If runtime exceeds 2h on CPU, the plan includes a "GPU Escape Hatch" to offload to Kaggle. | A pure CPU run is preferred to simplify CI. GPU is only a fallback for the training phase if the CPU budget is exceeded, not for the entire pipeline. |
| **Scaffold Splitting** | Standard random split is invalid for molecular datasets due to high similarity between molecules, leading to data leakage. | Random splitting would inflate performance metrics artificially, violating the "Verified Accuracy" and scientific validity principles. |
| **Reproducibility on GPU** | The GPU escape hatch uses a pinned Docker image (`pytorch/pytorch:latest-cuda11.7-cudnn8-runtime`) and a specific Kaggle kernel ID to ensure the environment is identical to the local CPU run. | Without pinning, the Kaggle environment could change, violating reproducibility. |

## Implementation Details

### 1. Dataset Ingestion (FR-001)
- **Source**: ChEMBL ADMET (Verified Source).
- **Process**:
 1. Download `raw.parquet` from verified source.
 2. Validate checksum.
 3. Parse SMILES -> `Mol` (RDKit).
 4. Filter: Remove rows with `NaN` in target column.
 5. Handle Duplicates: Average target values for identical SMILES.
 6. **Timeout Enforcement**: The ingestion script MUST enforce a timeout. If exceeded, the process is terminated and logs "TIMEOUT: Graph construction exceeded 15 minutes".

### 2. Model Architecture (FR-002)
- **GNN**: 3-layer Graph Convolutional Network (GCN).
 - **Parameters**: ≤ 500,000.
 - **Layers**: Input -> GCN(64) -> ReLU -> GCN(64) -> ReLU -> GCN(64) -> Global Mean Pooling -> FC(32) -> ReLU -> FC(1).
 - **Regularization**: Dropout (a moderate rate), Weight Decay (a small regularization coefficient), Early Stopping (patience=10).
 - **Device**: CPU (PyTorch CPU backend).
- **Baselines**:
 - **Random Forest**: 100 trees, max_depth=10.
 - **Linear Regression**: Standard OLS.
- **Input**: GNN uses graph topology; Baselines use descriptor vectors only.

### 3. Cross-Validation & Splitting (FR-003)
- **Split Strategy**: **Scaffold Splitting** (Murcko Scaffolds) to prevent data leakage from similar molecules.
- **Folds**: 5-fold.
- **Metrics**: R², MAE, RMSE.
- **Statistical Test**: **Wilcoxon signed-rank test** (alpha=0.05) comparing GNN vs. RF/LR R² scores across the 5 folds. (Replaces t-test due to small sample size).

### 4. Sensitivity & Uncertainty (FR-004, FR-005)
- **Sensitivity Sweep**: Prediction interval widths {,, 0.1}. Measure MAE variation.
- **Permutation Importance**: Randomly shuffle specific atom/bond features (substructures) and measure drop in R².
- **Perturbation Experiment**: For SC-004, specific functional groups (hydroxyl, carboxyl, amine) are removed from molecules, and the change in predicted permeability is checked against chemical intuition.
- **Causal Disclaimer**: All conclusions framed as "associational" (FR-006).

### 5. Compute Feasibility (FR-007)
- **CPU-First**: The small parameter count (≤500K) and [deferred] dataset size are designed to run on 2 cores / 7GB RAM within 2 hours.
- **GPU Escape Hatch**: If the training step exceeds a reasonable duration on CPU, the execution agent will automatically re-run on a Kaggle GPU (scaled down: 8-bit quantization or fewer epochs) as per the "Compute feasibility" rules.
 - **Reproducibility**: The Kaggle run uses a pinned Docker image (`pytorch/pytorch:.1-cuda11.7-cudnn8-runtime`) and a specific Kaggle kernel ID to ensure the environment is identical to the local CPU run.
 - **No Synthetic Approximation**: No synthetic CPU approximation of a GPU-only method is planned.

## Data Availability & Risks

- **Risk**: The "Verified datasets" block lacks a confirmed source for *polymeric membrane* permeability.
- **Mitigation**: The study has been reframed to "General Molecular Permeability (ADMET)". The ChEMBL ADMET dataset is used as a proxy. A prominent disclaimer will be included in the final report stating the domain shift.
- **Streaming**: If the dataset exceeds memory, `datasets.load_dataset(..., streaming=True)` will be used to process shards sequentially.

## References

- **ChEMBL ADMET Dataset**: ` (Verified Source).
- **RDKit**: ` (Standard Library).
- **PyTorch Geometric**: ` (Standard Library).

*Note: URLs for NIST, PubChem, and MTR listed in the original spec were inspected and found to be non-chemical (cybersecurity, LLM, conversational) or mismatched. They are excluded from the chemical analysis plan.*