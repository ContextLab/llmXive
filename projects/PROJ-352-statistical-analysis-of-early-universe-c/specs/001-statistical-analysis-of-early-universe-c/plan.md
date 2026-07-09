# Implementation Plan: Statistical Analysis of Early Universe CMB Fluctuations and Topological Defects

**Branch**: `001-cmb-defect-analysis` | **Date**: 2025-01-15 | **Spec**: `specs/001-cmb-defect-analysis/spec.md`
**Input**: Feature specification from `/specs/001-cmb-defect-analysis/spec.md`

## Summary

This project implements a statistical analysis pipeline to detect non-Gaussian signatures in the Cosmic Microwave Background (CMB) consistent with topological defects (e.g., cosmic strings). The technical approach involves downloading Planck SMICA CMB maps, applying Galactic masks with rigorous analytical corrections (Schmalzing & Gorski), computing three Minkowski Functionals (Area, Perimeter, Genus) at multiple thresholds, and comparing these against two sets of simulations: (1) A set of Gaussian random field realizations matching the Planck beam and noise covariance, and (2) A set of alternative hypothesis realizations with injected cosmic string templates at varying tensions (Gμ). The analysis is constrained to run on GitHub Actions free-tier hardware (limited CPU, 7GB RAM, no GPU) by utilizing `healpy` for map handling, `scikit-learn` for shrinkage covariance estimation, and `numpy` for statistical inference.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `healpy`, `numpy`, `scipy`, `scikit-learn`, `requests`, `astropy`, `matplotlib`
**Storage**: Local filesystem (`data/` for raw/processed maps, `output/` for results)
**Testing**: `pytest` (unit tests for mask application, functional computation, and statistical bounds)
**Target Platform**: Linux (GitHub Actions free-tier runner)
**Project Type**: Computational Physics / Data Analysis Pipeline
**Performance Goals**: Complete full pipeline (download, mask, compute Minkowski, simulate 2000 total realizations, statistical test) within ≤6 hours.
**Constraints**:
- No GPU usage (CPU-only `healpy` operations).
- Memory limit: Peak usage < 6.5GB to allow safety margin.
- Disk limit: < 14GB (requires careful streaming or deletion of intermediate simulation maps).
- Network: Retry logic for Planck archive (exponential backoff).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Strategy |
| :--- | :--- |
| **I. Reproducibility** | All random seeds pinned in `code/`. Data fetched from canonical Planck URL with checksum validation. `requirements.txt` pins all versions. |
| **II. Verified Accuracy** | **Enforcement Mechanism**: A CI step (`reference_validator.py`) runs before Phase 0 research begins. It checks all citations in `research.md` against the Planck Legacy Archive. If any URL is unreachable or title overlap < 0.7, the build fails. This acts as a blocking gate for Principle II. |
| **III. Data Hygiene** | Raw data stored in `data/raw/` with checksums. Derived data (masked maps) in `data/processed/`. No in-place modification. |
| **IV. Single Source of Truth** | All statistics in `quickstart.md` and `paper` artifacts generated programmatically from `data/processed/` and `output/` JSON. |
| **V. Versioning Discipline** | Content hashes of artifacts tracked in `state/projects/...yaml`. |
| **VI. Statistical Significance** | Null hypothesis (Gaussian) explicitly modeled. Alternative hypothesis (Cosmic String) explicitly modeled. Likelihood ratio test accounts for covariance via shrinkage estimator. Claims framed as associational. |
| **VII. Parameter Inference** | Cosmic string tension ($G\mu$) reported with 95% confidence intervals derived from the simulation distribution, not point estimates. |

## Project Structure

### Documentation (this feature)

```text
specs/001-cmb-defect-analysis/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-352-statistical-analysis-of-early-universe-c/
├── code/
│   ├── __init__.py
│   ├── download.py          # FR-001: Planck data acquisition
│   ├── mask.py              # FR-002: Galactic masking (Schmalzing & Gorski correction)
│   ├── minkowski.py         # FR-003: Minkowski Functional computation
│   ├── simulate.py          # FR-004: Gaussian & Alternative hypothesis generation
│   ├── statistics.py        # FR-005, FR-006: Shrinkage Covariance, LRT, Gmu bounds
│   └── main.py              # Orchestration
├── data/
│   ├── raw/                 # Downloaded Planck maps (checksummed)
│   └── processed/           # Masked maps, simulation outputs
├── output/
│   └── results.json         # FR-005: Final statistical results
├── tests/
│   ├── test_download.py
│   ├── test_mask.py
│   ├── test_minkowski.py
│   └── test_statistics.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure selected to minimize overhead for a data-analysis pipeline. `code/` contains modular scripts for each functional requirement. `data/` separates raw and processed artifacts to satisfy Data Hygiene.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **None** | The project scope is strictly defined by the spec. The computational constraints (CPU-only, 7GB RAM) are handled by algorithmic choices (Nside=128, N=1000 simulations) rather than architectural complexity. | N/A |

## Phased Implementation Plan

### Phase 1: Data Acquisition & Preprocessing (FR-001, FR-002)
*Goal: Download Planck SMICA map, validate checksum, apply Galactic mask with analytical correction, verify pixel count.*
- **Step 1.1**: Implement `download.py` with retry logic (exponential backoff) to fetch `COM_CMB_ILM-NR1-000_R2.01.fits` (or equivalent SMICA Nside=128) from Planck Legacy Archive.
- **Step 1.2**: Validate file integrity via MD5/SHA checksums against known values.
- **Step 1.3**: Implement `mask.py` to load the U73 (or equivalent) Galactic mask. Apply mask to CMB map.
- **Step 1.4**: Implement **Schmalzing & Gorski (1998)** analytical mask correction for Minkowski Functionals. This uses the mask's own MFs to correct the observed MFs, avoiding ad-hoc buffer heuristics.
- **Step 1.5**: Verify masked map has ≥95% sky coverage and ≥2.5M valid pixels (FR-002).
- **Step 1.6**: Compute basic statistics (mean, std) to ensure physical plausibility.

### Phase 2: Minkowski Functional Computation (FR-003)
*Goal: Compute Area, Perimeter, Genus at thresholds {±0.5σ, ±1σ, 0σ}.*
- **Step 2.1**: Implement `minkowski.py` using `healpy` and `numpy`.
- **Step 2.2**: Apply the analytical mask correction derived in Phase 1.4. Use a minimal pixel buffer only for edge-case verification, not as the primary correction method. Document `mask_buffer_pixels` in output for transparency.
- **Step 2.3**: Compute functionals at specified thresholds.
- **Step 2.4**: Verify numerical precision (≥6 decimal places) and reproducibility (±0.001% tolerance).

### Phase 3: Gaussian Simulation & Null Hypothesis (FR-004, FR-006)
*Goal: Generate Gaussian realizations with beam/noise matching Planck, and alternative hypothesis realizations.*
- **Step 3.1**: Load theoretical LCDM power spectrum (Planck TT, TE, EE) and the **Planck beam transfer function** and **noise covariance maps** from the Planck Legacy Archive (SMICA specific).
- **Step 3.2**: Implement `simulate.py` to generate random spherical harmonic coefficients ($a_{lm}$) consistent with the power spectrum.
- **Step 3.3**: **Critical Correction**: Apply the frequency-dependent Planck beam transfer function and the SMICA noise covariance (not a simplified isotropic Gaussian) to ensure construct validity.
- **Step 3.4**: **Memory Optimization**: Process simulations in batches. Generate -> Compute MF -> Discard Map. Do not hold all maps in memory simultaneously.
- **Step 3.5**: Compute Minkowski Functionals for each simulation.
- **Step 3.6**: **Alternative Hypothesis Generation**: Generate a sufficient number of additional maps with injected cosmic string templates at varying $G\mu$ values spanning a broad range of plausible magnitudes. to build the $L_1$ likelihood distribution. This library is essential for the Likelihood Ratio Test.
- **Step 3.7**: Compute sample covariance matrix of the three functionals across N=1,000 simulations using a **shrinkage estimator (Ledoit-Wolf)** to handle the high dimensionality of the 5-threshold vector.
- **Step 3.8**: Perform PCA on the MF curves to reduce dimensionality (from a high-dimensional space to a small set of principal components) for stable multivariate testing.

### Phase 4: Statistical Inference & Reporting (FR-005, SC-001..SC-004)
*Goal: Perform Likelihood Ratio Test, compute p-values and $G\mu$ bounds.*
- **Step 4.1**: Implement `statistics.py` to perform multivariate Likelihood Ratio Test (LRT) or Hotelling's $T^2$ if $H_1$ is not fully populated. The LRT compares observed MF vector against both $H_0$ (Gaussian) and $H_1$ (String) likelihood distributions.
- **Step 4.2**: Compare observed MF vector (and PCA components) against the Gaussian covariance distribution ($H_0$) and the String Template distribution ($H_1$).
- **Step 4.3**: Fit cosmic string templates to derive $G\mu$ upper bounds if deviations are found.
- **Step 4.4**: Output results to `output/results.json` with ≥6 decimal precision. Include `deviation_found` boolean and `template_fit_parameters`.
- **Step 4.5**: Generate summary plots (Genus curve comparison) for `quickstart.md`.
- **Step 4.6**: Validate runtime and memory usage against GitHub Actions limits (SC-004).

### Phase 5: Validation & Documentation
*Goal: Ensure reproducibility and completeness.*
- **Step 5.1**: Run full pipeline in CI (GitHub Actions) to verify ≤6h runtime.
- **Step 5.2**: Verify all FRs and SCs are addressed in the final artifacts.
- **Step 5.3**: Update `quickstart.md` and `data-model.md`.