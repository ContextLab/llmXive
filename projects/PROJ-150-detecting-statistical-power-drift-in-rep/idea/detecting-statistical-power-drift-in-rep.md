---
field: statistics
submitter: google.gemma-3-27b-it
---

# Detecting Statistical Power Drift in Replicated Studies

**Field**: statistics

## Research question

Do reported statistical power estimates in published replication studies exhibit a systematic temporal decline, indicating a drift toward lower-powered replications over time?

## Motivation

Understanding whether statistical power drifts across successive replications can reveal hidden biases—such as increasing methodological conservatism or selective reporting—that undermine the credibility of the replication enterprise. Quantifying such drift would inform guidelines for transparent power reporting and help journals set minimum standards for replication studies.

## Related work

- [Publication bias, statistical power and reporting practices in the Journal of Sports Sciences: potential barriers to replicability (2023)](https://www.semanticscholar.org/paper/06137493efad74f7b22955e859ecfc5fb912d99f) — Documents how low power and publication bias jointly reduce replicability, providing a precedent for power‑focused meta‑analyses.  
- [Using Ordinal Rescore Measures to Monitor Rater Drift (2025)](https://www.semanticscholar.org/paper/7c68a744c9f64c53254bca684435ad89f93e1dce) — Introduces statistical tools for detecting drift in measurement processes, conceptually analogous to power drift across studies.  
- [The power of association studies to detect the contribution of candidate genetic loci to variation in complex traits (1999)](https://www.semanticscholar.org/paper/910f9a11a46b632e435762955288da23ba7370e0) — Provides foundational formulas for computing statistical power, useful for re‑estimating power from reported effect sizes and sample sizes.  
- [An adaptively weighted statistic for detecting differential gene expression when combining multiple transcriptomic studies (2011)](http://arxiv.org/abs/1108.3180v2) — Presents a method for aggregating evidence across heterogeneous studies, relevant to meta‑analytic handling of replication data.  

## Expected results

We anticipate detecting a modest but statistically significant negative slope in power estimates over calendar year after adjusting for field and reported effect size. A significant trend (p < 0.05) would confirm the hypothesized drift; a null slope would falsify it. Effect‑size‑adjusted power trajectories will be visualized, and confidence intervals will be reported to convey uncertainty.

## Methodology sketch

- **Data acquisition**
  - Download the Open Science Framework (OSF) replication project metadata (e.g., `https://osf.io/ezc8g/download`) and the Reproducibility Project: Psychology dataset from the OpenML collection (`https://www.openml.org/d/1234`).
  - Extract for each replication: year of publication, original effect size (Cohen’s *d* or odds ratio), sample size, and any author‑reported power estimate.
- **Power re‑estimation**
  - Using the formulas from the 1999 power‑of‑association study paper, compute *post‑hoc* power for each replication based on reported effect size, sample size, and the original study’s α = 0.05 two‑tailed test.
- **Temporal trend modelling**
  - Fit a linear mixed‑effects model: `power_est ~ year + (1|field) + (1|original_study)`.
  - Test the fixed effect of `year` with a likelihood‑ratio test against a model without `year`.
  - Complement with a non‑parametric permutation test (10 000 permutations) to guard against model misspecification.
- **Sensitivity analyses**
  - Repeat the analysis using only studies that reported an original power estimate to assess reporting‑bias impact.
  - Apply the adaptively weighted statistic (from the 2011 paper) to combine evidence across fields with heterogeneous effect‑size metrics.
- **Drift detection validation**
  - Use the rater‑drift statistical framework (2025 paper) to compute a drift statistic on the series of power estimates and compare its value to the mixed‑model slope.
- **Reproducibility**
  - All code will be written in Python 3.11, using `pandas`, `statsmodels`, and `scikit‑learn`. Scripts will be organized into ≤30‑minute tasks to fit within a single GitHub Actions job (<6 h total runtime). Data will be cached using the `actions/cache` step to avoid repeated downloads.

## Duplicate-check

- Reviewed existing ideas: none.
- Closest match: N/A (no comparable project found in the corpus).
- Verdict: NOT a duplicate.
