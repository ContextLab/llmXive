# Implementation Plan: Predicting Rate Constants of SN1 Reactions from Molecular Structure

**Branch**: `001-predict-sn1-rate-constants` | **Date**: 2024-05-22 | **Spec**: `specs/001-predicting-rate-constants-of-sn1-reactio/spec.md`

## Summary

This feature implements a reproducible, CPU-first pipeline to predict SN1 reaction rate constants from molecular structure. The system ingests kinetic data from verified HuggingFace sources (`DTS-SN-01-2024`, `SN-All-Date

The specific value to remove/generalize: '-Date'

Rewritten passage:`), validates strict metadata requirements (temperature, solvent, explicit substrate class), computes electronic descriptors (Gasteiger charges, topological indices) via RDKit, and trains a Message Passing Neural Network (MPNN) with Nested Cross-Validation. Performance is evaluated against linear and Kernel Ridge Regression baselines using R² and MAE, with statistical significance tested via bootstrap and Holm-Bonferroni correction. Interpretability is achieved via SHAP attributions (framed associatively) and robustness is verified through sensitivity and perturbation analyses.

## Technical Context

**Language/Version**: Python  
**Primary Dependencies**: `rdkit`, `torch` (CPU-only), `scikit-learn`, `shap`, `datasets`, `pandas`, `pyyaml`  
**Storage**: Local files in `data/` (raw, processed, artifacts); `data/` files are checksummed.  
**Testing**: `pytest` for unit tests; integration tests via `main.py` execution on CI.  
**Target Platform**: GitHub Actions Free Tier (multiple CPUs, ~7 GB RAM, ~14 GB disk, no GPU).  
**Project Type**: Computational Research Pipeline / Library  
**Performance Goals**: Complete full pipeline (ingestion → training → evaluation) within 6 hours on 2-core CPU.  
**Constraints**: No GPU usage for training; strict exclusion of datasets missing required metadata; deterministic seeding (seed=42); no causal language in output.  
**Scale/Scope**: Dataset size [deferred] (verified sources only); if <500 rows, framed as feasibility study.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Evidence / Action |
|-----------|--------|-------------------|
| I. Reproducibility | PASS | `code/config.py` enforces `torch.use_deterministic_algorithms(True)` and `seed=42`. `requirements.txt` pins all deps. Data fetched from canonical HF URLs. |
| II. Verified Accuracy | PASS | All dataset URLs cited are from the "Verified datasets" block. No invented URLs. |
| III. Data Hygiene | PASS | Raw data preserved in `data/raw/`; processed data in `data/processed/` with checksums recorded in `state/...yaml`. No in-place modification. |
| IV. Single Source of Truth | PASS | All metrics trace to `data/processed/` and `code/`. No hand-typed numbers. |
| V. Versioning Discipline | PASS | Artifacts hashed; `updated_at` updated on change. The pipeline script automatically updates the `updated_at` timestamp in the state YAML upon artifact generation. |
| VI. Numerical Stability | PASS | Fixed RDKit/PyTorch versions; deterministic algorithms enabled. Uses Gasteiger charges and topological indices (not PM7) as per the CPU constraint. PM7 is explicitly out of scope per the spec. |
| VII. Chemical Dataset Provenance | PASS | Raw kinetic datasets downloaded with timestamps; preprocessing scripts logged. Note: While the Constitution lists NIST/Reaxys, the Plan uses HuggingFace datasets because the verified URLs for NIST/Reaxys are non-kinetic, and this deviation is documented and justified in the spec (FR-001). |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-sn1-rate-constants/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── output.schema.yaml
│   └── collinear.schema.yaml
└── tasks.md             # Phase 2 output (NOT created here)
```

### Source Code (repository root)

```text
projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/
├── code/
│   ├── main.py              # Orchestrates ingestion, training, eval
│   ├── config.py            # Seeds, paths, hyperparameter ranges
│   ├── ingestion.py         # Data download, validation, cleaning
│   ├── descriptors.py       # RDKit-based descriptor computation
│   ├── model.py             # MPNN architecture, training loop
│   ├── baselines.py         # Linear, KRR, Random baselines
│   ├── eval.py              # Metrics, bootstrap, Holm-Bonferroni
│   ├── interpretability.py  # SHAP, sensitivity, perturbation, VIF
│   └── requirements.txt     # Pinned dependencies
├── data/
│   ├── raw/                 # Unmodified downloaded files (checksummed)
│   ├── processed/           # Cleaned CSVs, descriptors, splits
│   └── artifacts/           # Models, reports, plots
├── tests/
│   ├── unit/
│   └── integration/
└── state/
    └── projects/PROJ-373-predicting-rate-constants-of-sn1-reactio.yaml
```

**Structure Decision**: Single-project structure chosen for tight coupling of data, model, and evaluation. All scripts in `code/` are runnable end-to-end.

## Complexity Tracking

No violations detected. Complexity is justified by the need for Nested CV, scaffold splitting, and rigorous statistical testing as mandated by the spec.

## Statistical Methodology

- **Nested Cross-Validation**:
  - **Outer Loop**: Scaffold splitting (using RDKit `GetScaffold` or Morgan fingerprints) to ensure chemically distinct molecules are in train/test splits. This prevents data leakage from similar structures and ensures generalization to unseen chemistry.
  - **Inner Loop**: 5-fold CV (reduced to 3-fold if dataset size > 2000 to maintain 6h budget) for hyperparameter tuning.
- **Hyperparameter Optimization**: Random search (≤50 configurations) as per Berthold et al. (2018) efficiency findings.
- **Baseline Comparison**: Linear Regression and KRR use the *exact same* Gasteiger/topological descriptors as the MPNN's initial node features. This ensures a fair comparison of "Non-linear Graph Learning vs Linear Regression on the same feature space". The MPNN learns message passing from the graph topology, while the baseline is constrained to the same input space to isolate the benefit of the architecture.
- **Statistical Significance**: Bootstrap (1000 iterations, seed=42) for confidence intervals. Holm-Bonferroni correction applied to all pairwise comparisons (MPNN vs Random/Linear/KRR on R²/MAE).

## Compute Feasibility

- **Dynamic Budgeting**:
  - If dataset size N < 500: Full Nested CV with multiple folds and multiple configurations.
  - If 500 ≤ N < 2000: Nested CV with multiple folds and multiple configurations.
  - If N ≥ 2000: Nested CV (multiple repetitions and folds) with 20 configs.
  - This ensures the total number of training runs (Outer * Inner * Configs) remains within the 6-hour CPU limit.
- **Memory**: Streaming or chunked processing if dataset > 7GB RAM.
- **No GPU**: All operations are CPU-optimized.

## Implementation Phases

### Phase 0: Data Ingestion & Validation
- Download `DTS-SN1-15-01-2024` and `SN18-All-20240204`.
- Verify presence of `SMILES`, `rate_constant`, `substrate_class`, `temperature`, `solvent`.
- Exclude datasets missing any required column (FR-009).
- **Distribution Shift Check**: Harmonize units (convert all rates to s⁻¹) and check for experimental condition shifts between datasets. Exclude rows with inconsistent units or unresolvable condition shifts.
- Output: `data/processed/cleaned.csv`, `data/processed/exclusion_log.csv`.

### Phase 1: Descriptor Computation & Splitting
- Compute Gasteiger charges and topological indices using RDKit.
- Filter rows with unparseable SMILES or failed descriptor calculation.
- Stratified split (70/15/15) by `substrate_class`.
- Output: `data/processed/descriptors.csv`, `data/processed/split_train.csv`, etc.

### Phase 2: Model Training (Nested CV)
- Execute Nested CV with scaffold splitting (outer) and random search (inner).
- Train MPNN, Linear Regression, and KRR baselines.
- Save best model and metrics.
- Output: `artifacts/model.pt`, `artifacts/metrics.json`.

### Phase 3: Evaluation & Success Criterion Verification
- Calculate R² and MAE for all models on the held-out test set.
- Perform bootstrap comparison with Holm-Bonferroni correction.
- **SC-001 Verification**: Explicitly check if `MPNN_R2 - Linear_R2 > 0.05` AND `p < 0.05`. Output `PASS` or `FAIL`. If significant but < 0.05, report as "Statistically significant but below magnitude threshold".
- Output: `artifacts/comparison_report.json`.

### Phase 4: Sensitivity Analysis (FR-006)
- Sweep top-k descriptors (k=1 to 10) based on absolute SHAP value.
- Retrain/evaluate model with reduced feature set.
- Report variance in R².
- Output: `artifacts/sensitivity_report.md`.

### Phase 5: Perturbation Study (FR-008)
- Remove top SHAP features from the input.
- Measure the drop in R².
- Output: `artifacts/perturbation_report.md`.

### Phase 6: Interpretability & Consistency (SC-004)
- Generate SHAP summary plot.
- **Consistency Check**: Re-run model with multiple different seeds and compare SHAP rankings.
- Run VIF diagnostic on **all descriptor classes EXCEPT Gasteiger charges** (as mandated by FR-007). Pairs with VIF > 5 are flagged for joint analysis.
- Output: `artifacts/shap_report.md`, `artifacts/vif_report.json`, `artifacts/shap_consistency_report.md`.

### Phase 7: Final Report Generation
- Aggregate all metrics, reports, and limitations.
- Generate `artifacts/final_report.md`.

## Limitations

- **Substrate Class Discretization**: The model relies on explicit "secondary/tertiary" labels. This discretization may introduce label noise as the true physical driver (carbocation stability) is continuous. This limitation is explicitly reported in the final output.
- **Power Limitations**: If N < 500, the study is framed as a feasibility demonstration with limited power to detect small effects (R² diff < 0.05).
- **Collinearity**: Gasteiger charges are excluded from VIF testing per FR-007, limiting the ability to detect collinearity between electronic and topological signals derived from the same algorithm.