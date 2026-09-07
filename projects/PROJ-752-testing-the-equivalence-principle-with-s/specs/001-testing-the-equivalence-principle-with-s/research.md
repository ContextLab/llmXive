# Research: Testing the Equivalence Principle with Satellite Laser Ranging

## Scientific Background

The Weak Equivalence Principle (WEP) states that the trajectory of a test body in a gravitational field depends only on its initial position and velocity, independent of its composition. A violation would manifest as a composition-dependent differential acceleration ($a_c$) between two bodies in the same gravitational field. The Eötvös parameter $\eta = 2|a_1 - a_2| / |a_1 + a_2|$ quantifies this violation.

Satellite Laser Ranging (SLR) provides millimeter-level precision in measuring the distance to geodetic satellites. By analyzing the orbits of satellites with distinct compositions (e.g., LAGEOS-1/2: Aluminum/Titanium vs. Etalon: Steel vs. Starlette: Steel), one can constrain $\eta$ to extremely low levels.

## Dataset Strategy

The project relies on SLR normal-point data. The `# Verified datasets` block below contains the following sources:

1. **SLR (parquet)**: `
 * **Status**: Verified.
 * **Usage**: This dataset contains SLR observations. It will be used as the primary source for normal points if it includes the target satellites (LAGEOS, Etalon, Starlette).
 * **Metadata Check**: The pipeline will verify the presence of `mass` and `composition` columns. If missing, it will merge with `satellite_constants.yaml` (see below).
2. **ILRS Archive (Canonical Fallback)**: `
 * **Status**: Verified (Official Source).
 * **Usage**: If the HF dataset lacks required satellites or metadata, the system will attempt to fetch data from the official ILRS archive. The Reference-Validator Agent MUST verify this URL before ingestion.
 * **Note**: This is the canonical source for LAGEOS-1, LAGEOS-2, Etalon-1, Etalon-2, and Starlette data.

**Critical Gap & Mitigation**:
* **Selection Bias**: If the HF dataset only contains 'clean' subsets, the resulting $\eta$ estimate may underestimate variance.
 * **Mitigation**: The pipeline will compare the distribution of station IDs and epochs in the HF dataset against the full ILRS archive metadata. If deviation >10% is detected, a 'Bias Warning' is issued, and a stratified resampling step is applied.
* **Missing Metadata**: If the HF dataset lacks `mass` or `composition` columns.
 * **Mitigation**: The pipeline will automatically fetch these from `satellite_constants.yaml` (see below) and merge them. If constants are missing there, the satellite is excluded with a "Missing Metadata" flag.

**Physical Constants Source**:
* **Source**: `satellite_constants.yaml` (to be created in `data/`).
* **Citations**: Values for mass, cross-sectional area, and drag coefficients will be sourced from specific ILRS mission documents or peer-reviewed papers (e.g., Coulot et al.; Appleby et al.).

## Methodological Rigor

### Power Analysis
* **Target Precision**: $10^{-14}$ for $\eta$.
* **Required Sample Size**: Based on standard SLR noise models (1-2 mm) and orbital decay rates, a minimum of **[deferred] normal points per satellite** is estimated to achieve sufficient power.
* **Feasibility Check**: The pipeline will verify N >= 10,000 per satellite. If N < 10,000, the run is flagged as "Underpowered" and the 6-hour constraint is re-evaluated.

### Statistical Framework
* **Model**: The differential acceleration $a_c$ is estimated as a parameter in a **joint least-squares fit**.
 * **Correlation Structure**: The joint model includes a shared error term for atmospheric drag and SRP, modeled as a block-diagonal covariance matrix where off-diagonal blocks represent the correlation coefficient ($\rho$) between satellites in similar orbital regimes. $\rho$ is estimated from the residuals of a preliminary fit.
* **Hypothesis Testing**:
 * $H_0$: $a_c = 0$ (WEP holds).
 * $H_1$: $a_c \neq 0$.
* **Multiple Comparisons**: The "family of tests" is defined as the **10 unique pairs** formed by the 5 target satellites (L1-L2, L1-E1, etc.). **Holm-Bonferroni** correction will be applied to control Family-Wise Error Rate (FWER) for this fixed family.
* **Sensitivity Analysis**:
 * **Geopotential Sweep**: Vary geopotential models (GGM05C, EGM2008, GOCO06s).
 * **Systematic Error Sweep**: Vary station bias models and atmospheric drag coefficients (e.g., Jacchia vs. NRLMSISE-00).
 * **Output**: Report Z-score variation across these models. If Z-score varies by >20%, flag as "Unreliable due to model uncertainty".

### Benchmark Retrieval
* **Source**: `benchmarks.yaml` (to be created in `data/`).
* **Content**: State-of-the-art values (e.g., Müller et al., year) with citations.
* **Logic**: The `analysis/eotvos.py` module will load this file and compute the comparison logic, ensuring the `benchmark_comparison` field in the output is populated.

### Simulation Validation
* **Purpose**: To avoid tautological validation.
* **Method**: Generate a simulated dataset with a known injected $\eta$ (e.g., $10^{-13}$) using the same dynamical model.
* **Test**: Run the pipeline on this simulated data. The estimated $\eta$ must match the injected value within 2-sigma. This provides an independent ground truth.

### Consistency Check (Joint vs. Separate)
* **Purpose**: To validate the joint model against the separate-fit baseline (as per amended FR-003).
* **Method**: Compute separate-fit estimates for $a_c$ for each satellite pair. Compare to the joint-fit estimate.
* **Criterion**: The difference must be within 2-sigma of the combined covariance bounds. If not, flag the joint model as potentially biased.

### Definition of 'g'
* **Decoupling**: The denominator 'g' in $\eta = |a_c| / g$ is derived from a **standard geopotential model** (e.g., EGM2008) and **NOT** from the estimated orbital parameters. This avoids circularity where the estimated parameters assume a specific g to calculate the parameter that tests g.

## Compute Feasibility
* **Environment**: GitHub Actions Free Tier (2 CPU, ~7 GB RAM).
* **Strategy**:
 * **Streaming**: Large parquet files will be streamed using `datasets.load_dataset(..., streaming=True)` to avoid loading >7GB into RAM.
 * **Sampling**: If the full dataset exceeds compute limits, a fixed-seed random sample (e.g., first k points) will be used for the initial run, with a note on power limitations.
 * **No GPU Required**: Classical orbit determination does not require CUDA.