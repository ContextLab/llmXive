# Deviation Rationale: Spec vs. Plan Conflict Resolution

## Overview

This document outlines the critical deviations made between the original feature specification (`spec.md`) and the implementation plan (`plan.md`) for the project "Investigating the Impact of Code Ownership on LLM Code Understanding" (PROJ-441).

These deviations were necessary to ensure scientific rigor, statistical validity, and alignment with the specific constraints of the research methodology. The original specification provided a simplified proxy approach, while the implementation plan adopted a more robust, industry-standard statistical framework.

## 1. Ownership Metric: LOC-Weighted Gini vs. Simple Commit Count

### Specification Requirement (FR-001)
The original spec proposed using a **simple commit count** per developer as a proxy for code ownership. The metric was intended to be a raw frequency count of commits attributed to specific developers within a repository.

### Plan Deviation
The implementation plan replaces the simple commit count with a **LOC-Weighted Gini Coefficient** of commit distribution.

### Rationale for Deviation
1. **Granularity of Contribution**: A simple commit count fails to distinguish between a developer committing 1 line of code versus 1,000 lines. In the context of "ownership," the volume of code contributed is a more accurate proxy for responsibility and familiarity with the codebase than the mere frequency of commits.
2. **Inequality Measurement**: The Gini coefficient is the standard economic metric for measuring inequality. Applying it to Line-of-Code (LOC) weighted distribution allows us to quantify the *concentration* of ownership. A low Gini coefficient implies shared ownership (high collaboration), while a high Gini coefficient implies a "bus factor" risk (centralized ownership).
3. **Scientific Accuracy**: Research into socio-technical aspects of software engineering (e.g., "Bus Factor" studies) consistently shows that LOC-weighted metrics correlate better with code quality and defect density than raw commit counts.

### Implementation Detail
The metric is calculated in `code/extractors/git_metrics.py` by:
1. Running `git blame` on all Python/Java files in the target repository at a specific historical commit.
2. Aggregating the number of lines attributed to each unique author.
3. Computing the Gini coefficient based on these line counts.

## 2. Statistical Methodology: Linear Mixed-Effects Model (LMM) vs. Simple Regression

### Specification Requirement (FR-004)
The original spec suggested a standard **Linear Regression** (OLS) model to correlate ownership metrics with LLM performance (BLEU score).

### Plan Deviation
The implementation plan mandates the use of a **Linear Mixed-Effects Model (LMM)** (also known as Hierarchical Linear Modeling).

### Rationale for Deviation
1. **Hierarchical Data Structure**: The data is inherently hierarchical. Code snippets (observations) are nested within repositories. Snippets from the same repository are not statistically independent; they share context, coding style, and team dynamics.
2. **Violation of Independence**: Standard OLS regression assumes independent observations. Applying OLS to nested data violates this assumption, leading to underestimated standard errors and inflated Type I error rates (false positives).
3. **Random Effects**: An LMM allows us to model the **Repository** as a random effect. This accounts for the variance introduced by the repository itself, isolating the specific effect of the ownership metric on the snippet-level performance.
4. **Robustness**: LMMs are the gold standard in social science and software engineering research for analyzing nested data, ensuring the p-values reported for the ownership coefficient are statistically valid.

### Implementation Detail
The analysis is performed in `code/analysis/regression.py` using the `statsmodels` library. The model formula is structured as:
`BLEU_Score ~ Ownership_Metric + Complexity + Documentation_Density + (1 | Repository_ID)`

## 3. Unit of Analysis: Snippet-Level vs. Repository-Level

### Specification Requirement (Implied)
The spec implied aggregating metrics to the repository level for analysis.

### Plan Deviation
The plan explicitly defines the **Snippet** as the unit of analysis (n=150), with ownership metrics aggregated from the repo level but applied to individual snippets.

### Rationale for Deviation
1. **Statistical Power**: Aggregating to the repository level would reduce the sample size to the number of repositories (likely < 20), making statistical inference impossible.
2. **Variance Explanation**: Analyzing at the snippet level allows the model to explain variance in LLM performance based on local code complexity and documentation, while controlling for the global ownership structure of the repository.

## Conclusion

These deviations are not merely technical preferences but are essential for the scientific validity of the research. The LOC-weighted Gini coefficient provides a more accurate measure of ownership concentration, and the Linear Mixed-Effects Model ensures that the statistical conclusions drawn from the data are robust against the hierarchical nature of software repositories.

All implementations strictly adhere to the `plan.md` methodology to ensure the project meets the acceptance criteria for scientific rigor (SC-003, SC-005).