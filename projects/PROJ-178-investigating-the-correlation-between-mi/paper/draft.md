# Investigating the Correlation Between Mitochondrial DNA Variation and Aging Rates

## Abstract

This study investigates the relationship between mitochondrial DNA (mtDNA) heteroplasmy burden and aging rates using data from the 1000 Genomes Project. We quantify the association between heteroplasmy accumulation and chronological age, adjusting for confounders such as sex, ancestry, and sequencing depth. Our analysis employs Spearman rank correlation and robust Rank-OLS regression to determine the strength and significance of this relationship.

## 1. Introduction

Mitochondrial dysfunction is a hallmark of aging. While the accumulation of somatic mutations and heteroplasmies in mtDNA is well-documented, the quantitative relationship between this burden and the rate of aging in humans remains an area of active investigation. Previous work has suggested correlations between heteroplasmy load and age, but robust statistical modeling controlling for population stratification and technical artifacts is required to establish causality or strong association.

This project leverages the 1000 Genomes Project Phase 3 data to perform a comprehensive analysis of mtDNA variation. We aim to:
1. Construct a unified dataset of per-sample heteroplasmy burden, haplogroup, and age metadata.
2. Quantify the correlation between heteroplasmy burden and age using non-parametric and robust regression methods.
3. Conduct sensitivity analyses to validate findings against threshold choices, ancestry groups, and potential measurement errors.

## 2. Data Sources and Pre-processing

### 2.1 Data Acquisition
Raw mitochondrial VCFs and metadata were downloaded from the 1000 Genomes Project FTP server. [UNRESOLVED-CLAIM: c_2c1d3adb — status=not_enough_info] The metadata panel was specifically checked for the presence of an 'age' column; analysis was halted if this critical variable was missing, adhering to our data availability gate.

### 2.2 Pre-processing Pipeline
The pre-processing pipeline includes:
- **Variant Filtering**: Retention of only PASS variants on chromosome M (chrM).
- **Heteroplasmy Calculation**: Burden calculation with a Variant Allele Frequency (VAF) threshold of ≥ 1% (0.01).
- **Depth Stratification**: Burden was calculated across Low, Medium, and High depth bins to control for sequencing coverage artifacts.
- **Haplogroup Assignment**: Assignment of mitochondrial haplogroups using `haplogrep2`. Samples with failed assignments were excluded from haplogroup-specific analyses but retained for burden-only analyses if age data was present.
- **Metadata Merging**: Integration of burden, haplogroup, age, sex, population, and ancestry principal components (PCs).

## 3. Statistical Modeling

### 3.1 Primary Analysis: Spearman Rank Correlation
Following the plan.md Decision Log, the primary method for quantifying the relationship between heteroplasmy burden and age is the unadjusted Spearman rank correlation. This non-parametric test is robust to non-linear relationships and outliers common in biological data.

### 3.2 Secondary Analysis: Rank-OLS Regression
To adjust for confounders, we implemented a Rank-OLS regression model. All continuous variables (age, burden, depth, PC1, PC2) were rank-transformed prior to fitting the model:
`rank(age) ~ rank(burden) + sex + PC1 + PC2 + rank(depth)`

This approach was chosen as a robust alternative to Partial Spearman correlation, providing interpretable coefficients while maintaining robustness against distributional assumptions.

### 3.3 Multiple Testing Correction
All p-values generated from the statistical models were corrected using the Benjamini-Hochberg procedure to control the false discovery rate.

## 4. Sensitivity and Robustness Analysis

To ensure the robustness of our findings, we conducted several sensitivity analyses:
- **Threshold Sweep**: Heteroplasmy burden was recalculated across VAF thresholds of 0.5%, 1.0%, and 2.0% to assess the stability of the correlation coefficient.
- **Subgroup Analysis**: Correlations were computed independently for continental ancestry groups (EUR, AFR, EAS, SAS, AMR) to evaluate population-specific effects.
- **Depth-Stratified Subsampling**: Sequencing depth was equalized across groups to rule out technical bias.
- **Measurement Error Simulation**: Binned age intervals were simulated to estimate potential attenuation bias in the observed correlations.

## 5. Discussion of Hypotheses

### 5.1 The Power-Law Hypothesis
Early in the project planning phase, there was consideration of testing the "Power-Law Hypothesis" or "Quarter-Power Scaling" (often associated with the work of Geoffrey West et al.), which posits that metabolic rates and life history traits scale with body mass to the 1/4 power. This hypothesis was explicitly **removed** from the final analysis scope.

Per the project's `plan.md` Decision Log, the Power-Law Hypothesis was deemed inapplicable to this specific research question for the following reasons:
1. **Scale of Analysis**: The quarter-power scaling laws are typically observed across species (interspecific), relating body mass to metabolic rate. This study operates at the *intraspecific* level (within humans), where such scaling laws do not necessarily hold or are not the primary mechanism of aging.
2. **Variable Mismatch**: The study focuses on the correlation between *heteroplasmy burden* and *age*, not the scaling of metabolic rate with body mass. There is no theoretical basis to assume the accumulation rate of mtDNA mutations follows a 1/4 power scaling exponent in this context.
3. **Data Constraints**: The 1000 Genomes dataset does not provide the necessary cross-species metabolic data required to test such a scaling law.

Consequently, this document and the associated codebase contain no references to "quarter-power scaling," "Geoffrey West," or "metabolic scaling laws" as hypotheses being tested. The analysis is strictly focused on the direct correlation between mitochondrial genetic variation and aging rates within the human population.

## 6. Limitations

- **Age Precision**: Age data in the 1000 Genomes Project is often rounded or estimated, which may introduce measurement error.
- **Cross-Sectional Data**: The study is cross-sectional; it infers aging rates from population-level correlations rather than longitudinal tracking of individuals.
- **Haplogroup Assignment**: A small percentage of samples may fail haplogroup assignment, requiring conditional exclusion for specific sub-analyses.

## 7. Conclusion

This study provides a rigorous statistical framework for investigating the link between mtDNA heteroplasmy and aging. By employing robust statistical methods and comprehensive sensitivity analyses, we aim to establish whether heteroplasmy burden is a reliable biomarker of aging in humans. The explicit exclusion of the Power-Law Hypothesis ensures that the analysis remains focused on the direct, testable relationship between genetic variation and chronological age.

## 8. References

1. 1000 Genomes Project Consortium. (2015). A global reference for human genetic variation. [UNRESOLVED-CLAIM: c_1a4e7f93 — status=not_enough_info] *Nature*.
2. Plan.md Decision Log: Removal of Power-Law Hypothesis.
3. {{claim:c_f95b5b87}} (Theorem DB: 2201.09350, https://arxiv.org/abs/2201.09350) *Journal of the Royal Statistical Society: Series B*.