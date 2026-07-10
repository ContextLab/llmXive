# Implementation Plan: Predicting Molecular Excitation Wavelengths from SMILES with Graph Neural Networks

**Branch**: `001-predict-molecular-excitation-wavelengths` | **Date**: 2024-05-22 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-predict-molecular-excitation-wavelengths/spec.md`

## Summary

This project implements a Graph Neural Network (GNN) to predict the maximum excitation wavelength ($\lambda_{max}$) of organic molecules directly from their SMILES strings. The approach prioritizes computational feasibility on CPU-only infrastructure (GitHub Actions free tier) while maintaining scientific rigor through scaffold-based data splitting to prevent structural leakage. The pipeline ingests UV-Vis data (prioritizing experimental sources), converts SMILES to molecular graphs using RDKit, trains a lightweight message-passing GNN (<1M parameters), and compares performance against an ECFP fingerprint + Ridge Regression baseline.

## Technical Context

**Language/Version**: Python 3.10  
**Primary Dependencies**: `rdkit`, `torch` (CPU version), `torch-geometric` (CPU compatible), `pandas`, `scikit-learn`, `numpy`, `pyyaml`  
**Storage**: Local filesystem (CSV/Parquet artifacts under `data/`)  
**Testing**: `pytest` (unit tests for data parsing, integration tests for pipeline flow)  
**Target Platform**: Linux (GitHub Actions free-tier runner: limited vCPU, 7GB RAM, no GPU)  
**Project Type**: Data Science / Machine Learning Pipeline  
**Performance Goals**: Complete end-to-end training and evaluation within 6 hours; MAE < 30 nm on test set (if experimental data available).  
**Constraints**: No GPU usage; memory footprint < 7GB; no external API calls during runtime (datasets pre-fetched or cached); strict scaffold splitting.  
**Scale/Scope**: Dataset size limited to fit within 7GB RAM (sampled if necessary) while ensuring test set n≥50 for statistical power.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/`. External datasets fetched from verified HuggingFace URLs. `requirements.txt` pins exact versions. |
| **II. Verified Accuracy** | **PASS** | **Task Added**: `verify-accuracy-gate` runs Reference-Validator logic to check dataset URLs and title overlap before execution. |
| **III. Data Hygiene** | **PASS** | Raw data stored in `data/raw/` with checksums. Derived data in `data/processed/`. No in-place modifications. |
| **IV. Single Source of Truth** | **PASS** | All metrics in `paper/` derived from `code/` output CSVs. No hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | **Task Added**: `generate-hashes` script computes content hashes for artifacts and updates `state/` YAML file. |
| **VI. Spectral-Prediction Accuracy** | **PASS** | Plan targets MAE < 30 nm; failure defined as > 50 nm. **Fallback**: If data is computed, criteria redefined to match ground truth. |
| **VII. Structural Leakage Prevention** | **PASS** | Data split logic explicitly implements Bemis-Murcko scaffold splitting with a dominant training partition and balanced validation and test sets. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-molecular-excitation-wavelengths/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-379-predicting-molecular-excitation-waveleng/
├── data/
│   ├── raw/                 # Downloaded raw CSVs/Parquets
│   ├── processed/           # Cleaned, split CSVs with scaffold IDs
│   └── checksums.txt        # MD5/SHA256 hashes of raw data
├── code/
│   ├── __init__.py
│   ├── ingest.py            # FR-001: Data ingestion & cleaning (PubChem + UV-Vis)
│   ├── validate_data.py     # Data Validity Gate: Check for experimental columns
│   ├── split.py             # FR-002: Scaffold splitting
│   ├── model.py             # FR-003: GNN & Baseline definitions
│   ├── train.py             # FR-003: Training loop
│   ├── evaluate.py          # FR-004: MAE/R2 calculation
│   ├── explain.py           # FR-005: Feature attribution
│   ├── sensitivity.py       # FR-006: Threshold sweeping
│   ├── collinearity_check.py# FR-007: Collinearity & Redundancy detection
│   ├── utils.py             # Common helpers (RDKit, logging)
│   └── hash_artifacts.py    # Versioning: Generate hashes & update state
├── tests/
│   ├── test_ingest.py
│   ├── test_split.py
│   └── test_model.py
├── data-model.md            # Schema definitions
├── requirements.txt         # Pinned dependencies
└── README.md                # Quickstart guide
```

**Structure Decision**: Single-project structure selected to minimize overhead and align with the computational constraints (CPU-only, small model). The `code/` directory is organized by functional phase (ingest, split, model, train, evaluate) to match the user story flow and ensure testability of each FR.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Scaffold Splitting** | Required by **Constitution Principle VII** and **FR-002** to prevent data leakage. | Random splitting would allow molecules with identical cores in train and test, inflating performance metrics and violating scientific validity. |
| **GNNExplainer** | Required by **FR-005** for interpretability. | Simple feature importance (e.g., permutation) on a GNN is less granular and does not identify specific substructures/atoms as required. |
| **CPU-Only Constraint** | Required by **SC-002** (Compute Feasibility). | GPU-based training is impossible on the target CI environment; using a smaller model and sampled data is the only viable path. |
| **Ridge Regression Baseline** | Required to prevent overfitting on high-dimensional ECFPs with small datasets. | Unregularized linear regression on sparse fingerprints is prone to overfitting and does not constitute a "strong" baseline. |

## Implementation Phases

### Phase 0: Data Validity & Acquisition
1. **Verify Datasets**: Run `verify-accuracy-gate` to confirm UV-Vis ML dataset URL and check for experimental columns (`lambda_max_exp`).
2. **Ingest Data**:
   - Ingest `UV-Vis ML` CSV (Primary).
   - Ingest `PubChem` SMILES (Secondary, for validation/scaffold diversity).
   - **FR-001**: Parse SMILES, validate with RDKit, handle duplicates (median λmax).
3. **Data Validity Gate**:
   - If `lambda_max_exp` column exists: Proceed with experimental target.
   - If only computed values exist: **Reframe SC-001** to "prediction of computed values" and log the limitation.

### Phase 1: Data Processing & Splitting
1. **Scaffold Split**:
   - Generate Bemis-Murcko scaffolds.
   - Split data into training, validation, and test sets ensuring no scaffold leakage (**FR-002**, **Constitution VII**).
   - **Power Analysis**: Ensure test set size ≥ 50. If not, adjust sampling or report low power.
2. **Collinearity Check**:
   - **FR-007**: Calculate Pearson correlation for ECFP bits. Flag if r ≥ 0.9.
   - **FR-007**: Calculate latent cosine similarity for GNN subgraphs. Flag if > 0.9.

### Phase 2: Model Training
1. **Train Baseline**: ECFP + Ridge Regression (Regularized) (**FR-004**).
2. **Train GNN**: MPNN (2-3 layers, <1M params) (**FR-003**).
   - CPU-only, early stopping, fixed seed.
3. **Versioning**: Generate content hashes for `model.pt` and update `state/` YAML (**Constitution V**).

### Phase 3: Evaluation & Attribution
1. **Evaluate**: Compute MAE, R², and Wilcoxon signed-rank test (**SC-005**).
   - **Low Power Handling**: If n<50, report effect size (delta MAE) as descriptive, not hypothesis test.
2. **Attribution**: GNNExplainer on test set (**FR-005**).
   - Apply redundancy masks for flagged subgraphs (**FR-007**).
3. **Sensitivity**: Sweep MAE thresholds (**FR-006**).
4. **Output**: Generate `metrics.json` with collinearity flags, redundancy masks, and power status.

## Fallback Success Criteria

If the dataset contains **only computed** $\lambda_{max}$ values:
- **SC-001**: Success is defined as MAE < 30 nm against *computed* ground truth (not experimental noise floor).
- **Constitution VI**: The "experimental noise floor" assumption is explicitly invalidated, and the report will state this limitation clearly.

## Risk Mitigation

| Risk | Impact | Mitigation Strategy |
| :--- | :--- | :--- |
| **Dataset lacks experimental $\lambda_{max}$** | High: Invalidates SC-001 noise floor assumption. | **Data Validity Gate** detects this; SC-001 is reframed to computed ground truth. |
| **Dataset too large for 7GB RAM** | High: Pipeline crashes. | Implement chunked loading or random sampling ensuring test set n≥50. |
| **Scaffold split yields <50 test samples** | High: Statistical test invalid. | Adjust sampling or report results as descriptive (low power). |
| **GNN fails to converge on CPU** | Medium: No results. | Switch to baseline (ECFP+Ridge) as primary result if GNN fails. |
| **Unregularized Baseline Overfits** | Medium: Unfair comparison. | **Mandatory Ridge/Lasso regularization** for baseline model. |

## Compute Feasibility Strategy

- **Hardware Target**: GitHub Actions Free Tier (limited CPU resources, 7GB RAM, 6h limit).
- **Memory Management**:
  - Data loading uses `pandas` with `dtype` optimization.
  - Sampling strategy ensures test set n≥50 while fitting in RAM.
  - Batch size tuned (e.g., or 64).
- **Time Management**:
  - Training epochs limited to a moderate range with early stopping.
  - Model size strictly capped at <1M parameters.
  - No GPU/CUDA code paths.
- **Libraries**:
  - `torch`: CPU wheel only.
  - `torch-geometric`: CPU compatible version.
  - `rdkit`: Pre-compiled wheel.