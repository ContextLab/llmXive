---
field: statistics
submitter: google.gemma-3-27b-it
---

# Evaluating the Impact of Different Missing Data Mechanisms on Regression Discontinuity Designs  

**Field**: statistics  

## Research question  

How do missing completely at random (MCAR), missing at random (MAR), and missing not at random (MNAR) mechanisms affect the bias, consistency, and efficiency of common regression discontinuity (RD) estimators, and which correction strategies (e.g., multiple imputation, inverse‑probability weighting) can mitigate these effects?

## Motivation  

RD designs are a cornerstone of causal inference when randomization is infeasible, yet their validity hinges on smoothness of the forcing variable near the cutoff. Real‑world applications often suffer from incomplete observations of the outcome or covariates, and the impact of different missing‑data mechanisms on RD estimates is poorly understood. Clarifying when standard RD estimators remain reliable—and when they require bias‑correction—will give applied researchers concrete guidance for handling missing data in quasi‑experimental settings.

## Related work  

- [Optimized Regression Discontinuity Designs (2017)](http://arxiv.org/abs/1705.01677v3) — Provides a survey of RD estimation strategies and highlights the importance of bandwidth selection, forming a baseline for evaluating estimator performance.  
- [Manipulation‑Robust Regression Discontinuity Designs (2020)](http://arxiv.org/abs/2009.07551v7) — Introduces conditions for identification when the running variable is manipulated, offering theoretical tools that can be extended to missing‑data scenarios.  
- [Orthogonal Matching Pursuit with Noisy and Missing Data: Low and High Dimensional Results (2012)](http://arxiv.org/abs/1206.0823v2) — Studies regression with missing covariates, informing the choice of imputation and regularization techniques for RD covariate adjustment.  
- [High‑dimensional regression with noisy and missing data: Provable guarantees with nonconvexity (2011)](http://arxiv.org/abs/1109.3714v4) — Offers guarantees for estimators under missing data, useful for constructing robust RD estimators in high‑dimensional settings.  
- [Least angle regression (2004)](https://doi.org/10.1214/009053604000000067) — Classic method for variable selection that can be combined with imputation to improve RD model specification when covariates are partially missing.  

## Expected results  

- Under MCAR, standard local‑linear RD estimators will retain consistency but show modest efficiency loss proportional to the missing fraction.  
- Under MAR, properly specified multiple‑imputation or inverse‑probability‑weighting will recover unbiased estimates, whereas naïve RD will exhibit bias proportional to the degree of missingness.  
- Under MNAR, all naïve estimators will be biased; bias‑correction methods that model the missingness mechanism (e.g., selection models) will reduce but not fully eliminate bias.  
- Quantitative metrics (bias, root‑mean‑square error, 95 % confidence‑interval coverage) will clearly separate the three mechanisms and demonstrate which correction technique offers the best trade‑off between bias reduction and variance inflation.

## Methodology sketch  

- **Data acquisition**  
  - Download a publicly available RD‑eligible dataset (e.g., the *UCI “College Distance”* dataset or the *National Longitudinal Survey of Youth* education cutoff) via `wget`/`curl`.  
  - Generate synthetic RD data (running variable, outcome, covariates) using the canonical triangular kernel model to allow controlled experiments.  

- **Introduce missingness**  
  - Apply MCAR, MAR, and MNAR mechanisms to the outcome and/or covariates at missing rates of 10 %, 30 %, and 50 % using reproducible random seeds.  
  - For MAR, make missingness depend on observed covariates; for MNAR, let missingness depend on the unobserved outcome value.  

- **Estimation procedures**  
  1. **Naïve RD**: Local‑linear regression with triangular kernel (bandwidth chosen by Imbens‑Kalyanaraman rule).  
  2. **Multiple Imputation (MI)**: `mice` package (5 imputations) applied to missing variables, followed by RD on each completed dataset and Rubin’s pooling.  
  3. **Inverse‑Probability Weighting (IPW)**: Estimate propensity of being observed via logistic regression (including covariates) and weight the RD estimator accordingly.  
  4. **Selection‑model correction**: Fit a joint model of outcome and missingness (Heckman‑type) and compute a bias‑adjusted RD estimate.  

- **Performance evaluation**  
  - For each combination of missingness mechanism, missing rate, and estimator, compute bias, RMSE, and empirical coverage of 95 % confidence intervals over 1,000 Monte‑Carlo replications.  
  - Summarize results in tables and heat‑map visualizations (generated with `matplotlib`/`seaborn`).  

- **Computational constraints**  
  - All simulations and analyses run in pure Python/R on the GitHub Actions runner (≤2 CPU cores, ≤7 GB RAM).  
  - Each Monte‑Carlo replication is limited to ≤0.2 seconds; total runtime ≈ 4 hours, comfortably within the 6‑hour limit.  

## Duplicate-check  

- Reviewed existing ideas: none.  
- Closest match: N/A (no semantically similar fleshed‑out idea detected).  
- Verdict: **NOT a duplicate**.
