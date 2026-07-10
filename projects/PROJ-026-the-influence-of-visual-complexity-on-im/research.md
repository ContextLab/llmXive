# Research Methodology: Statistical Analysis Plan

## 1. Overview

This document outlines the statistical analysis plan for the study "The Influence of Visual Complexity on Implicit Bias." It details the primary hypothesis testing method, justification for the chosen approach, and sensitivity analysis protocols.

## 2. Primary Statistical Method: Permutation Test

### 2.1 Decision Record

**Original Plan**: The initial experimental design proposal suggested the use of Analysis of Variance (ANOVA) to compare Implicit Association Test (IAT) D-scores across different levels of visual complexity (Low, Medium, High).

**Revised Plan**: The methodology has been updated to employ a **Permutation Test** (also known as a randomization test) as the primary inferential statistic.

**Effective Date**: [Current Date]
**Reference**: Project Plan PROJ-026, Task T033a.

### 2.2 Justification for Methodological Shift

The shift from ANOVA to a Permutation Test is driven by three critical factors specific to the nature of visual stimulus data and the requirements of rigorous causal inference in this context:

1. **Handling Stimulus-Set Confounds**:
 In studies involving image stimuli, the specific set of images used can introduce confounding variance that is difficult to model with standard parametric assumptions. ANOVA assumes that the error terms are independent and identically distributed, an assumption often violated when specific images drive the effect disproportionately. A Permutation Test allows for the exact distribution of the test statistic under the null hypothesis to be derived empirically by shuffling labels (e.g., complexity categories) while keeping the stimulus data intact. This effectively controls for the specific set of images used, as the permutation respects the structure of the stimulus set (Greenwald et al., 2003; Edgington & Onghena, 2007).

2. **Robustness to Non-Normality**:
 IAT D-scores, while often approximately normal in large samples, can exhibit skewness or kurtosis, particularly in smaller subsamples or when reaction time outliers are present. ANOVA is sensitive to violations of normality. The Permutation Test is a non-parametric method that makes no assumptions about the underlying distribution of the data, relying instead on the randomization of the observed data itself. This ensures the validity of the p-value regardless of the distribution shape.

3. **Small Sample Size Considerations**:
 If the study is conducted with a moderate number of participants, the asymptotic properties required for ANOVA F-tests may not fully hold. Permutation tests provide an exact test of significance (conditional on the data) that is valid for any sample size, provided the randomization assumption holds.

### 2.3 Implementation Details

* **Test Statistic**: The mean difference of D-scores between the High Complexity and Low Complexity conditions.
* **Procedure**:
 1. Calculate the observed test statistic ($T_{obs}$) from the actual data.
 2. Randomly permute the condition labels (High/Low/Medium) across the observations $N$ times (where $N \geq 10,000$ to ensure stable p-value estimation).
 3. For each permutation, calculate the test statistic ($T_{perm}$).
 4. The p-value is calculated as the proportion of $|T_{perm}| \geq |T_{obs}|$.
* **Seed**: A fixed random seed (42) will be used for reproducibility.

### 2.4 Sensitivity Analysis: Leave-One-Image-Out (LOIO)

To further address the concern of stimulus-set confounds, a **Leave-One-Image-Out (LOIO)** sensitivity analysis will be conducted. This involves:
1. Iteratively removing one image stimulus from the dataset.
2. Re-running the Permutation Test on the reduced dataset.
3. Assessing the stability of the p-value and effect size across iterations.
If the significance of the result is driven by a single outlier image, the LOIO analysis will reveal this instability, thereby validating the robustness of the findings.

## 3. Effect Size Reporting

While the Permutation Test provides the p-value, effect sizes will be reported to quantify the magnitude of the influence.
* **Metric**: Cohen's $d$ (standardized mean difference).
* **Note**: Partial $\eta^2$ is not applicable to the Permutation Test framework and will not be reported. Instead, the "Permutation Effect Size" (Cohen's $d$) will be the primary metric for magnitude.

## 4. References

* Edgington, E. S., & Onghena, P. (2007). *Randomization Tests* (4th ed.). Chapman and Hall/CRC.
* Greenwald, A. G., Nosek, B. A., & Banaji, M. R. (2003). Understanding and using the Implicit Association Test: I. An improved scoring algorithm. *Journal of Personality and Social Psychology*, 85(2), 197–216.
* Good, P. I. (2005). *Permutation, Parametric, and Bootstrap Tests of Hypotheses* (3rd ed.). Springer.