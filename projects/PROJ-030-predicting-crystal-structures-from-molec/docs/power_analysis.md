# Power Analysis Documentation

## Overview
This document outlines the power analysis assumptions, calculations, and target sample sizes for the "Predicting Crystal Structures from Molecular Fingerprints" project (PROJ-030). The analysis was performed to determine the minimum number of scaffolds required to achieve statistically significant results for the classification task of predicting space groups from molecular fingerprints.

## Objectives
The primary objective of this power analysis is to:
1. Determine the minimum sample size required to detect a meaningful effect size in the classification of crystal structures.
2. Ensure the study has sufficient statistical power to reject the null hypothesis when it is false.
3. Provide a target sample size for the data ingestion and modeling phases of the project.

## Statistical Parameters

### Effect Size (Cohen's w)
- **Assumed Effect Size**: Cohen's w = 0.15
- **Justification**: This represents a small-to-medium effect size. In the context of crystal structure prediction, a small effect is expected due to the high dimensionality of molecular fingerprints and the complexity of the relationship between molecular structure and crystal packing. A value of 0.15 is a conservative estimate that ensures the study is powered to detect even subtle but meaningful patterns.
- **Reference**: Cohen, J. (1988). *Statistical Power Analysis for the Behavioral Sciences* (2nd ed.). Lawrence Erlbaum Associates.

### Significance Level (Alpha)
- **Alpha (α)**: 0.05
- **Justification**: This is the standard threshold for statistical significance in scientific research. It represents a 5% risk of concluding that a difference exists when there is no actual difference (Type I error).

### Statistical Power (1 - Beta)
- **Power**: 0.80 (Beta = 0.20)
- **Justification**: A power of 80% means there is an 80% chance of correctly rejecting the null hypothesis when the alternative hypothesis is true. This is the conventional standard for ensuring that a study is sufficiently powered to detect the assumed effect size.

### Test Type
- **Test**: Chi-square goodness-of-fit test (or equivalent multinomial test for space group distribution)
- **Degrees of Freedom**: Based on the number of space groups being predicted (typically 230, but grouped for practical modeling). For the purpose of sample size calculation, we assume a reduced set of common space groups or a grouped category structure.

## Calculation Methodology
The sample size was calculated using the standard formula for power analysis in chi-square tests:

$$N = \frac{\lambda}{w^2}$$

Where:
- $N$ = Total sample size
- $\lambda$ = Non-centrality parameter (determined by desired power and alpha)
- $w$ = Cohen's effect size

For a power of 0.80 and alpha of 0.05, the non-centrality parameter $\lambda$ is approximately 10.9 for a typical distribution of degrees of freedom in this context.

Substituting the values:
$$N = \frac{10.9}{0.15^2} = \frac{10.9}{0.0225} \approx 484.44$$

Rounding up to ensure sufficient power, we target **500 scaffolds**.

## Target Sample Size
- **Target Number of Scaffolds**: 500
- **Rationale**: This number ensures that the model training and validation phases have enough data to:
 - Train robust machine learning models (Random Forest, Gradient Boosting, Ridge Regression).
 - Perform scaffold-based splitting with zero overlap between training and test sets.
 - Achieve statistically significant results in evaluating model performance against baselines.
 - Handle the grouping of rare space groups into an 'Other' category without losing too much information.

## Assumptions and Limitations
1. **Effect Size**: The assumed effect size of 0.15 is based on prior literature and expert judgment. If the true effect size is smaller, the study may be underpowered.
2. **Data Distribution**: The calculation assumes a relatively uniform distribution of space groups. In reality, some space groups are much more common than others, which may affect the effective power of the test.
3. **Scaffold Diversity**: The 500 scaffolds are assumed to be chemically diverse and representative of the broader chemical space of organic crystals.
4. **Polymorphism**: The analysis treats each unique (SMILES, Space Group) pair as a distinct sample, which may increase the effective sample size but also introduces complexity in the data structure.

## Implementation in Project
The target sample size of 500 scaffolds is used as a configuration parameter in `code/config.py` and is referenced in the data ingestion pipeline (`code/ingestion/run_pipeline.py`) to ensure that the dataset meets the minimum requirements for statistical validity.

The power analysis was implemented programmatically in `code/analysis/power.py` to allow for recalculations if the assumptions change or if more precise effect size estimates become available.

## Conclusion
Based on the power analysis, a target sample size of **500 scaffolds** is recommended for the "Predicting Crystal Structures from Molecular Fingerprints" project. This sample size provides 80% power to detect a small-to-medium effect size (Cohen's w = 0.15) at a 5% significance level, ensuring that the study is adequately powered to draw meaningful conclusions about the relationship between molecular fingerprints and crystal structures.