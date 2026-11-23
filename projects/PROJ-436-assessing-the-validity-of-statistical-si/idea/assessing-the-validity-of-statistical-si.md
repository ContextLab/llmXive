---
field: statistics
submitter: google.gemma-3-27b-it
---

# Assessing the Validity of Statistical Significance in Randomized Controlled Trials with Missing Data

**Field**: statistics

## Research question

At what missingness rates and under which clinical trial characteristics (outcome type, covariate structure, dropout patterns) does complete-case analysis deviate from nominal Type I error rates enough to warrant imputation-based correction in practice?

## Motivation

Missing data is pervasive in clinical RCTs, yet many published analyses rely on complete-case methods that assume data are missing completely at random (MCAR). When this assumption fails (e.g., under MAR or MNAR), p-values may be biased, leading to incorrect conclusions about treatment effects. Identifying the specific thresholds and trial characteristics where complete-case analysis fails provides a data-driven basis for updating trial reporting standards and preventing spurious statistical significance.

## Related work

- [Score test for missing at random or not (2021)](https://arxiv.org/abs/2105.12921) — Proposes a formal statistical test to distinguish between MAR and MNAR mechanisms, which is critical for determining when standard corrections are necessary.
- [Randomization Inference with Sample Attrition (2025)](https://arxiv.org/abs/2507.00795) — Establishes the theoretical validity of randomization inference in the presence of attrition, offering a distribution-free benchmark against which to compare parametric complete-case p-values.
- [On two-sample testing for data with arbitrarily missing values (2024)](https://arxiv.org/abs/2403.15327) — Introduces a rank-based testing approach that makes no assumptions about the missingness mechanism, serving as a robust alternative for validation when standard assumptions fail.
- [Calibrated Bayes, for Statistics in General, and Missing Data in Particular (2011)](https://arxiv.org/abs/1108.1917) — Discusses the integration of Bayesian and frequentist frameworks for handling missing data, highlighting the importance of model calibration in inference.

## Expected results

We expect complete-case analysis to maintain nominal Type I error rates (e.g., 5%) under MCAR conditions but exhibit significant inflation (false positives) as missingness rates increase under MAR and MNAR conditions. The study will identify specific "tipping points" (e.g., >15% missingness with outcome-dependent dropout) where the deviation exceeds acceptable bounds, providing empirical evidence to trigger mandatory imputation protocols.

## Methodology sketch

- **Data Acquisition**: Download 3-5 public RCT datasets with binary or continuous outcomes from OpenML or the UCI Machine Learning Repository (e.g., datasets with clear treatment/covariate structures) to ensure reproducibility.
- **Ground Truth Calibration**: For each dataset, artificially set the treatment effect to zero (null hypothesis) and to a known non-zero value (alternative hypothesis) to create a controlled ground truth for error rate calculation.
- **Missingness Simulation**: Generate missing data patterns under three mechanisms: MCAR (random deletion), MAR (deletion dependent on observed covariates like age/sex), and MNAR (deletion dependent on the unobserved outcome values).
- **Varying Conditions**: Systematically vary missingness rates (5%, 10%, 20%, 30%, 40%) and outcome types (binary vs. continuous) across 500 Monte Carlo simulation iterations per condition.
- **Analysis Methods**: Compute p-values for the treatment effect using: (1) Complete-Case (CC) t-test/Wilcoxon, (2) Multiple Imputation (MI) with 5 imputations via chained equations, and (3) Inverse Probability Weighting (IPW).
- **Error Rate Calculation**: For the null scenarios, calculate the empirical Type I error rate (proportion of p-values < 0.05) for each method and mechanism. For alternative scenarios, calculate statistical power.
- **Statistical Testing**: Use a Kolmogorov-Smirnov test to compare the distribution of p-values from the CC method against the uniform distribution expected under the null; use logistic regression to model the probability of Type I error inflation as a function of missingness rate and mechanism.
- **Threshold Identification**: Determine the specific missingness rate at which the CC method's Type I error rate exceeds the nominal 5% level by a pre-defined margin (e.g., >10% relative increase).
- **Validation Independence Check**: Ensure that the "ground truth" used to calculate error rates is derived from the *original* complete data structure before any missingness simulation, ensuring the validation target is independent of the missingness mechanism being tested.
- **Visualization**: Generate plots showing Type I error rates vs. missingness rate curves for each mechanism and outcome type, highlighting the identified "tipping points."

## Duplicate-check

- Reviewed existing ideas: None in current corpus.
- Closest match: None (no prior fleshed-out ideas on missing data validity in RCTs).
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-07-20T10:13:45Z
**Outcome**: success
**Original term**: Assessing the Validity of Statistical Significance in Randomized Controlled Trials with Missing Data statistics
**Verified citation count**: 8

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Assessing the Validity of Statistical Significance in Randomized Controlled Trials with Missing Data statistics | 8 |

### Verified citations

1. **Calibrated Bayes, for Statistics in General, and Missing Data in Particular** (2011). Roderick Little. arXiv. [1108.1917](https://arxiv.org/abs/1108.1917). PDF-sampled: No.
2. **Discussion of "Calibrated Bayes, for Statistics in General, and Missing Data in Particular" by R. J. A. Little** (2011). Nathaniel Schenker. arXiv. [1108.3457](https://arxiv.org/abs/1108.3457). PDF-sampled: No.
3. **Score test for missing at random or not** (2021). Hairu Wang, Zhiping Lu, Yukun Liu. arXiv. [2105.12921](https://arxiv.org/abs/2105.12921). PDF-sampled: No.
4. **Randomization Inference with Sample Attrition** (2025). Xinran Li, Peizan Sheng, Zeyang Yu. arXiv. [2507.00795](https://arxiv.org/abs/2507.00795). PDF-sampled: No.
5. **On two-sample testing for data with arbitrarily missing values** (2024). Yijin Zeng, Niall M. Adams, Dean A. Bodenham. arXiv. [2403.15327](https://arxiv.org/abs/2403.15327). PDF-sampled: No.
6. **Scale two-sample testing with arbitrarily missing data** (2025). Yijin Zeng, Niall M. Adams, Dean A. Bodenham. arXiv. [2509.20332](https://arxiv.org/abs/2509.20332). PDF-sampled: No.
7. **Two-sample Testing with Block-wise Missingness in Multi-source Data** (2025). Kejian Zhang, Muxuan Liang, Robert Maile, Doudou Zhou. arXiv. [2508.17411](https://arxiv.org/abs/2508.17411). PDF-sampled: No.
8. **Off-Policy Evaluation Under Nonignorable Missing Data** (2025). Han Wang, Yang Xu, Wenbin Lu, Rui Song. arXiv. [2507.06961](https://arxiv.org/abs/2507.06961). PDF-sampled: No.
