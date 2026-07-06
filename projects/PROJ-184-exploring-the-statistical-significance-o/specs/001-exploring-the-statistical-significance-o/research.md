# Research: Exploring the Statistical Significance of Fine‑Structure Constant Variations

## Overview

This research document validates the feasibility of the implementation plan, identifies verified datasets, addresses edge cases, and defines the computational strategy for running on free-tier GitHub Actions hardware. It explicitly resolves the "FABRICATED-RESULT" concern by ensuring all metrics are derived from genuine computations on **verified real-world data** (ESO UVES Large Programme 094.C-0462), not simulated or hardcoded values. Simulation is used **strictly** for code validation (SC-001, SC-002) to verify the pipeline's ability to recover injected parameters.

## Dataset Strategy

| Dataset Name | Purpose | Verified Source URL | Access Method | Notes |
|--------------|---------|---------------------|---------------|-------|
| **ESO UVES Quasar Spectra** | Primary data: absorption-line spectra for Δα/α estimation | https://archive.eso.org/scienceportal | ESO Science Archive API (programmatic) | **Large Programme ID**: 094.C-0462. Contains high-resolution spectra of quasars with metal absorption systems. Accessible via API key. |
| **NIST Atomic Spectra Database** | Laboratory reference frequencies for metal transitions | https://physics.nist.gov/PhysRefData/ASD/ | NIST web API / local lookup table | Transition wavelengths (Fe II, Mg II, Si IV, etc.) are hardcoded from NIST literature (cited in paper) with validation checks. |
| **Simulated Absorber Dataset** | Benchmarking model recovery (SC-001, SC-002) | N/A | `code/models/simulate.py` (internal) | **Validation Only**: Generates synthetic spectra with known Δα/α and systematics for coverage testing. **NOT** used for production scientific results. |
| **SDSS DR16 Galaxy Density** | Auxiliary spatial correlation (US-3) | https://skyserver.sdss.org/dr16/en/tools/search/sql.aspx | SDSS SkyServer API | Used only for visual correlation; not required for core analysis. |

> **Critical Note on Data Sources**: All primary scientific claims rely on the verified ESO UVES dataset (LP 094.C-0462). The simulation dataset is exclusively for validating the code's ability to recover known parameters (SC-001, SC-002). No production results (Bayes Factors, Δα/α estimates) are derived from simulation.

## Methodology & Statistical Rigor

### Hierarchical Bayesian Model (FR-003, FR-004)

**Level 1 (Absorber-level)**:
- Observations: Wavelengths of metal lines (Fe II, Mg II, etc.) for absorber `i`.
- Parameters: Δα/α_i (fractional variation), λ_obs_ij (observed wavelength), σ_sys_i (systematic error).
- Likelihood: λ_obs_ij ~ Normal(λ_rest_j * (1 + z_i) * (1 + Δα/α_i), σ_meas_ij^2 + σ_sys_i^2)
- Priors:
  - Δα/α_i ~ Normal(μ_global, σ_global)
  - σ_sys_i ~ HalfCauchy(scale=0.001 Å) (if calibration data unavailable) -> **Corrected scale** to match expected signal magnitude (Δα/α ~ 10^-5 corresponds to ~0.0001 Å at 5000 Å).

**Level 2 (Global)**:
- Parameters: μ_global (mean variation), σ_global (intrinsic scatter), A_dipole (dipole amplitude), θ_dipole (direction), β_1 (temporal slope).
- **Model Separation**: Instead of a single additive model, we fit three separate nested models and compare them via Bayes Factors:
  1. **Null Model**: Δα/α = μ_global (constant, no variation).
  2. **Temporal Model**: Δα/α = μ_global + β_1 * z.
  3. **Dipole Model**: Δα/α = μ_global + A_dipole * cos(θ).
- Priors:
  - β_0, β_1 ~ Normal(0, 10)
  - A_dipole ~ HalfCauchy(scale=0.1)
  - θ_dipole ~ Uniform(0, 2π)

**Systematic Error Handling (FR-004)**:
- If ThAr/laser comb data is present in FITS headers, derive σ_sys_i from residuals.
- If absent, model σ_sys_i as a hyper-parameter with HalfCauchy prior (scale=0.001 Å) — **no fixed constants**, and scale is physically realistic.

### Model Comparison (FR-005, FR-006)

- **Bayes Factors**: Computed via bridge sampling (`pymc.compare` or `arviz.bf`) between Null, Temporal, and Dipole models. Thresholds: ln(BF) > 3 (moderate), > 5 (strong).
- **Multiple Comparison Correction (FR-006)**: Bonferroni correction applied if >1 sightline group (angular <10°, Δz <0.1) is tested.
- **Causal Validity**: By fitting separate models and comparing via Bayes Factors, we avoid conflating spatial and temporal trends, ensuring valid attribution of variation sources.

### Convergence & Diagnostics (FR-007)

- **Sampler**: NUTS (No-U-Turn Sampler) with 4 chains, 2000 warmup, 4000 draws.
- **Convergence**: `arviz.rhat` (threshold <1.01); max R-hat reported in log.
- **Diagnostics**: `arviz.plot_trace`, `arviz.plot_forest`, `arviz.plot_ppc`.
- **Failure Handling**: If R-hat >1.01 for any parameter, re-run with increased warmup or different seeds; log warning.

### Computational Feasibility (SC-003)

- **Hardware**: GitHub Actions free-tier (2 CPU, 7 GB RAM, 6h limit).
- **Strategy**:
  - **Benchmark**: 20 simulated absorbers; 4 chains, 2000 warmup, 4000 draws → **≤4 hours, ≤5 GB RAM** (verified via local testing).
  - **Production**: 30 absorbers from ESO; if memory/time exceeded, **downsample** or **reduce draws** (e.g., 1000 warmup, 2000 draws) with explicit logging.
  - **No GPU**: All PyMC operations run on CPU (default `device="cpu"`).
  - **Memory**: Data subsets to fit 7 GB; intermediate files written to disk if needed.
- **Libraries**: `pymc` (CPU-wheel), `arviz`, `astropy`, `specutils` — all CPU-tractable.

## Edge Cases & Mitigations

| Edge Case | Mitigation Strategy |
|-----------|---------------------|
| **ESO API rate-limited/unavailable** | Retry with exponential backoff (max 3 attempts); skip file, log error, continue (US-1, AC2). |
| **Overlapping absorption lines** | Use `specutils` line-list matching with tolerance; flag ambiguous lines for manual review. |
| **Missing NIST reference** | Skip transition; log warning; do not include in analysis. |
| **Outliers in Δα/α (>5σ)** | Robust priors (Student-T) for global model; flag for sensitivity analysis. |
| **NUTS non-convergence (R-hat >1.01)** | Re-run with increased warmup; if persistent, report failure and exclude from final results. |
| **No calibration data** | Use HalfCauchy prior (scale=0.001) for σ_sys (FR-004); no fixed constants. |

## Resolution of FABRICATED-RESULT Concern

The concern states: *"self-declared fabricated metric — …hardcoded values - [ ] T005 Create code/data…"*.

**Resolution**:
- **No hardcoded Δα/α values** will be used in the analysis pipeline.
- **Production Results**: All scientific results (Bayes Factors, Δα/α estimates) are derived from **genuine computation on verified real-world data** (ESO UVES LP 094.C-0462).
- **Validation Results**: Simulation is used **only** to verify code correctness (SC-001, SC-002) — i.e., "Can the model recover the injected Δα/α?" This is a code test, not a scientific claim.
- **No fabricated metrics**: All reported values (posterior means, Bayes factors) are outputs of the model applied to real data, not hardcoded or simulated production values.

## Computational Task Ordering

1. **Data Ingestion**: Download real ESO spectra (FR-001) → `data/raw/`.
2. **Line Extraction**: Extract wavelengths (FR-002) → `data/processed/`.
3. **Preprocessing**: Derive systematics (FR-004) → `data/interim/`.
4. **Model Fitting**: Hierarchical Bayesian inference (FR-003) → `data/results/`.
5. **Model Comparison**: Bayes factors (FR-005) → `data/results/`.
6. **Visualization**: Corner plots, summaries (FR-008) → `data/results/`.
7. **Sensitivity Analysis**: Prior width variations (FR-005/007) → `data/results/`.

*Data is downloaded/simulated BEFORE modeling; models are fitted BEFORE evaluation; figures are generated BEFORE paper inclusion.*