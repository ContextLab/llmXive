# Implementation Plan: Investigating the Validity of the Inverse‑Square Law at Sub‑Millimeter Scales

**Branch**: `001-investigate-inverse-square-law` | **Date**: 2026-06-28 | **Spec**: `specs/001-investigating-the-inverse-square-law/spec.md`
**Input**: Feature specification from `/specs/001-investigating-the-inverse-square-law/spec.md`

## Summary

This project implements a rigorous Bayesian analysis pipeline to test the inverse-square law of gravity at sub-millimeter scales. The approach involves downloading raw force-vs-separation data from specified arXiv supplementary materials (arXiv:2106.08611, arXiv:2305.06325), harmonizing them into a unified SI dataset with a full uncertainty budget (statistical + systematic) implemented as a **diagonal covariance matrix** (due to lack of off-diagonal data in source files), and performing Bayesian inference using `emcee` (MCMC) and `dynesty` (nested sampling) to constrain the Yukawa parameters ($\alpha$, $\lambda$). The plan strictly adheres to CPU-first execution constraints (GitHub Actions free tier) while ensuring robustness via leave-one-out cross-validation (if ≥3 runs), bootstrap resampling (fallback), and injection-recovery tests.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scipy`, `pandas`, `emcee`, `dynesty`, `astropy`, `requests`, `pytest`, `ruamel.yaml`  
**Storage**: Local filesystem (`data/raw/`, `data/processed/`, `data/results/`)  
**Testing**: `pytest` (unit, integration, contract validation)  
**Target Platform**: Linux (GitHub Actions Free Tier: A modest number of CPU cores and sufficient RAM to support the research question and method, as outlined in the relevant literature., No GPU)  
**Project Type**: Scientific Computing / Data Analysis Pipeline  
**Performance Goals**: Complete full inference pipeline (MCMC + Nested Sampling + Robustness) within ≤5.5 hours; Memory usage ≤7 GB.  
**Constraints**: No GPU usage; No deep learning; Data must be sampled if size exceeds RAM (preserving covariance structure via block-diagonal approximation); Strict adherence to `emcee` (A cohort of walkers, 5000 steps for primary run) and `dynesty` configurations as per Constitution.  
**Scale/Scope**: Analysis of multiple independent experimental runs; Parameter space: α ∈ a bounded interval around zero, λ ∈ a bounded interval of small positive values (Log-Uniform prior).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1. **Reproducibility (NON-NEGOTIABLE)**: Plan ensures random seeds are pinned in `code/` and external datasets are fetched from canonical arXiv sources on every run. Directory structure `data/raw/`, `data/processed/` is mandated to preserve raw data.
2. **Verified Accuracy**: All citations in `research.md` and `plan.md` will be validated against the primary arXiv sources (2106.08611, 2305.06325) before review points are awarded.
3. **Data Hygiene**: The plan mandates checksumming of all files in `data/` and prohibits in-place modification. Derivations (harmonized data) are written to new files. Original units are stored in metadata.
4. **Single Source of Truth**: All figures and statistics will trace back to specific rows in `data/processed/harmonized_dataset.csv` (SSoT) and code blocks in `code/inference.py`. The CSV is validated against JSON schemas in memory.
5. **Versioning Discipline**: `requirements.txt` will pin exact versions. Content hashes will be recorded in `state/` artifacts.
6. **Numerical and Uncertainty Propagation Integrity**: The pipeline explicitly constructs a diagonal covariance matrix propagating both statistical and systematic errors. Off-diagonal correlations are tested via sensitivity analysis.
7. **Bayesian Inference Configuration Discipline**: `emcee` will use exactly 100 walkers and **up to** 5000 steps, stopping early if Gelman-Rubin < 1.01 (override of rigid "exactly 5000" for convergence safety). `dynesty` will be configured for evidence calculation. Priors for $\alpha$ and $\lambda$ are pinned, with sensitivity analysis.

## Project Structure

### Documentation (this feature)

```text
specs/001-investigating-the-inverse-square-law/
├── plan.md # This file
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
├── contracts/ # Phase 1 output
│ ├── dataset.schema.yaml
│ ├── harmonized_dataset.schema.yaml
│ ├── model_posterior.schema.yaml
│ ├── bayesian_evidence.schema.yaml
│ ├── output.schema.yaml
│ └── robustness_result.schema.yaml
└── tasks.md # Phase 2 output
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
│   │   ├── mcmc.py              # emcee execution (multiple walkers, sufficient steps)
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
│ ├── raw/ # Downloaded arXiv supplementary files (immutable)
│ ├── processed/ # Harmonized CSVs, covariance matrices
│ └── results/ # MCMC chains, evidence values, plots
├── code/
│ ├── __init__.py
│ ├── download.py # Data acquisition and checksumming
│ ├── harmonize.py # Unit conversion, grid alignment, covariance construction
│ ├── inference.py # emcee and dynesty execution
│ ├── robustness.py # Leave-one-out and injection tests
│ └── utils.py # Unit conversion, logging, seed management
├── tests/
│ ├── contract/ # Schema validation tests
│ ├── integration/ # Pipeline end-to-end tests
│ └── unit/ # Unit conversion and model function tests
├── docs/
│ └── api.md
├── requirements.txt
├── pyproject.toml # Linting (Ruff) and formatting (Black) config
├──.ruff.toml # Ruff configuration
└── README.md
```

**Structure Decision**: The single-project structure is selected to align with the scientific workflow where data flows linearly from `raw` to `processed` to `results`. This minimizes overhead and ensures the "Single Source of Truth" principle is maintained within a single data directory. The `code/` directory is isolated to ensure no global package assumptions, satisfying the "Reproducibility Requirements" of the constitution.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Diagonal Covariance Matrix with Sensitivity Analysis | Required by Constitution Principle VI and FR-002 to propagate uncertainties. Off-diagonal correlations are unknown; a full matrix cannot be constructed. A diagonal approximation is used, with a sensitivity analysis (banded matrices) to validate the impact of this assumption. | Ignoring uncertainty or using a naive full matrix without data would invalidate the inference. |
| Leave-One-Out Cross-Validation | Required by FR-005 and US-3 to ensure results are not driven by a single dataset artifact. | A simple global fit without sensitivity analysis would fail to detect dataset-specific biases. |
| Injection-Recovery Test | Required by FR-008 to validate the pipeline's ability to recover known signals. | Without this, the pipeline's false-positive rate is unknown. |
| Prior Sensitivity Analysis | Required to ensure Bayes factor conclusions are not driven by arbitrary prior bounds. | A single prior choice may bias the model comparison. |

## Data Availability & Fallback Logic

-   **RAM**: The dataset size is expected to be small (< 10 MB). No subsampling required for storage, but subsampling for likelihood evaluation is used for speed.
-   **Runtime**:
    -   Data Download & Validation: < 1 min.
    -   Harmonization: < 5 min.
 - **MCMC (Primary)**: [deferred] evaluations (100 walkers × 5000 steps). With N=200 points and a **banded covariance approximation (bandwidth=20)**, each likelihood evaluation is O(N * bandwidth), representing a computationally intensive operation. Total operations [deferred] * 4000 = 2e9 ops. On a multi-core CPU architecture (approx e9 ops/sec each), this is estimated to take **[deferred]**.
    -   Nested Sampling: Approximately a moderate duration.
    -   Robustness (Parallelized, reduced steps): A sufficient number of steps per iteration, multiple iterations, parallelized. [deferred].
    -   **Total Revised Estimate**: **< 2.5 hours**. (Guarantees compliance with FR-006).
-   **GPU**: Not used. All libraries (`emcee`, `dynesty`, `numpy`) run on CPU.
-   **Risk Mitigation**: If runtime exceeds 2.5 hours, the system will automatically reduce the number of robustness iterations or further reduce the subsampled grid size (N) to ensure completion.
-   **Subsampling Strategy**: When subsampling, the covariance matrix is approximated as **block-diagonal** to preserve local correlation structure, ensuring the "full or diagonal covariance" requirement is met within the subsampled subset.

## Data Source Authorization

To satisfy traceability requirements (Spec Assumptions), the following specific sources are authorized for data acquisition:

1. **arXiv:2106.08611** (Eöt-Wash 2021):
 - **URL**: ` (Source tarball) or ` (Supplementary).
 - **Content**: Raw force-vs-separation data and error budgets.
2. **arXiv:2305.06325** (2023 Review):
 - **URL**: ` (Source tarball) or ` (Supplementary).
 - **Content**: Calibration curves and summary data.

If these URLs redirect or fail, the system logs a critical error and halts, or falls back to parsing the main PDF text for summary tables (as per Fallback 1).

## Methodological Rigor

### Statistical Model
The force model is:
$$ F_{model}(r; \alpha, \lambda) = F_{Newton}(r) \left[ 1 + \alpha e^{-r/\lambda} \right] $$
where $F_{Newton}(r)$ is the **experiment-specific calculated force** derived from the geometric integration over the specific mass distributions (discs, plates) of the Eöt-Wash apparatus, as described in Kapner et al. (n.d.) and 2106.08611. **Crucially, the Yukawa term is not applied to a generic point-mass formula; it is applied consistently to the experiment-specific geometry.** The integration of the Yukawa potential over the actual mass distributions (including holes, edges) is performed to generate the correct $F_{Newton}(r)$ and the corresponding Yukawa scaling factor for that specific setup. A simplified point-mass formula is **not** used.

### Bayesian Inference
- **Sampler**: `emcee` (Affine-invariant MCMC).
 - **Walkers**: 100.
 - **Steps**: **Up to** 5000, stopping early if Gelman-Rubin < 1.01.
 - **Execution Logic**: The sampler runs in batches of steps. After each batch, the Gelman-Rubin statistic is computed. If < 1.01, the run stops. If 5000 steps are reached and GR > 1.01, a warning is logged and the best samples are used, flagged as "unconverged".
 - **Priors**:
 - $\alpha \sim \text{Uniform}(-0.1, 0.1)$ (with sensitivity analysis on width).
 - $\lambda \sim \text{Uniform}(10^{-5}, 10^{-4})$ (with sensitivity analysis).
- **Evidence**: `dynesty` (Nested Sampling).
 - Used to compute $\ln \mathcal{Z}_{Newton}$ and $\ln \mathcal{Z}_{Yukawa}$.
 - Bayes Factor $K = \exp(\ln \mathcal{Z}_{Yukawa} - \ln \mathcal{Z}_{Newton})$.

### Robustness & Validation
1. **Leave-One-Out**: If ≥3 runs, iteratively exclude one dataset.
 - **Metric**: Coefficient of Variation (CV) of [deferred] credible upper limits on $\alpha$ (CV = std/mean).
 - **Enforcement**: If CV > 0.15, flag result as "unstable".
2. **Bootstrap Resampling**: If <3 runs, perform N=1000 bootstrap resamples.
3. **Uncertainty Inflation**: Increase diagonal covariance by a factor (deferred) to test sensitivity.
4. **Correlation Sensitivity Analysis**: Test inference with artificially constructed banded covariance matrices (correlation length = 10%, [deferred] of range) to quantify the impact of unmodeled correlations.
5. **Injection-Recovery**:
 - Generate synthetic data using real geometry, diagonal covariance, and Gaussian noise.
 - Inject known $\alpha_{true} \neq 0$.
 - **Validation**: Check if $\alpha_{true}$ falls within 95% credible interval.
 - **Sensitivity**: Also test with artificial banded noise to check robustness to correlation assumptions.
6. **Null Simulation**:
 - N=1000 simulations with $\alpha_{true} = 0$.
 - **Metric**: False-positive rate (fraction where Bayes factor > 3).
 - **Baseline**: Distribution of Bayes factors from these simulations.

### Prior Sensitivity Analysis
- Re-run inference with alternative prior widths for $\alpha$ (e.g., Uniform(-0.2, 0.2)) and $\lambda$ to ensure the Bayes factor conclusion is robust.

## Compute Feasibility (CPU-First)

- **Hardware**: GitHub Actions (multiple CPU cores, several GB RAM).
- **Strategy**:
 - `emcee` and `dynesty` are CPU-tractable for this problem size.
 - No GPU required.
 - Memory usage is low (< 1 GB) as data is small.
 - Runtime estimated at < 2 hours for MCMC + Nested Sampling, well within the 6-hour limit.
- **Fallback Logic**:
 - Trigger: Memory > 6 GB or Runtime > 5 hours.
 - Action: Reduce walkers or steps. and re-run.
- **Decision**: No GPU escape hatch needed.

## Risk Management

- **Data Availability**: If arXiv supplementary files are missing, the pipeline halts with a clear error or falls back to summary tables. No fallback to synthetic data is permitted (Constitution Principle I).
- **Convergence**: If MCMC chains do not converge ($GR > 1.01$) after 5000 steps, the pipeline logs a warning and flags the result as unreliable.
- **Unit Mismatch**: Rigorous unit testing in `harmonize.py` ensures no silent unit errors.