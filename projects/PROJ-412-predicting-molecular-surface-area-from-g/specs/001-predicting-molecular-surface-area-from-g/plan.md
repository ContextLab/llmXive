# Implementation Plan: Predicting Molecular Surface Area from Graph Convolutional Networks

**Branch**: `001-predict-molecular-surface-area` | **Date**: 2026-07-13 | **Spec**: `specs/001-predicting-molecular-surface-area-from-g/spec.md`
**Input**: Feature specification from `/specs/001-predicting-molecular-surface-area-from-g/spec.md`

## Summary

This project implements a comparative study between a 2D-only Graph Convolutional Network (GCN) and a Geometry-Based Baseline (a predictive model using 3D descriptors) to predict molecular surface area (SA). The primary goal is to quantify the information loss incurred by omitting 3D conformational data (Constitution Principle VI). The pipeline ingests SMILES from verified HuggingFace datasets (ZINC with a QM9 fallback), generates 2D graph features and 3D SA labels (or uses pre-computed labels from QM9), trains both models on CPU, and performs rigorous statistical comparisons including paired t-tests and sensitivity analysis with multiple-comparison correction.

**Critical Note on Baseline Validity & Circularity Mitigation**: 
The "Geometry-Based Baseline" is defined as a predictive model (e.g., Ridge Regression) trained on 3D geometric descriptors. To strictly avoid circularity (where the baseline simply recalls the label generation noise), we enforce **Conformer Seed Separation**:
1.  **Label Generation**: The "Ground Truth" SA is calculated from a 3D conformer generated using **Seed A** (e.g., `seed=42`).
2.  **Baseline Feature Extraction**: The 3D descriptors used as input for the Baseline model are calculated from a *different* 3D conformer generated using **Seed B** (e.g., `seed=123`), where Seed B != Seed A.
3.  **Rationale**: Since 3D conformer generation is stochastic, Seed A and Seed B will yield slightly different geometries. The Baseline model must therefore learn the generalizable relationship between 3D geometry and SA, rather than overfitting to the specific noise of the label's conformer. This ensures the Baseline has non-zero error, making the comparison with the 2D GCN scientifically valid and the t-test meaningful.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `rdkit`, `torch`, `torch-geometric`, `scikit-learn`, `pandas`, `numpy`, `datasets` (HuggingFace)
**Storage**: Local filesystem (`data/` for raw/processed, `artifacts/` for models)
**Testing**: `pytest`
**Target Platform**: Linux (GitHub Actions CPU runner: 2 cores, ~7 GB RAM)
**Project Type**: Data Science / Machine Learning Research Pipeline
**Performance Goals**: Complete full training and evaluation cycle within 6 hours on CPU.
**Constraints**:
- Memory: Must fit within a constrained RAM footprint consistent with standard workstation capabilities, as discussed in [Citation]. (use streaming for datasets, batched processing).
- Compute: No local GPU; CPU-only training for GCN.
- Data: Must use verified HuggingFace sources; no fabricated or gated data.
- Reproducibility: Fixed random seeds (including distinct seeds for label/baseline conformers), checksummed data (Constitution Principles I, III).

> **Note on Compute Feasibility**: The GCN models are designed to be "lightweight" (shallow architecture, small batch size) to ensure they run within the 6-hour CPU limit. A **Pilot Phase** is implemented to verify that the target sample size (N=1000 successful 3D conformers) can be achieved within 4 hours on ZINC15. If the pilot fails, the pipeline automatically switches to the QM9 dataset (which has pre-computed 3D properties) to ensure statistical validity without the CPU bottleneck of conformer generation.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action/Verification |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/config.py` (including `SEED_LABEL` and `SEED_BASELINE`); datasets fetched from canonical HuggingFace URLs; `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **PASS** | All dataset URLs cited are from the "Verified datasets" block. No external citations invented. |
| **III. Data Hygiene** | **PASS** | Pipeline will generate checksums for raw and processed data. No in-place modifications. |
| **IV. Single Source of Truth** | **PASS** | Evaluation results (MAE, R², p-values) will be written to JSON/CSV artifacts; paper will reference these files, not hard-coded values. |
| **V. Versioning Discipline** | **PASS** | Artifacts will be named with content hashes; state file updated on change. |
| **VI. Geometric Fidelity** | **PASS** | Plan explicitly includes a Geometry-Based Baseline using 3D descriptors from a *distinct* conformer generation process (Seed B) compared to the label (Seed A) to ensure valid comparison. The baseline is distinct from the label generation to avoid circularity. |
| **VII. Conformational Sampling** | **PASS** | Pipeline will log RDKit conformer generation parameters (attempts, minimization steps) AND the specific seeds used for both label generation and baseline feature extraction in `conformer_params` field. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-molecular-surface-area-from-g/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-412-predicting-molecular-surface-area-from-g/
├── data/
│   ├── raw/             # Downloaded parquet files
│   ├── processed/       # Graph features, 3D labels, splits
│   └── checksums.json   # Data integrity hashes
├── code/
│   ├── __init__.py
│   ├── config.py        # Seeds, thresholds, paths
│   ├── data/
│   │   ├── ingest.py    # SMILES -> Graph + 3D Label (or load QM9)
│   │   ├── pilot.py     # Feasibility check for N=1000
│   │   └── split.py     # Stratified split (KS test)
│   ├── models/
│   │   ├── gcn_2d.py    # 2D-Only GCN Model Definition
│   │   └── baseline_3d.py # Geometry-Based Baseline (Predictive Model)
│   ├── train.py         # Training loop (CPU)
│   ├── eval.py          # Evaluation & Statistical Tests
│   └── sensitivity.py   # Threshold sweep & McNemar correction
├── tests/
│   ├── unit/            # Unit tests for RDKit parsing, graph conversion
│   ├── integration/     # End-to-end pipeline test (small subset)
│   └── contract/        # Schema validation tests
├── artifacts/           # Model weights, results JSON
└── requirements.txt     # Pinned dependencies
```

**Structure Decision**: Single-project structure chosen. The workflow is linear (Ingest -> Process -> Train -> Eval), making a monolithic `code/` directory with modular sub-packages appropriate. No separate frontend/backend is needed.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Dual Model Architecture (2D GCN + Geometry-Based Baseline)** | Required by Constitution Principle VI to quantify information loss. A direct calculator (Oracle) was rejected as tautological. | A single model would fail to answer the research question of "2D vs 3D" fidelity. |
| **Conformer Seed Separation** | Required to resolve circularity concerns. Using the same conformer for label and baseline features would result in near-zero error for the baseline, invalidating the t-test. | Using a single conformer seed creates a methodological flaw where the baseline is essentially an oracle for its own noise. |
| **Sensitivity Analysis + Correction** | Required by FR-006/FR-007 to prevent cherry-picking and ensure robustness. | A single threshold evaluation would be methodologically unsound and prone to false positives. |
| **Streaming Data Processing + Pilot Phase** | Required to fit large HuggingFace datasets into 7 GB RAM and ensure N=1000 validity. | Loading full datasets into memory would cause OOM errors; post-hoc sampling risks underpowering. |

## FR/SC Mapping

| ID | Requirement/Scenario | Plan Component |
| :--- | :--- | :--- |
| **FR-001** | Ingest SMILES, convert to 2D graph (RDKit). | `code/data/ingest.py` (Graph conversion logic). |
| **FR-002** | Generate 3D SA labels (RDKit 3D). | `code/data/ingest.py` (Conformer generation with Seed A & SA calc) OR load QM9. |
| **FR-003** | Train lightweight GCN (CPU, early stopping). | `code/train.py` (2D GCN class, training loop, early stopping). |
| **FR-004** | Train Geometry-Based Baseline (RDKit 3D). | `code/models/baseline_3d.py` (Predictive model using 3D descriptors from Seed B). |
| **FR-005** | Paired t-test (MAE comparison, p-value, effect size). | `code/eval.py` (Statistical testing module). |
| **FR-006** | Sensitivity analysis (thresholds, standard significance levels). | `code/sensitivity.py` (Sweep logic). |
| **FR-007** | Multiple-comparison correction (Bonferroni/FDR). | `code/sensitivity.py` (McNemar's test + Bonferroni correction). |
| **SC-001** | Measure R² (GCN vs Baseline). | `code/eval.py` (Metric calculation). |
| **SC-002** | Measure MAE (GCN vs Baseline). | `code/eval.py` (Metric calculation). |
| **SC-003** | Measure statistical significance (p-value, Cohen's d). | `code/eval.py` (Statistical testing). |
| **SC-004** | Measure robustness (threshold variation). | `code/sensitivity.py` (Sweep results). |
| **SC-005** | Measure computational feasibility (runtime). | `code/train.py` (Timing logs). |
| **US-1.3** | Stratified split (KS test p > 0.05). | `code/data/split.py` (KS test implementation). |
| **US-3.3** | Bonferroni/FDR correction. | `code/sensitivity.py` (Correction implementation). |

## Computational Feasibility Strategy

1.  **Pilot Phase**: Before full processing, a pilot of 10 molecules is run on ZINC15 to estimate conformer generation time. If `1000 * pilot_time > 4 hours`, the pipeline switches to QM9 (pre-computed 3D) to ensure N=1000 is achieved within the 6-hour limit.
2.  **CPU-First**: The GCNs are shallow networks (2-3 layers) with small embedding dimensions to ensure training completes within 6 hours on 2 CPU cores.
3.  **Data Streaming**: The `datasets` library will be used in streaming mode to avoid loading the entire ZINC15/SMILES dataset into RAM.
4.  **Minimum Viable Sample (MVS)**: The study targets N=1000 *successful* 3D conformers. If the dataset (ZINC) cannot yield this number within the time budget, the fallback to QM9 is triggered. This ensures the study is never underpowered by accident.
5.  **No Fabrication**: No synthetic data, hard-coded results, or placeholder metrics will be used. All metrics will be derived from the actual model runs on real data.

## Data Availability & Fallback

- **Primary**: ZINC15 (verified URL).
- **Fallback**: QM9 (verified URL). QM9 contains pre-computed 3D properties (including surface area) and is computationally feasible for the CI runner.
- **Switch Condition**: If the ZINC15 pilot phase indicates the N=1000 target cannot be met within 4 hours, the pipeline switches to QM9.
- **Verification**: Both datasets are verified open sources with programmatic access.