# Implementation Plan: Predicting Molecular Diffusion Coefficients in Liquids with Graph Neural Networks

**Branch**: `001-predict-molecular-diffusion` | **Date**: 2026-06-26 | **Spec**: `specs/001-predicting-molecular-diffusion-coefficie/spec.md`
**Input**: Feature specification from `specs/001-predicting-molecular-diffusion-coefficie/spec.md`

## Summary

This project implements a CPU-optimized pipeline to predict molecular diffusion coefficients in liquids using Graph Neural Networks (GNNs). The approach converts SMILES strings into graph representations (atoms/nodes, bonds/edges) and combines them with scalar solvent descriptors (viscosity, dielectric constant) to train a Message Passing Neural Network (MPNN). The implementation strictly adheres to CPU-only constraints (no CUDA/GPU), performs 5-fold cross-validation, compares performance against a linear regression baseline, and executes sensitivity analyses on hyperparameters and feature ablation.

**CRITICAL DATA NOTE**: As of this writing, no verified dataset containing the specific combination of SMILES, Solvent Properties, and Experimental Diffusion Coefficients has been identified. **The project is currently paused for scientific claims.** The pipeline will be validated using synthetic data (generated via Stokes-Einstein physics or random structure) strictly for structural integrity and code execution. **No performance metrics (r, RMSE) will be reported from synthetic runs.** The project cannot reach `research_complete` without a verified real-world dataset.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `rdkit`, `torch` (CPU-only), `torch-geometric` (CPU-only), `scikit-learn`, `pandas`, `pyyaml`, `pytest`
**Storage**: Local filesystem (`data/raw`, `data/processed`, `artifacts`)
**Testing**: `pytest` with contract validation against YAML schemas
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, 7GB RAM)
**Project Type**: Computational Research / Data Science Pipeline
**Performance Goals**: Complete training/evaluation on ≤5,000 samples (if real data exists) within 6 hours; memory usage < 7GB.
**Constraints**: NO GPU/CUDA; NO dynamic molecular dynamics; NO imputation of missing data (exclusion only).
**Scale/Scope**: 
- **Real Data**: Capped at ~5,000 molecule-solvent pairs for CI feasibility.
- **Synthetic Data (Current State)**: Used ONLY for pipeline validation; sample size arbitrary (e.g., 100-500) to ensure CI speed. **No scientific metrics reported.**

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value. **NO FABRICATED METRICS.**

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **I. Reproducibility**: **COMPLIANT**. The plan mandates pinned seeds (42), deterministic data loading, and a `requirements.txt` with exact versions. All artifacts are derived from raw data without in-place modification.
2.  **II. Verified Accuracy**: **COMPLIANT (Conditional)**. The plan requires citing only verified dataset URLs from the project's `# Verified datasets` block. **Current Status**: No verified dataset exists. The plan proceeds with synthetic data *only* for structural validation. **Scientific claims are blocked** until a real dataset is sourced. No fabricated metrics are permitted.
3.  **III. Data Hygiene**: **COMPLIANT**. Raw data is preserved. Derivations (featurized graphs) are written to new files. Checksums will be recorded in `state/`. No PII is expected in chemical datasets.
4.  **IV. Single Source of Truth**: **COMPLIANT**. All statistics (r, RMSE) will be computed by code and stored in JSON reports, referenced directly by the paper. No hand-typed numbers. **Note**: If synthetic data is used, no statistics are reported.
5.  **V. Versioning Discipline**: **COMPLIANT**. Artifacts will carry content hashes. The plan includes a step to update `state/` timestamps upon artifact generation.
6.  **VI. Static-to-Dynamic Representation Fidelity**: **COMPLIANT (Conditional)**. The plan explicitly uses RDKit for static graph generation and scalar descriptors. **Note**: If synthetic data is used, the 'Static-to-Dynamic' fidelity is only validated on the synthetic generator's internal logic (e.g., Stokes-Einstein), not real-world diffusion dynamics. This does not support scientific claims about physical diffusion.
7.  **VII. Statistical Significance and Baseline Comparison**: **COMPLIANT (Conditional)**. The plan mandates Pearson r, RMSE, and a paired t-test against a linear baseline with solvent descriptors. **Note**: These metrics are only calculated and reported if a verified real-world dataset is used.

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-molecular-diffusion-coefficie/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-365-predicting-molecular-diffusion-coefficie/
├── data/
│   ├── raw/             # Downloaded CSVs/Parquets (immutable)
│   ├── processed/       # Featurized JSONL/Parquet (derived)
│   └── checksums.txt    # Integrity records
├── code/
│   ├── __init__.py
│   ├── config.py        # Hyperparameters, seeds, paths
│   ├── featurization.py # RDKit graph conversion, solvent descriptor lookup
│   ├── models/
│   │   ├── __init__.py
│   │   ├── mpnn.py      # CPU-optimized MPNN architecture
│   │   └── baseline.py  # Linear regression with fingerprints
│   ├── training.py      # 5-fold CV loop, training logic
│   ├── evaluation.py    # Metrics, t-tests, ablation
│   └── main.py          # Orchestration script
├── tests/
│   ├── contract/        # Schema validation tests
│   ├── unit/            # Unit tests for featurization/models
│   └── integration/     # End-to-end pipeline tests
├── artifacts/           # Model checkpoints, reports
├── requirements.txt     # Pinned dependencies
└── README.md
```

**Structure Decision**: Single-project structure (Option 1) is selected. The project is a focused research pipeline where separation of frontend/backend is unnecessary. All components (featurization, training, evaluation) are tightly coupled to the data flow.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | The project scope (CPU GNN on small dataset) fits within the default complexity limits of the CI runner. | N/A |

## Implementation Phases

### Phase 0: Data Acquisition & Validation (Blocked until verified dataset found)
- **Goal**: Acquire a verified dataset containing SMILES, Solvent Type, and Diffusion Coefficients.
- **Action**: If no verified dataset exists, generate synthetic data *strictly for pipeline validation* (no metrics).
- **Output**: `data/raw/dataset.csv` (Real or Synthetic).

### Phase 1: Featurization
- **Goal**: Convert raw data to graph representations and solvent descriptors.
- **Action**: Parse SMILES with RDKit, compute node/edge features, map solvent types to descriptors.
- **Constraint**: Exclude records with missing data (log `[MISSING_DATA_EXCLUDED]`).
- **Output**: `data/processed/featurized_data.jsonl`.

### Phase 2: Model Training (MPNN & Baseline)
- **Goal**: Train GNN and Linear Baseline.
- **Action**: 5-fold CV (stratified by solvent or diffusion bin).
- **Constraint**: CPU-only, seed=42.
- **Output**: `artifacts/models/mpnn_fold_*.pt`, `artifacts/models/baseline_fold_*.pt`.

### Phase 3: Evaluation & Profiling (SC-003, SC-005)
- **Goal**: Calculate metrics and profile resource usage.
- **Action**: Compute Pearson r, RMSE. Perform Shapiro-Wilk test on residuals. If non-normal, use Wilcoxon signed-rank test.
- **Profiling**: Log `total_runtime_seconds` and `peak_memory_mb` to results JSON.
- **Output**: `artifacts/reports/results.json`.

### Phase 4: Ablation Study (FR-006, SC-004)
- **Goal**: Isolate the contribution of solvent descriptors.
- **Action**: Retrain GNN *without* solvent descriptors. Compare performance to full GNN.
- **Output**: `artifacts/reports/ablation_results.json`.

### Phase 5: Sensitivity Analysis (FR-006)
- **Goal**: Test robustness to hyperparameters.
- **Action**: Sweep message passing steps {1, 2, 3}. Report r and RMSE *with outliers included*.
- **Output**: `artifacts/reports/sensitivity_results.json`.

### Phase 6: Reporting
- **Goal**: Generate final report.
- **Action**: Aggregate results, ensure all metrics are from real data (or state "No real data").
- **Output**: `paper/draft.md`.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| **No verified dataset** | **BLOCKING**. Project cannot reach `research_complete`. Synthetic data used only for pipeline validation (no metrics). |
| **Memory Overflow** | Process in batches; limit dataset size; use `float32`. |
| **Negative Correlation** | Report as valid null result (r < 0.3). |
| **SMILES Parsing Failures** | Robust error handling; log invalid entries. |
| **Fabricated Results** | **STRICT PROHIBITION**. No metrics reported from synthetic data. |