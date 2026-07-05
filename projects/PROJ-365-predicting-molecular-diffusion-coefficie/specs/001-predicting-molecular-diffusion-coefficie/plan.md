# Implementation Plan: Predicting Molecular Diffusion Coefficients in Liquids with Graph Neural Networks

**Branch**: `001-predict-molecular-diffusion` | **Date**: 2026-06-26 | **Spec**: `specs/001-predict-molecular-diffusion-coefficie/spec.md`
**Input**: Feature specification from `/specs/001-predict-molecular-diffusion-coefficie/spec.md`

## Summary

This project implements a CPU-optimized Message Passing Neural Network (MPNN) to predict molecular diffusion coefficients in liquids using **verified experimental data from the NIST Thermodynamics Research Center (TRC)**. The system programmatically ingests diffusion data via the `thermo` Python library, featurizes molecules into graphs using RDKit (static topology), and combines them with scalar solvent descriptors (viscosity, dielectric constant) to train a lightweight GNN. 

Performance is benchmarked against two baselines: (1) a Linear Regression model on Morgan Fingerprints + Solvent Descriptors, and (2) a **Solvent-Only** model (viscosity + dielectric constant only) to isolate the contribution of molecular structure. The pipeline includes rigorous sensitivity analysis, ablation studies, and statistical significance testing. **Per FR-005, the primary statistical test is a paired t-test on per-sample absolute errors**, with a fallback to Wilcoxon signed-rank only if the Shapiro-Wilk test indicates non-normality of errors (addressing the methodology concern regarding error distribution assumptions).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `rdkit`, `torch` (CPU-only), `torch-geometric` (CPU-compatible), `scikit-learn`, `pandas`, `numpy`, `pyyaml`, `thermo` (for NIST data access)  
**Storage**: Local CSV/JSONL for raw/processed data; `data/` directory for artifacts.  
**Testing**: `pytest` for unit tests; integration tests via end-to-end pipeline execution on CI.  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, ~7GB RAM, no GPU).  
**Project Type**: Data science pipeline / CLI tool.  
**Performance Goals**: Full pipeline (ingestion, training, eval, sensitivity) must complete in ≤ 6 hours on CPU; memory usage < 7GB.  
**Constraints**: No CUDA/GPU usage; no large pre-trained LLMs; dataset must be sampled if >5k molecules to fit memory; strict handling of missing data (exclusion + logging).  
**Scale/Scope**: Dataset size variable (up to 5k molecules for training); handles a large-scale set of molecules for ingestion sampling if needed.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification Method |
|-----------|--------|---------------------|
| **I. Reproducibility** | PASS | `random.seed(42)` set in all scripts; `requirements.txt` pins versions; CI runs on fresh runner. |
| **II. Verified Accuracy** | PASS | Dataset sourced from NIST TRC via `thermo` library (verified source); no fabricated metrics. |
| **III. Data Hygiene** | PASS | Raw data checksums recorded; transformations write new files; `[MISSING_DATA_EXCLUDED]` logging implemented. |
| **IV. Single Source of Truth** | PASS | All stats in reports generated from `code/` execution; no hand-typed numbers in docs. |
| **V. Versioning Discipline** | PASS | Content hashes tracked in `state/`; `updated_at` timestamps updated on artifact change. |
| **VI. Static-to-Dynamic Fidelity** | PASS | Architecture uses RDKit graphs + scalar descriptors (viscosity, dielectric); no MD trajectories or time-series inputs. |
| **VII. Statistical Significance** | PASS | **Paired t-test** on absolute errors (per FR-005) with normality check; Wilcoxon fallback if non-normal. Baseline comparison mandatory (including Solvent-Only baseline). |

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-molecular-diffusion-coefficie/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-365-predicting-molecular-diffusion-coefficie/
├── data/
│   ├── raw/                 # Downloaded raw CSV/Parquet (from NIST via thermo)
│   ├── processed/           # Featurized JSONL, fingerprints
│   └── checksums.json       # Data integrity hashes
├── code/
│   ├── __init__.py
│   ├── ingestion.py         # FR-001, FR-002, FR-007: Data loading (NIST), SMILES validation, featurization
│   ├── models.py            # FR-003: MPNN, Linear Baseline, and Solvent-Only Baseline definitions
│   ├── train.py             # FR-004: Training loop, 5-fold CV, seed handling
│   ├── eval.py              # FR-005: Metrics, Paired t-test (with normality check), baseline comparison
│   ├── sensitivity.py       # FR-006: Hyperparameter sweep, ablation study
│   └── utils.py             # Logging, device checks, memory monitoring
├── tests/
│   ├── unit/
│   │   ├── test_ingestion.py
│   │   └── test_models.py
│   └── integration/
│       └── test_pipeline.py
├── docs/
│   └── reports/             # Generated PDFs/Markdown reports
└── requirements.txt
```

**Structure Decision**: Single-project structure with clear separation of `data/` (raw/processed) and `code/` (modular scripts). This aligns with the data science workflow and ensures reproducibility by keeping raw data immutable and processed data derived.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **CPU-Only Constraint** | Required for free-tier CI feasibility. | GPU methods (CUDA) are excluded due to hardware limits; CPU-optimized MPNN is the only viable path. |
| **Ablation Study** | Required to isolate graph contribution (SC-001). | Omitting it would fail to prove GNN superiority over simple descriptors. |
| **Solvent-Only Baseline** | Required to address scientific soundness (Solvent dominance). | Omitting it would make it impossible to distinguish molecular structure effects from solvent effects. |
| **Paired t-test (with normality check)** | Required by FR-005; Wilcoxon fallback added for robustness if normality fails. | Using only Wilcoxon would violate FR-005; using only t-test without check would be scientifically unsound if errors are non-normal. |
| **5-Fold CV** | Required for robust performance estimation (FR-004). | Single split is too volatile; LOO is too slow for >5k molecules. |
