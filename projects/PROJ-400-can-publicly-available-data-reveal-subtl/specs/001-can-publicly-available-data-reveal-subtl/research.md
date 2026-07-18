# Research: Can Publicly Available Data Reveal Subtle Violations of Time-Reversal Symmetry in Beta Decay?

## Executive Summary

This research investigates whether archival data from the NNDC ENSDF database and primary literature contains sufficient published D-coefficients to perform a **Meta-Analysis** for detecting Time-Reversal (T) symmetry violations. The study focuses on nuclei such as 6He and 19Ne. The core hypothesis is that by aggregating independent published D-coefficient measurements via inverse-variance weighting, we can derive a more precise constraint on T-violation than individual experiments. The original proposed "cross-modal covariance" method was found to be physically invalid (requires simultaneous event-level data not available in archival summaries) and has been replaced by this Meta-Analysis approach.

## Dataset Strategy

### Target Nuclei
- **Primary**: 6He, 19Ne (as specified in FR-001, but pivoted to D-coefficient retrieval).
- **Selection Criteria**: Nuclei must have published measurements of the **D-coefficient** (or A, B, a coefficients from which D can be derived if the paper provides the formula).

### Data Sources & Feasibility

**Source**: NNDC ENSDF (Evaluated Nuclear Structure Data File) and Primary Literature.
- **Access Method**: The system will query the NNDC ENSDF database via its public web interface or API to retrieve evaluated D-coefficient values. If ENSDF lacks a D-coefficient, the system will search for the primary literature (via the 'Verified Accuracy' gate) to find the specific experiment's reported D-value.
- **Feasibility Check**: 
  - **Constraint**: The system must validate for the presence of *D-coefficient values* and their uncertainties. If a study only reports A, B, or a coefficients without a derived D, and does not provide the formula to derive D, the study is excluded.
  - **Risk**: Many historical beta decay measurements in ENSDF report A, B, or a coefficients but not D.
  - **Mitigation**: The `fetch_ensdf.py` script will include a validation step to parse the metadata of each entry. If the D-coefficient is missing and not derivable, the entry is excluded, and a "D-value missing" flag is logged.
  - **CRITICAL DATA LIMITATION**: ENSDF typically does **not** contain the raw event-level momentum spectra or polarization asymmetry coefficients required for the spec's "cross-modal covariance" method. The spec's requirement for such data (FR-001, US-1) is a **fatal feasibility flaw**. This plan proceeds with the only viable path: meta-analysis of *published D-coefficients*. The spec MUST be updated to reflect this.

**Note on Verified Datasets**: The provided "Verified datasets" block contains no nuclear physics datasets. This project relies entirely on the **NNDC ENSDF** public interface and primary literature as the primary source. No external HuggingFace/UCI dataset substitutes exist for this specific physics query. The plan assumes NNDC is accessible via public HTTP(S) requests.

### Data Availability & Streaming
- **Size**: ENSDF entries are typically small (text/CSV/XML tables). Streaming is not strictly necessary for the raw data itself, but the system will process datasets sequentially to stay within memory limits.
- **Download Strategy**: `requests` library with exponential backoff (3 retries) to handle temporary NNDC unavailability (Edge Case 1).
- **Format**: Data will be normalized to a standard internal JSON/Parquet format (`DMeasurement`) before analysis.

## Methodology

### 1. Data Retrieval & Validation (FR-001 Revised, FR-004)
- **Step**: Query NNDC for 6He and 19Ne.
- **Filter**: Extract only entries containing published D-coefficients (or derivable D-values).
- **Validation**: Check if the D-coefficient is reported or derivable.
  - *If D-value missing and not derivable*: Flag as "D-value missing", exclude from analysis.
  - *If D-value present*: Proceed to harmonization.
- **Note**: The spec's requirement for "raw momentum spectra" is physically impossible to fulfill from ENSDF for this method. The plan uses available D-values.

### 2. Meta-Analysis of D-Coefficients (FR-002 Revised)
- **Input**: Harmonized `DMeasurement` objects for each nucleus.
- **Assumption**: Each published D-coefficient is an independent measurement with a reported uncertainty.
- **Operation**: Compute the **inverse-variance weighted mean** of the D-coefficients.
- **Derivation**: The meta-analytic mean represents the best estimate of the D-coefficient for the nucleus.
- **Statistical Rigor**: 
  - **Heterogeneity**: Use Cochran's Q test to check for consistency among measurements.
  - **Model Selection**: If heterogeneity is significant, use a Random Effects model; otherwise, use a Fixed Effect model.

### 3. Permutation Testing (FR-003, SC-002, SC-004)
- **Null Hypothesis**: $H_0$: The true weighted mean D-coefficient is zero (consistent with T-symmetry).
- **Procedure**: 
  1. Calculate the observed weighted mean.
  2. Randomly **flip the signs** of the D-coefficients (or resample with replacement) for a large number of iterations to build a null distribution.
  3. Calculate p-value: proportion of null means $\ge$ observed mean (one-sided) or $|null| \ge |observed|$ (two-sided).
- **Stability Check**: Verify p-value variance < 0.01 by doubling shuffles (SC-004).
- **Clamping**: Clamp p-values to $[10^{-10}, 1-10^{-10}]$ to handle floating-point precision (Edge Case 3).
- **Note**: The spec's requirement to shuffle "Momentum" and "Polarization" from separate experiments is physically meaningless. This plan applies permutation to the *aggregated D-coefficients*.

### 4. Sensitivity & Validation (FR-005, FR-006, SC-001, SC-003)
- **Sensitivity Limit**: Calculate as the standard error (SE) of the weighted mean of measurements for the specific nucleus.
- **PDG Comparison**: Cross-reference derived upper bounds ($|D| < X$) with the Particle Data Group (PDG) Review limits.
- **Flagging**: If the derived bound is looser (larger) than the PDG limit, flag the result as "less sensitive than current world average" (US-3).

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: Since the analysis is performed per nucleus (6He, 19Ne), the family-wise error rate is controlled by the permutation test per nucleus. No global correction is needed unless multiple nuclei are combined in a meta-analysis (not in scope).
- **Sample Size/Power**: The "sample size" is the number of published D-coefficients. Power is limited by the number of available experiments. If only a few measurements exist, the meta-analysis may lack power; this limitation will be explicitly reported.
- **Causal Inference**: This is an observational analysis of archival data. Claims are strictly **associational** regarding the existence of a correlation; the T-violation interpretation relies on the Standard Model assumption that $D_{SM} \approx 0$.
- **Measurement Validity**: The method assumes the uncertainties reported in the primary literature are accurate and that the "D-coefficient" values are not synthetic reconstructions.

## Decision/Rationale: Compute Feasibility

- **CPU-First**: The statistical operations (weighted mean, permutation) are computationally light. [deferred] shuffles on a dataset of a small number of points will run in seconds/minutes on a -core CPU.
- **No GPU Required**: No deep learning or large matrix decompositions requiring CUDA are planned.
- **Memory**: Data is small (text/CSV). No streaming of large files is required, but the code will be written to handle data sequentially to respect the GB RAM limit.

## Risks & Mitigations

| Risk | Mitigation |
| :--- | :--- |
| **Data Unavailable**: NNDC returns 404 or no D-coefficients. | System flags "D-value missing" and excludes the nucleus. Report explicitly. |
| **No D-Values**: All entries report only A, B, a coefficients. | The study concludes "Archival data insufficient for meta-analysis" for that nucleus. |
| **Network Failure**: NNDC API timeout. | Exponential backoff (3 retries) then log failure and proceed with available data. |
| **Floating Point Issues**: p-value = 0 or 1. | Clamp to $[10^{-10}, 1-10^{-10}]$. |
| **Single Measurement**: Only one experiment for a nucleus. | Skip permutation consistency check; report single measurement with uncertainty. |
| **Spec Contradiction**: Spec mandates invalid "cross-modal covariance". | Plan explicitly documents this as a blocking flaw and proceeds with Meta-Analysis. Requires spec kickback. |