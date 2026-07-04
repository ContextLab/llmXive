# Implementation Plan: Testing Lorentz Violation with Publicly Available CMB Data

**Branch**: `001-testing-lorentz-violation` | **Date**: 2026-06-26 | **Spec**: `specs/001-testing-lorentz-violation/spec.md`
**Input**: Feature specification from `specs/001-testing-lorentz-violation/spec.md`

## Summary

This project implements a statistical pipeline to test for Lorentz invariance violations in the Cosmic Microwave Background (CMB) using Planck 2018 PR3 data. The approach involves downloading SMICA temperature and polarization maps from the ESA Legacy Archive (FITS format), applying masks, computing angular power spectra, and performing Bipolar Spherical Harmonic (BipoSH) and dipole modulation analyses. The core statistical engine compares an isotropic ΛCDM model against an anisotropic model using likelihood-ratio tests and MCMC sampling to constrain the SME coefficient \(k_{(V)}^{(5)}\). All analysis is constrained to run on CPU-only GitHub Actions runners by utilizing `healpy` for map operations and `emcee` for efficient MCMC sampling. The BipoSH analysis is restricted to low multipoles (\(\ell < 200\)) where the LIV signal is theoretically expected to dominate, ensuring signal-to-noise ratio is preserved while fitting memory limits.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `healpy`, `numpy`, `scipy`, `emcee`, `requests`, `astropy`, `pyyaml`  
**Storage**: Local file system (raw maps, masks, processed products, simulation outputs)  
**Testing**: `pytest` (unit tests for data integrity, integration tests for pipeline stages)  
**Target Platform**: Linux (ubuntu-latest GitHub Actions runner)  
**Project Type**: Scientific analysis pipeline / CLI  
**Performance Goals**: Complete end-to-end analysis within 6 hours; peak RAM < 7 GB.  
**Constraints**: No GPU; no deep learning; no external API calls during execution (except initial data fetch); strict adherence to Planck data formats.  
**Scale/Scope**: Processing Nside=2048 maps (restricted to \(\ell < 200\) for BipoSH); generating multiple Monte Carlo simulations; MCMC chain length ≤ 10,000.  
**Config**: `config.yaml` (loaded via `pyyaml`) for paths, seeds, and constants.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: The plan mandates pinning all random seeds in `config.yaml` and fetching data from the specific ESA sources defined in `research.md`. `requirements.txt` will enforce dependency versions.
- **II. Verified Accuracy**: The implementation will integrate the **Reference-Validator Agent** gate. All citations in `research.md` will be restricted to sources verified by this agent, checking for title-token-overlap ≥ 0.7 before acceptance.
- **III. Data Hygiene**: The pipeline will implement checksum verification for all downloaded artifacts. Raw data will be stored read-only in `data/raw/`; processed data will be written to `data/processed/` with new filenames.
- **IV. Single Source of Truth**: All figures and statistics in the final output will be generated programmatically from `data/processed/` and `code/`. No hand-typed values.
- **V. Versioning Discipline**: Content hashes for `data/` files will be recorded in the specific file `state/projects/PROJ-201-testing-lorentz-violation-with-publicly-.yaml` as required by the Constitution's 'Data Hygiene' section. The `code/` directory will be versioned via git.
- **VI. Statistical Anisotropy Validation**: The plan includes a specific phase for generating null-hypothesis simulations (isotropic ΛCDM with realistic noise/beam) to cross-validate any detected anisotropy, ensuring instrumental artifacts are distinguished from physical signals.
- **VII. Significance Threshold Governance**: The analysis will apply multiple-comparison corrections (Benjamini-Hochberg FDR) as required by FR-007 and report results against the standard statistical significance threshold, with explicit warnings for look-elsewhere effects.

## Project Structure

### Documentation (this feature)

```text
specs/001-testing-lorentz-violation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Loads config.yaml, seeds, constants
├── data/
│   ├── __init__.py
│   ├── downloader.py    # Fetch Planck data (FITS), verify checksums
│   ├── processor.py     # Masking, beam deconvolution
│   └── simulation.py    # Generate isotropic/anisotropic simulations
├── analysis/
│   ├── __init__.py
│   ├── power_spectra.py # Compute TT, EE, TE spectra (ℓ < 200)
│   ├── anisotropy.py    # Dipole modulation, BipoSH (L=2,3)
│   ├── minkowski.py     # Minkowski functional check
│   └── inference.py     # MCMC, likelihood ratio
├── utils/
│   ├── __init__.py
│   └── logging.py
├── main.py              # Entry point
└── requirements.txt

tests/
├── __init__.py
├── test_data.py         # Integrity checks
├── test_analysis.py     # Unit tests for estimators
└── test_inference.py    # MCMC convergence tests

data/
├── raw/                 # Downloaded maps (checksummed)
├── processed/           # Masked/deconvolved maps
├── simulations/         # Null distribution samples
└── results/             # Final metrics and constraints
```

**Structure Decision**: Single project structure selected. This aligns with the scientific pipeline nature of the project, keeping data ingestion, processing, and analysis tightly coupled within the `code/` directory. The separation of `data/raw` and `data/processed` ensures data hygiene (Principle III).

## Implementation Phases

### Phase 0: Data Acquisition & Verification (FR-001)
*   **Task 0.1**: Implement `downloader.py` to fetch SMICA, EE, TE maps and masks from the **ESA Legacy Archive** (FITS format).
    *   *Validation*: Verify checksums match ESA records.
    *   *Risk*: If ESA archive is unreachable, the pipeline halts with `ERROR_DATA_UNAVAILABLE`.
*   **Task 0.2**: Verify file integrity (no NaNs, correct Nside=2048).

### Phase 1: Data Processing & Forward Model Definition (FR-002, FR-008)
*   **Task 1.1**: Implement `processor.py` to apply confidence masks and deconvolve beam/pixel window functions.
*   **Task 1.2**: Define the **Forward Model**:
    *   *Algorithm*: To inject \(k_{(V)00}^{(5)}\), the code will modify the spherical harmonic coefficients \(a_{\ell m}\) of an isotropic map:
        \[ a_{\ell m}^{new} = a_{\ell m}^{iso} + k_{(V)00}^{(5)} \cdot \alpha_{\ell m}^{LM} \]
        where \(\alpha\) is the geometric factor derived from SME theory for L=2,3.
*   **Task 1.3**: Implement `simulation.py` to generate **200** anisotropic simulations by injecting specific \(k\) values using the forward model defined in Task 1.2.
    *   *Constraint*: Simulations must be convolved with Planck beam/pixel functions and include realistic noise power spectra to match the null distribution requirements.

### Phase 2: Anisotropy Diagnostics (FR-003, FR-004, Edge Cases)
*   **Task 2.1**: Compute Angular Power Spectra (TT, EE, TE) for \(\ell < 200\) using `healpy.anafast`.
*   **Task 2.2**: Compute **Dipole Modulation** (Hanson & Lewis estimator) as a preliminary screen.
*   **Task 2.3**: Compute **BipoSH Coefficients** specifically for **L=2 (Quadrupole)** and **L=3 (Octupole)** modes to constrain \(k_{(V)00}^{(5)}\).
    *   *Justification*: Theoretical predictions indicate the LIV signal for this coefficient is dominated by low-ℓ modes. Restricting to \(\ell < 200\) preserves signal-to-noise and fits memory limits.
*   **Task 2.4**: **Non-Gaussianity Check** (Edge Case): Implement Minkowski functionals (V0, V1, V2) on masked maps to flag potential false positives from instrumental artifacts.

### Phase 3: Model Comparison & Inference (FR-005, FR-006, FR-007)
*   **Task 3.1**: Construct Likelihood Function:
    *   Compare observed BipoSH coefficients \(A_{obs}\) against the distribution of \(A_{sim}\) generated by the forward model for various \(k\) values.
    *   Likelihood: \( \mathcal{L}(k) \propto \exp(-\frac{1}{2} (A_{obs} - \alpha \cdot k)^T \Sigma^{-1} (A_{obs} - \alpha \cdot k)) \).
*   **Task 3.2**: Run **MCMC Sampling** (≤ 10,000 samples) to derive posterior for \(k_{(V)00}^{(5)}\).
    *   *Constraint*: Monitor ESS; if < 200, issue warning.
*   **Task 3.3**: **Apply Multiple Comparison Correction**:
    *   Implement Benjamini-Hochberg FDR on the set of p-values from BipoSH modes (L=2,3; various M).
    *   Report corrected p-values and classify result as "consistent with isotropy" or "anomalous".

## Complexity Tracking

No violations of the Constitution detected. The complexity is managed by:
1.  **Low-ℓ Restriction**: Restricting BipoSH analysis to \(\ell < 200\) ensures memory fit (Nside=2048 maps are processed, but analysis is low-resolution) and preserves signal-to-noise for the specific LIV signal.
2.  **CPU-tractable methods**: Using `emcee` and `healpy` avoids heavy GPU dependencies.
3.  **Modular design**: Separation of data, analysis, and inference allows independent testing and debugging.
4.  **Simulation Count**: Reduced to a smaller scale to fit 7 GB RAM while maintaining statistical validity for low-ℓ anomaly detection.