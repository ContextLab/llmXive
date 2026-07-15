# Research: Can Publicly Available Data Reveal Subtle Violations of Time-Reversal Symmetry in Beta Decay?

## Executive Summary

This research plan outlines a meta-analysis of published D-coefficients (T-violation correlation parameters) for beta-decaying nuclei, specifically 6He and 19Ne. The primary challenge is the absence of a verified, programmatic API for the NNDC ENSDF database and the lack of a stable programmatic source for PDG D-coefficient limits. Consequently, the research strategy shifts from direct API scraping to a **Static Fallback Primary** approach: using hardcoded, verified values for the target nuclei to guarantee pipeline execution, with an optional "best-effort" scraper for NNDC. The statistical rigor relies on inverse-variance weighting for meta-analysis, with a **Random Effects** fallback for heterogeneity, and a **Sign-Flip Permutation Test** to validate null hypotheses (the only feasible analog to the original constitutional requirement given the aggregated data).

## Dataset Strategy

### Primary Data Source: NNDC ENSDF (D-Coefficients)
The spec requires D-coefficients from the NNDC ENSDF database.
- **Status**: **NO verified programmatic API found** in the "Verified datasets" block.
- **Strategy**: **Static Fallback Primary**.
  - **Method**: The `data_retrieval.py` script will first load a hardcoded, verified dataset of D-coefficients for 6He and 19Ne (derived from the latest PDG/ENSDF reviews). This ensures the pipeline always produces results.
  - **Optional Fetch**: The script will *attempt* to fetch updated data from the NNDC web interface using a targeted scraper with exponential backoff. If successful, these new values are appended to the static dataset with a `source="NNDC_Web"` tag. If failed, the static dataset is used.
  - **Risk Mitigation**: This approach guarantees reproducibility (PR-001) and avoids the "high-risk" fragility of relying solely on a dynamic HTML scraper.

### Secondary Data Source: Particle Data Group (PDG) Constraints
The spec requires validation against PDG review limits.
- **Status**: **NO verified programmatic API found** for specific D-coefficient limits. The previously cited Hugging Face datasets were mismatched (NLP/clustering data).
- **Strategy**: **Static Reference**.
  - **Method**: The `validation.py` module will use hardcoded, verified upper bounds for 6He and 19Ne from the latest PDG Review of Particle Physics (2024/2025 edition).
  - **Rationale**: Parsing PDFs or HTML tables for specific numbers is fragile and non-reproducible. Hardcoding the known values (with a clear comment referencing the specific PDG edition) is the most robust and reproducible strategy for this specific scientific question.

### Data Harmonization
- **Format**: All retrieved data will be normalized to a single CSV schema (`nucleus`, `value`, `uncertainty`, `source`, `reference_id`).
- **Handling Ranges**: If a D-coefficient is reported as a range (e.g., `[-0.05, 0.05]`), the midpoint will be used as the value, and half the range width as the uncertainty, as per Edge Cases.
- **Missing Data**: Nuclei with no data will be excluded from the meta-analysis but logged.

## Statistical Methodology

### 1. Meta-Analysis (FR-002, FR-003)
- **Method**: Inverse-variance weighting (Fixed Effect model).
  - Formula: $D_{combined} = \frac{\sum (D_i / \sigma_i^2)}{\sum (1 / \sigma_i^2)}$
  - Uncertainty: $\sigma_{combined} = \sqrt{1 / \sum (1 / \sigma_i^2)}$
- **Random Effects Fallback**: If Cochran's Q test indicates significant heterogeneity (p < 0.05), the system will switch to the **DerSimonian-Laird Random Effects model** to account for between-study variance ($\tau^2$). This addresses the concern that shared systematic errors might inflate the precision of a Fixed Effect model.
- **Upper Bound**: Calculate the 95% confidence interval upper bound as $D_{combined} + 1.645 \times \sigma_{combined}$ (one-sided).
- **Rigor**: This method assumes independent measurements. The constitution (Principle VI) confirms that treating D-coefficients from different experiments as independent is valid (independence applies to the *measurements*, not the underlying kinematic variables).

### 2. Consistency Testing (FR-004)
- **Method**: Cochran's Q test.
  - Formula: $Q = \sum w_i (D_i - D_{combined})^2$, where $w_i = 1/\sigma_i^2$.
  - Distribution: Chi-square with $k-1$ degrees of freedom.
  - Threshold: $p > 0.05$ indicates consistency (SC-002).
- **Edge Case Handling**: If $p=0$ or $p=1$ due to floating-point precision, values are clamped to $[10^{-10}, 1-10^{-10}]$.

### 3. Sensitivity Limit (FR-005)
- **Definition**: The standard error of the weighted mean ($\sigma_{combined}$).
- **Verification**: Compared against the theoretical minimum uncertainty achievable (SC-003).

### 4. Null-Hypothesis Rigor (Constitution Principle VII - Modified)
- **Constraint**: The original requirement ("shuffling polarization values to momentum bins") is **impossible** because the input data consists solely of pre-calculated D-coefficients (D_i) and their uncertainties (sigma_i). There are no raw momentum/polarization pairs to shuffle.
- **Method**: **Sign-Flip Permutation Test**.
  - **Procedure**: Randomly flip the signs of the D-coefficients (multiply by -1) 10,000 times. For each permutation, recalculate the weighted mean.
  - **Goal**: Generate a null distribution for the *meta-analytic average* under the hypothesis that the true D-coefficient is zero.
  - **Validation**: The observed weighted mean is compared against the 95th percentile of the null distribution. If the observed mean falls within the null distribution, the result is not statistically significant.
 - **Feasibility**: [deferred] sign-flips on a small dataset (N < 100) is computationally trivial on CPU (< 1 minute).
  - **Rationale**: This is the standard randomization test for meta-analysis when raw data is unavailable. It satisfies the *intent* of the constitutional requirement (testing D=0 against a null distribution) without requiring non-existent raw data.

## Decision/Rationale: CPU vs. GPU
- **Decision**: **CPU-only execution**.
- **Rationale**: The statistical operations (weighted average, chi-square, sign-flip permutation) are lightweight matrix/vector operations. No transformer models or heavy numerical simulations requiring CUDA are involved. The entire pipeline fits comfortably within the CPU and RAM constraints of the GitHub Actions free tier.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| NNDC API Unreachable | High (Data Gap) | **Static Fallback Primary**: The pipeline uses hardcoded verified data as the primary source. The scraper is optional. |
| HTML Structure Change | High (Parsing Error) | **Static Fallback**: The scraper is non-blocking. If it fails, the static data is used. |
| Single Measurement for a Nucleus | Medium (No Consistency Test) | Skip Cochran's Q for that nucleus; report single measurement result directly (Edge Case). |
| Range Data | Medium (Uncertainty Propagation) | Use midpoint and half-width as per spec Edge Cases. |
| Heterogeneity in Data | Medium (Invalid Fixed Effect) | **Random Effects Fallback**: Switch to DerSimonian-Laird model if Cochran's Q indicates heterogeneity. |

## References
- **PDG Data**: Static reference (hardcoded values from 2024/2025 Review of Particle Physics).
- **NNDC ENSDF**: Public web interface (no verified API URL).
- **Statistical Methods**: Standard meta-analysis, Cochran's Q, and Sign-Flip permutation tests (Cochran, 1954; standard meta-analysis literature).