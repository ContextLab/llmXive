# Research: Investigating the Correlation Between Mitochondrial DNA Variation and Aging Rates

## Problem Statement

The primary research question is: **Is there a statistically significant correlation between mitochondrial heteroplasmy burden and chronological age in human populations?**

This study aims to quantify this association using publicly available data. **CRITICAL DATA MISMATCH**: The primary candidate dataset, the 1000 Genomes Project Phase 3, is a population genetics resource. Its sample metadata contains population labels and sex, but **does NOT contain individual chronological ages**. Age is either missing, binned (e.g., "adult"), or imputed with high uncertainty. Using this dataset for an age-correlation study is scientifically unsound without a verified age source.

**Revised Strategy**: The project will first perform a "Data Availability Gate" check. If a verified `age` column is not found, the project will halt the correlation analysis and re-scope to a descriptive analysis of heteroplasmy burden distribution, or flag the hypothesis as "Data Unavailable". If age data is found (e.g., via a specific subset or external verified source), the analysis proceeds with robust methods.

## Dataset Strategy

### Verified Datasets
- **VCFs**: The plan assumes access to the public 1000 Genomes FTP site (ftp://ftp.1000genomes.ebi.ac.uk/vol1/ftp/phase3/). **NO verified source found** for a dataset containing both mtDNA VCFs and precise chronological ages.
- **Age Metadata**: **NO verified source found**. The `age` column is expected to be present in the 1000 Genomes phase3.integrated_call_samplesv3.sample_metadata file, but its availability and accuracy are uncertain.

### Dataset Limitations & Mitigation
1.  **Missing Age Data (Critical)**: The 1000 Genomes Project is not an aging study.
    -   *Mitigation*: **Hard Halt**: The pipeline will check for the `age` column. If missing, it will terminate with a clear error message: "Data Unavailable: Chronological age not found in source metadata." The project will not proceed with correlation analysis.
    -   *Bias Check*: If age is present but missing for some samples, a logistic regression will test if missingness correlates with ancestry or sequencing depth (MNAR check).
2.  **VCF Accessibility**: Large files require streaming.
    -   *Mitigation*: Stream VCFs using `vcfpy` and an in-memory `defaultdict(int)` accumulator to calculate burden without loading the entire file into RAM.
3.  **Measurement Error (Binning)**: If age is binned (e.g., 10-year ranges), the correlation will be attenuated (regression dilution bias).
    -   *Mitigation*: Perform a simulation to estimate the attenuation factor. Power calculations will be based on the attenuated effect size, not an optimistic r=0.1.

### Data Variables
| Variable | Description | Source | Type |
|----------|-------------|--------|------|
| `sample_id` | Unique sample identifier | 1000 Genomes | String |
| `age` | Chronological age (years) | 1000 Genomes metadata (if available) | Integer/Float |
| `sex` | Biological sex (M/F) | 1000 Genomes metadata | Categorical |
| `population` | Continental ancestry group | 1000 Genomes metadata | Categorical |
| `haplogroup` | Mitochondrial haplogroup | `haplogrep2` | Categorical |
| `heteroplasmy_burden` | Count of mtDNA variants with VAF ≥ 1% | Derived from VCF | Integer |
| `sequencing_depth` | Average coverage depth | VCF metadata | Float |
| `pc1`, `pc2` | Principal components for ancestry | 1000 Genomes metadata | Float |

## Statistical Methodology

### Primary Analysis
-   **Method**: **Rank-OLS Regression**.
    1.  Rank-transform all continuous variables (`age`, `burden`, `depth`, `PC1`, `PC2`) to handle non-normality.
    2.  Fit OLS: `rank(age) ~ rank(burden) + sex + PC1 + PC2 + rank(depth)`.
    3.  Extract coefficient and p-value for `rank(burden)`.
-   **Rationale**: Standard Spearman correlation is bivariate and cannot adjust for covariates. Rank-OLS preserves the robustness of rank-based methods while allowing multivariate adjustment, addressing the methodological gap identified by reviewers.
-   **Unadjusted Check**: Spearman correlation between `heteroplasmy_burden` and `age` (without covariates) will be reported for comparison only.

### Multiple Testing Correction
-   **Method**: Benjamini-Hochberg (BH) procedure.
-   **Scope**: Applied to all p-values generated in the primary analysis, sensitivity thresholds, and subgroup analyses.

### Power Analysis
- **Assumption**: N [deferred] (if age is available).
-   **Attenuation**: If age is binned, the observed effect size will be smaller. Power will be calculated based on the *attenuated* effect size (r_attenuated).
-   **Limitation**: If the effective sample size drops significantly due to missing age, the study may be underpowered.

### Causal Inference
-   **Observational Nature**: The data is observational.
-   **Framing**: Findings will be framed as **associational** only. No causal claims.

### Robustness & Sensitivity Analysis
1.  **Threshold Sensitivity**: Recalculate burden and re-run Rank-OLS for thresholds **0.5%, 1.0%, 2.0%**.
2.  **Subgroup Analysis**: Repeat analysis within **EUR, AFR, EAS, SAS, AMR**.
3.  **Depth Stratification**: Calculate burden separately for low/medium/high depth bins to control for technical artifacts.
4.  **Measurement Error Simulation**: Simulate binned age data to estimate attenuation bias.

## Reviewer Feedback Integration

**Reviewer: geoffrey-west-simulated**  
*Comment*: "We need to look for the exponent, not just the p-value... quarter-power scaling."

*Response*: The reviewer's insight regarding quarter-power scaling is theoretically profound for *interspecific* metabolic rate (Kleiber's law). However, applying an interspecific allometric scaling exponent to an *intraspecific* aging trajectory is a category error and theoretically invalid. The plan will **not** attempt to fit a power-law model (heteroplasmy_burden ~ age^β) to test for quarter-power scaling. Instead, the focus will remain on the linear (rank-based) association between burden and age, if data permits.

## Decision Log

| Decision | Rationale |
|----------|-----------|
| Use Rank-OLS instead of Partial Spearman | Allows multivariate adjustment while preserving rank robustness. |
| Hard Halt on Missing Age | Prevents scientifically invalid analysis; 1000 Genomes lacks precise age data. |
| Remove Power-Law Hypothesis | Interspecific scaling laws do not apply to intraspecific aging trajectories. |
| Depth-Stratified Burden | Controls for non-linear relationship between depth and variant detection. |
| BH Correction on All P-values | Ensures FDR control across all tests. |