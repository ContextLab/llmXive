# Implementation Plan: Exploring the Potential for Machine Learning to Identify Novel Phase Transitions in Isotropic Systems

**Branch**: `001-gene-regulation` | **Date**: 2026-07-14 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary

This project implements a CPU-tractable unsupervised machine learning pipeline to detect phase transitions in 2D isotropic spin systems (J1-J2 Heisenberg and XY models). The approach utilizes a Variational Autoencoder (VAE) to learn a compressed latent representation of Monte Carlo spin configurations. The critical temperature $T^*$ is identified via peak detection in the variance of the latent means, validated against independent physical observables (magnetic susceptibility) and Finite-Size Scaling (FSS) extrapolations. The implementation strictly adheres to the -hour runtime and 7 GB RAM constraints of the GitHub Actions free-tier runner.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scikit-learn`, `torch` (CPU-only build), `matplotlib`, `scipy`, `pandas`  
**Storage**: Local file system (`data/`, `code/`) for intermediate tensors and model checkpoints.  
**Testing**: `pytest` for unit tests; `pytest-timeout` for CI enforcement.  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, ~7 GB RAM).  
**Project Type**: Computational research / data science pipeline.  
**Performance Goals**: Total runtime ≤ 6 hours; Memory footprint ≤ 6 GB.  
**Constraints**: No GPU/CUDA; no 8-bit/4-bit quantization; no large-LLM inference. Data must be sampled or generated on-the-fly to fit memory.  
**Scale/Scope**: Lattice sizes L=16 and L=24; Temperature range T=0.1 to T=3.0; Latent dimension 10.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Verification Step |
|-----------|--------|-------------------|
| **I. Reproducibility** | **Pass** | All random seeds will be pinned in `code/`. Data generation scripts will be deterministic. |
| **II. Verified Accuracy** | **Pass** | All external citations, including textbooks, MUST be verified by the Reference-Validator Agent against the primary source or a canonical DOI with title-token-overlap ≥ 0.7. No fallback to unverified references is permitted. |
| **III. Data Hygiene** | **Pass** | Raw MC data (if pre-generated) will be checksummed. Generated data will be written to new files with derivation logs. Model checkpoints will be checksummed and metadata validated against `model-checkpoint.schema.yaml`. |
| **IV. Single Source of Truth** | **Pass** | All figures and statistics in `paper/` will be generated programmatically from `data/` and `code/`. |
| **V. Versioning Discipline** | **Pass** | Artifacts will carry content hashes; state file updated on change. |
| **VI. Latent-Space Criticality** | **Pass** | Primary metric is latent variance peak (FR-005), not reconstruction error. The fallback to reconstruction error is ONLY for reporting "No significant transition detected" and does NOT redefine $T^*$. |
| **VII. Independent Physical Verification** | **Pass** | ML results cross-validated against magnetic susceptibility $\chi$ (FR-008). For Heisenberg model, validation acknowledges absence of finite-$T_c$. |

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── spin-config.schema.yaml
    ├── dataset.schema.yaml
    ├── latent-output.schema.yaml
    ├── latent_schema.schema.yaml
    └── model-checkpoint.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-111-exploring-the-potential-for-machine-lear/
├── data/
│   ├── raw/                 # Raw MC configurations (generated or downloaded)
│   ├── processed/           # Normalized tensors (.npy)
│   └── checksums.txt        # SHA256 hashes
├── code/
│   ├── __init__.py
│   ├── data_generation.py   # MC simulation (if needed) or loader
│   ├── preprocessing.py     # Normalization, reshaping, splitting
│   ├── vae_model.py         # VAE architecture (Conv/Deconv)
│   ├── train.py             # Training loop with early stopping
│   ├── analysis.py          # Latent variance, peak finding, FSS
│   └── utils.py             # Autocorrelation, thinning, plotting
├── tests/
│   ├── unit/                # Unit tests for shapes, normalization
│   ├── integration/         # End-to-end pipeline tests
│   └── contract/            # Schema validation tests
├── requirements.txt         # Pinned dependencies
└── README.md                # Project overview
```

**Structure Decision**: Single project structure chosen to minimize I/O overhead and simplify dependency management for a research pipeline. All data processing and modeling occur in the `code/` directory, with outputs written to `data/`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Finite-Size Scaling (FSS)** | Required for extrapolation to $L \to \infty$ (FR-010). | Single-size analysis cannot confirm thermodynamic limit behavior. (Note: For J1-J2, FSS is limited to pseudo-critical temps due to unknown universality). |
| **Bootstrap Resampling** | Required for 95% CI (FR-006). | Analytical error estimation is unreliable for non-Gaussian latent distributions. |
| **Autocorrelation Thinning** | Required to ensure independent samples (FR-006). | Naive bootstrapping on correlated MC chains yields underestimated confidence intervals. |
| **GP Hyperparameter Sensitivity** | Required to ensure robust peak detection (Methodology Concern). | Fixed hyperparameters may introduce bias or miss peaks. |
