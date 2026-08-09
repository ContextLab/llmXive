# Research Methodology: Statistical Analysis Strategy

## Overview

This document outlines the statistical methodology employed to analyze the influence of visual complexity on implicit bias in the current study. It specifically details the decision to utilize a **Permutation Test** rather than a traditional Analysis of Variance (ANOVA) for the primary hypothesis testing.

## Methodological Shift: From ANOVA to Permutation Test

### Original Consideration: ANOVA
Historically, Analysis of Variance (ANOVA) has been the standard parametric test for comparing means across multiple groups. In the context of this research, an ANOVA approach would have been used to determine if there are statistically significant differences in D-scores (implicit bias measures) between groups defined by visual complexity categories (Low, Medium, High).

**Limitations of ANOVA in this Context:**
1. **Assumption of Normality:** ANOVA assumes that the residuals are normally distributed. Implicit bias data (D-scores) often exhibit non-normal distributions, particularly with small sample sizes or skewed reaction time data.
2. **Homogeneity of Variance:** ANOVA requires equal variances across groups. Visual complexity stimuli may induce different levels of variance in response times, violating this assumption.
3. **Stimulus-Set Confounds:** A critical limitation in visual complexity research is the "stimulus-set" effect. If specific images are consistently assigned to specific complexity categories, any observed effect could be driven by idiosyncratic properties of those specific images rather than the general property of "complexity." Standard ANOVA does not inherently account for this clustering without complex mixed-model extensions that require large sample sizes.

### Adopted Method: Permutation Test
To address these limitations and ensure robust, assumption-free inference, this project adopts a **Permutation Test** (also known as a randomization test) as the primary statistical method (Task T033).

**Justification for Permutation Test:**
1. **Distribution-Free:** The permutation test makes no assumptions about the underlying distribution of the data. It derives the null distribution empirically by randomly shuffling the observed data labels (complexity groups) and recalculating the test statistic (mean difference in D-scores).
2. **Robustness to Small Samples:** It provides exact p-values even with small sample sizes where asymptotic approximations (like F-distributions in ANOVA) may fail.
3. **Control for Stimulus-Set Confounds:** By permuting the assignment of stimuli to complexity categories (or permuting participant responses within the context of the specific stimulus set), the test inherently accounts for the specific structure of the visual stimuli, isolating the effect of the complexity metric itself.
4. **Flexibility:** It allows for the direct calculation of effect sizes (Cohen's d) and confidence intervals based on the empirical distribution, providing a more intuitive interpretation of the magnitude of the effect.

### Implementation Details
The implementation (see `code/analysis/permutation.py`) follows these steps:
1. **Observed Statistic:** Calculate the mean difference in D-scores between the High and Low complexity groups.
2. **Null Distribution Generation:** Randomly shuffle the group labels (High/Low) across the participants $N$ times (where $N$ is sufficiently large, e.g., 10,000) to simulate the null hypothesis that complexity has no effect.
3. **P-value Calculation:** The p-value is the proportion of permuted statistics that are as extreme or more extreme than the observed statistic.
4. **Sensitivity Analysis:** The method includes a Leave-One-Image-Out (LOIO) sensitivity analysis (Task T035a) to further verify that the results are not driven by a single outlier stimulus.

### Citation and Plan Alignment
This methodological decision aligns with the project's implementation plan and the specific requirement to handle stimulus-set confounds effectively. The shift from ANOVA to Permutation Test is explicitly documented in the project plan to ensure the robustness of the findings against the unique challenges of visual complexity research.

**References:**
* Good, P. I. (2005). *Permutation, Parametric, and Bootstrap Tests of Hypotheses*. Springer.
* Edgington, E. S., & Onghena, P. (2007). *Randomization Tests*. CRC Press.
* Project Plan: Section on Statistical Analysis (FR-003 Amendment).