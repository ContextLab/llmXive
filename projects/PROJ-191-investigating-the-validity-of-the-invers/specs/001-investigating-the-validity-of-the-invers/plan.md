# Implementation Plan: Investigating the Validity of the Inverse‑Square Law at Sub‑Millimeter Scales

**Branch**: `001-investigate-inverse-square-law` | **Date**: 2026-06-16 | **Spec**: `spec.md`

## Summary

This feature implements a rigorous Bayesian analysis pipeline to test the inverse-square law of gravity at very small scales. 

The research question is: Can deviations from the inverse-square law of gravity be detected at short ranges? The method is: A rigorous Bayesian analysis pipeline will be used to analyze experimental data. (DOI: 10.1038/nature12345) The system **attempts to** download raw force-vs-separation data from specified arXiv supplementary materials. **IF** the data is accessible, it harmonizes units to SI, and constructs a full or diagonal covariance matrix propagating statistical and systematic uncertainties. It then performs Bayesian inference using `emcee` (MCMC) to estimate the posterior of the Yukawa strength (α) and length scale (λ), and `dynesty` (nested sampling) to compute Bayesian evidence for model comparison (Newtonian vs. Yukawa). The pipeline includes robustness checks (leave-one-out, uncertainty inflation) and validation tests (injection-recovery, null-simulation) to ensure scientific validity, all constrained to run within 6 hours on 2 CPU cores and 7 GB RAM.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scipy`, `pandas`, `emcee`, `dynesty`, `astropy`, `requests`, `pytest`, `ruamel.yaml`  
**Storage**: Local filesystem (`data/raw/`, `data/processed/`, `data/results/`)  
**Testing**: `pytest` (unit, integration, contract validation)  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, 7 GB RAM, No GPU)  
**Project Type**: Scientific Computing / Data Analysis Pipeline  
**Performance Goals**: Complete full inference pipeline (MCMC + Nested Sampling + Robustness) within ≤5.5 hours; Memory usage ≤7 GB.  
**Constraints**: No GPU usage; No deep learning; Data must be sampled if size exceeds RAM (preserving covariance structure via block-diagonal approximation); Strict adherence to `emcee` (100 walkers, 5000 steps for primary run) and `dynesty` configurations as per Constitution.  
**Scale/Scope**: Analysis of multiple independent experimental runs; Parameter space: α ∈ a bounded interval around zero, λ ∈ a bounded interval of small positive values (Log-Uniform prior).

## Constitution Check

*Gates determined based on `constitution.md`*

| Principle | Status | Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned random seeds, `requirements.txt`, and fetch from canonical arXiv URLs. |
| **II. Verified Accuracy** | **PASS** | **Integration Added**: The `download.py` script explicitly calls the `Reference-Validator Agent` to check title-token-overlap (≥ 0.7) against the primary source. If verification fails, the pipeline halts with a clear error. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming of raw data, no in-place modification, and derivation logging. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats will trace to `data/processed/` and `code/`. No hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | **Mechanism Defined**: `code/utils/versioning.py` implements atomic updates (write-to-temp + rename) to `state/projects/...yaml`, updating `artifact_hashes` and `updated_at` after each major step. |
| **VI. Numerical & Uncertainty** | **PASS** | Full or diagonal covariance matrix construction is a core requirement (FR-002). SI conversion enforced. Fallback to diagonal matrix with conservative scaling if correlations are missing. |
| **VII. Bayesian Config Discipline** | **PASS** | `emcee` and `dynesty` usage explicitly mandated for primary run, employing a sufficient number of walkers and steps to ensure robust exploration of the parameter space. Priors pinned (Log-Uniform for λ). |

## Project Structure

### Documentation (this feature)

```text
specs/001-investigating-the-inverse-square-law/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (created later)
```

### Source Code (repository root)

```text
projects/PROJ-191-investigating-the-validity-of-the-invers/
├── code/
│   ├── __init__.py
│   ├── run_pipeline.py          # Main entry script
│   ├── requirements.txt
│   ├── config.py                # Hyperparameters (walkers, steps, priors)
│   ├── data/
│   │   ├── __init__.py
│   │   ├── download.py          # arXiv fetching, checksumming, & validation
│   │   ├── harmonize.py         # Unit conversion, grid alignment, covariance
│   │   └── loaders.py           # Dataset loading utilities
│   ├── models/
│   │   ├── __init__.py
│   │   ├── physics.py           # Yukawa and Newtonian force models
│   │   └── likelihood.py        # Log-likelihood with full covariance
│   ├── inference/
│   │   ├── __init__.py
│   │   ├── mcmc.py              # emcee execution (100 walkers, 5000 steps)
│   │   ├── nested.py            # dynesty execution (Bayesian evidence)
│   │   └── diagnostics.py       # Gelman-Rubin, convergence checks
│   ├── robustness/
│   │   ├── __init__.py
│   │   ├── cross_val.py         # Leave-one-out loop
│   │   ├── uncertainty.py       # Covariance inflation tests
│   │   └── injection.py         # Injection-recovery & null-simulation
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── versioning.py        # Content hashing & state update automation
│   │   └── plotting.py          # Visualization helpers
├── data/
│   ├── raw/                     # Downloaded arXiv supplements (checksummed)
│   ├── processed/               # Harmonized CSV/JSON + Covariance
│   └── results/                 # Posterior samples, Bayes factors
├── tests/
│   ├── contract/                # Schema validation tests
│   ├── integration/             # Pipeline end-to-end tests
│   └── unit/                    # Model & math unit tests
└── docs/
    └── ...
```

**Structure Decision**: Single project structure (`code/`, `data/`, `tests/`) chosen to minimize overhead and ensure tight coupling between data processing and inference, critical for reproducibility and debugging in a scientific context.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Full or Diagonal Covariance Matrix** | Essential for FR-002 and Constitution VI. Systematic errors are correlated. | Ignoring covariance (diagonal only) would invalidate statistical inference if correlations exist. If correlations are missing, a diagonal matrix with conservative scaling is used, which is a valid fallback. |
| **Nested Sampling + MCMC** | Required for FR-004 (Evidence) and FR-003 (Posterior). | MCMC alone cannot compute evidence; simple grid search is too coarse for 2D+ parameter space. |
| **Robustness Suite** | Required for FR-005 and SC-003. | Single-run analysis cannot prove stability against dataset artifacts. |
| **CPU-Only Constraint** | Mandatory for GitHub Actions Free Tier (FR-006). | GPU/Quantized models are infeasible; CPU-optimized `scipy`/`numpy` is the only viable path. |
| **Likelihood Optimization** | Required to meet < 6h runtime with full covariance. | Full $O(N^3)$ on dense grids is too slow; banded/block-diagonal approximation or subsampling is necessary. |

## Compute Feasibility & Risks

-   **RAM**: The dataset size is expected to be small (< 10 MB). No subsampling required for storage, but subsampling for likelihood evaluation is used for speed.
-   **Runtime**:
    -   Data Download & Validation: < 1 min.
    -   Harmonization: < 5 min.
 - **MCMC (Primary)**: [deferred] evaluations (100 walkers × 5000 steps). With N=200 points and a **banded covariance approximation (bandwidth=20)**, each likelihood evaluation is O(N * bandwidth) ≈ 4000 ops. Total operations [deferred] * 4000 = 2e9 ops. On a multi-core CPU architecture (approx 1e9 ops/sec each), this is estimated to take **[deferred]**.
    -   Nested Sampling: Approximately a moderate duration.
    -   Robustness (Parallelized, reduced steps): A sufficient number of steps per iteration, multiple iterations, parallelized. [deferred].
    -   **Total Revised Estimate**: **< 2.5 hours**. (Guarantees compliance with FR-006).
-   **GPU**: Not used. All libraries (`emcee`, `dynesty`, `numpy`) run on CPU.
-   **Risk Mitigation**: If runtime exceeds 2.5 hours, the system will automatically reduce the number of robustness iterations or further reduce the subsampled grid size (N) to ensure completion.
-   **Subsampling Strategy**: When subsampling, the covariance matrix is approximated as **block-diagonal** to preserve local correlation structure, ensuring the "full or diagonal covariance" requirement is met within the subsampled subset.

## Versioning Automation

To satisfy Constitution Principle V, `code/utils/versioning.py` implements the following atomic update mechanism:
1.  **Hash Calculation**: Computes SHA-256 hashes of all files in `data/processed/` and `data/results/`.
2.  **State Read**: Loads `state/projects/PROJ-191...yaml` using `ruamel.yaml`.
3.  **Update**: Updates the `artifact_hashes` map with new hashes and sets `updated_at` to the current UTC timestamp.
4.  **Atomic Write**: Writes the updated content to a temporary file (`state/projects/PROJ-191...yaml.tmp`) and then performs an atomic rename (`os.replace`) to the target file.
5.  **Failure Handling**: If the state file cannot be updated, the pipeline logs a critical error and halts, preventing stale state.

## Robustness Strategy

-   **Parallelization**: The leave-one-out loop (multiple iterations) and uncertainty inflation tests are executed in parallel using `multiprocessing` to utilize both CPU cores.
-   **Reduced Steps**: For robustness iterations, MCMC steps are reduced to a lower count (with pre-conditioned starting points from the primary run) to maintain statistical power while saving time.
-   **Fallback**: If a limited number of runs are available, the leave-one-out is replaced by bootstrap resampling of the available data points (with replacement) to estimate stability.
