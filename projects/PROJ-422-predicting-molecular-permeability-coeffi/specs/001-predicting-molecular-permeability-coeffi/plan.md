# Implementation Plan: Predicting Molecular Permeability Coefficients Using Graph Neural Networks and Publicly Available Datasets

**Branch**: `001-molecular-permeability-gnn` | **Date**: 2026-08-26 | **Spec**: `specs/001-molecular-permeability-gnn/spec.md`

## Summary

This project implements a comparative analysis of Graph Neural Networks (GNNs) versus classical machine learning (Random Forest) for predicting molecular properties. Due to the absence of verified datasets containing *experimental* permeability coefficients, the study pivots to a **Feasibility Study**: predicting **calculated logP** (a standard molecular descriptor) from SMILES strings. This validates the GNN pipeline's ability to learn structure-property relationships (topology) compared to a baseline using standard descriptors. The system ingests public datasets (SMILES + descriptors), constructs molecular graphs using RDKit, and trains a Message Passing Neural Network (MPNN) alongside a Random Forest baseline. The plan prioritizes CPU-first execution on GitHub Actions free-tier runners. The analysis includes statistical significance testing (paired t-test), effect size calculation (Cohen's d), and interpretability analysis (GNNExplainer/SHAP) to determine if topological features provide incremental predictive value over standard descriptors.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `rdkit`, `torch`, `torch-geometric`, `scikit-learn`, `shap`, `gnnexplainer`, `pandas`, `datasets` (Hugging Face), `statsmodels`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/interim`), CSV/Parquet formats  
**Testing**: `pytest` (unit tests for parsing, integration tests for pipeline)  
**Target Platform**: Linux (GitHub Actions free-tier: 2 vCPU, 7GB RAM, no GPU)  
**Project Type**: Computational research pipeline / CLI  
**Performance Goals**: Full pipeline execution ≤ 6 hours; Peak memory ≤ 7 GB.  
**Constraints**: No local GPU; must handle invalid SMILES gracefully; must stream data if >7GB.  
**Scale/Scope**: Target dataset size: scalable from small pilot cohorts to larger collections, sufficient to validate the proposed approach. (based on available public permeability datasets); if larger, stream or sample.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

- **I. Reproducibility**: The plan mandates pinned `requirements.txt` and deterministic random seeds. All data fetches use canonical HF URLs.
- **II. Verified Accuracy**: All dataset citations in `research.md` are restricted to the "Verified datasets" block provided in the prompt. No external URLs will be invented.
- **III. Data Hygiene**: The pipeline will download raw data to `data/raw`, compute checksums, and write derived data to `data/processed` without modifying raw files.
- **IV. Single Source of Truth**: All metrics (RMSE, MAE, R², Cohen's d, p-values) will be logged to a structured JSON/CSV artifact, which serves as the source for the final report.
- **V. Versioning Discipline**: Artifacts will be versioned via content hashes in the project state file upon completion.
- **VI. Graph-Representation Fidelity**: Graph construction relies exclusively on `rdkit` parsing of SMILES strings. No manual edge additions or heuristic simplifications are permitted.
- **VII. Validation Independence**: The target variable is **calculated logP** (derived from SMILES). The bias check (FR-013) will verify the correlation between inputs and this target. Since the target is a descriptor, a high correlation is expected and will be flagged as "Proxy Target" rather than an error, acknowledging the study's nature as a feasibility test for the GNN architecture.

## Project Structure

```text
projects/PROJ-422-predicting-molecular-permeability-coeffi/
├── code/
│   ├── __init__.py
│   ├── data/
│   │   ├── download.py          # Fetches from HF, checksums
│   │   ├── preprocess.py        # SMILES -> Graph/Descriptors, cleaning
│   │   └── split.py             # Stratified split logic
│   ├── models/
│   │   ├── __init__.py
│   │   ├── gnn.py               # MPNN architecture (PyTorch Geometric)
│   │   └── rf.py                # Random Forest baseline
│   ├── analysis/
│   │   ├── train.py             # Training loop, early stopping
│   │   ├── evaluate.py          # Metrics, t-test, effect size
│   │   └── explain.py           # GNNExplainer, SHAP
│   └── utils/
│       └── logging.py           # Structured logging
├── data/
│   ├── raw/                     # Downloaded datasets (checksummed)
│   ├── processed/               # Feature matrices, splits
│   └── interim/                 # Intermediate graph objects
├── tests/
│   ├── unit/
│   │   ├── test_preprocess.py
│   │   └── test_models.py
│   └── integration/
│       └── test_pipeline.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project layout under `code/` with clear separation of data, models, and analysis. This minimizes overhead for the CI runner and aligns with the "computational research pipeline" pattern.

## Complexity Tracking

No violations found. The complexity is managed by:
1. **CPU-First Design**: Using a small MPNN (shallow architecture) and standard RF to fit within 7GB RAM.
2. **Streaming**: Using `datasets` library streaming to avoid loading massive datasets into RAM.
3. **Graceful Degradation**: Fallback to random split if stratification fails on small N.

## Phase Plan

### Phase 0: Research & Data Verification
- **Goal**: Confirm dataset availability and handle missing targets.
- **Steps**:
  1. Inspect verified datasets (HF links) for "permeability" or "logP" columns.
  2. **Critical Check**: If no experimental permeability column is found (as expected), **Switch to Proxy Mode**. The target will be set to the calculated `logP` column (if available) or a synthetic proxy derived from standard descriptors.
  3. Document dataset size and missingness patterns.
  4. Log the switch to Proxy Mode and the implications for the study (Feasibility Study vs. Experimental Prediction).

### Phase 1: Data Pipeline & Model Architecture
- **Goal**: Build the ingestion, preprocessing, and baseline model.
- **Steps**:
  1. Implement `download.py` with checksum verification.
  2. Implement `preprocess.py`: SMILES parsing (RDKit), descriptor calculation, graph construction.
     - **Retention Check**: Calculate the percentage of valid molecules. If retention < 95%, trigger `SystemExit(1)` with a detailed error log (FR-011).
     - **Bias Check**: Calculate correlation between input descriptors and target. If |r| > 0.85, set `bias_warning: true` in the output (FR-013).
  3. Implement `split.py`: Stratified split by polymer type (or fallback).
  4. Implement `models/gnn.py` (MPNN) and `models/rf.py` (Random Forest).
  5. **Contract**: Validate output schemas for processed data against `contracts/dataset.schema.yaml`.

### Phase 2: Training & Evaluation
- **Goal**: Train models and compute metrics.
- **Steps**:
  1. Implement `analysis/train.py`: Training loop with early stopping.
     - **Ablation Study**: Train a Random Forest baseline on **graph-derived features only** (flattened graph statistics: mean node degree, graph connectivity, substructure counts) to isolate the incremental value of topology (FR-012).
  2. Implement `analysis/evaluate.py`: RMSE, MAE, R² calculation.
  3. Implement statistical test (paired t-test) for FR-007 on prediction errors.
  4. **Power Analysis Implementation**:
     - Calculate **Cohen's d** (effect size) for the difference in prediction errors.
     - Calculate Confidence Intervals for the mean difference.
     - Perform **post-hoc power analysis** using the observed effect size and sample size.
     - Log all metrics (p-value, Cohen's d, CI, power) to the results artifact.
  5. **Constraint Check**: Monitor memory/CPU usage; trigger "GPU escape hatch" only if CUDA error occurs and model is unsolvable on CPU.

### Phase 3: Interpretability & Reporting
- **Goal**: Explain results and generate final report.
- **Steps**:
  1. Implement `analysis/explain.py`: SHAP for RF, GNNExplainer for GNN.
  2. **Comparative Feature Report**:
     - Identify substructures with high GNNExplainer scores.
     - Map these substructures to the RF input space (e.g., check if a detected aromatic ring correlates with a high 'Aromaticity' descriptor).
     - Highlight substructures that are critical for GNN but have low importance in RF (FR-009).
  3. Generate comparative visualizations (heatmaps, feature importance bars).
  4. Run bias check (FR-013) and annotate results with `bias_warning` flag if |r| > 0.85.
  5. Compile final `results.md` and `paper.md` drafts, ensuring the "Exploratory Feasibility" framing and power analysis limitations are clearly stated.

### Phase 4: Validation & Cleanup
- **Goal**: Ensure reproducibility and hygiene.
- **Steps**:
  1. Run full pipeline end-to-end on CI.
  2. Verify checksums and artifact hashes.
  3. Final review against FR/SC list.