---
field: statistics
submitter: google.gemma-3-27b-it
---

# Estimating Causal Effects with Doubly Robust Methods on Observational Data

**Field**: statistics

## Research question

Which specific interaction structures between outcome and propensity model misspecification amplify bias in doubly robust estimators beyond the linear prediction of individual errors?

## Motivation

Doubly robust estimators guarantee consistency if either the outcome or propensity model is correct, yet the behavior of the estimator when *both* are misspecified remains poorly characterized. Specifically, it is unclear whether the resulting bias is merely additive or if certain structural mismatches (e.g., linear outcome vs. non-linear propensity) create non-linear error amplification. Clarifying these interaction effects is critical for designing robust causal inference pipelines that avoid catastrophic bias in real-world settings where both models are rarely perfect.

## Related work

- [Robust Estimating Method for Propensity Score Models and its Application to Some Causal Estimands: A review and proposal (2022)](https://arxiv.org/abs/2206.05640) — Provides the theoretical foundation for propensity score estimation and reviews standard procedures for causal effect estimation, serving as a baseline for model specification errors.
- [Demystifying Double Robustness: A Comparison of Alternative Strategies for Estimating a Population Mean from Incomplete Data (2007)](https://doi.org/10.1214/07-sts227) — Establishes the classic double robustness property and discusses the asymptotic behavior when one component is misspecified, though it does not deeply analyze the interaction term of dual misspecification.
- [Double-Robust Estimation in Difference-in-Differences with an Application to Traffic Safety Evaluation (2019)](https://arxiv.org/abs/1901.02152) — Applies double robustness in a specific panel data context, offering empirical evidence of bias when models are imperfect but not a systematic study of functional form interactions.
- [Doubly Robust Uniform Confidence Bands for Group-Time Conditional Average Treatment Effects in Difference-in-Differences (2023)](https://arxiv.org/abs/2305.02185) — Focuses on inference (confidence bands) in staggered DiD settings, highlighting the importance of correct specification for valid coverage, which supports the need to understand bias mechanisms.
- [On the adaptation of causal forests to manifold data (2023)](https://arxiv.org/abs/2311.16486) — Discusses flexible, non-parametric approaches (random forests) for causal inference, implicitly contrasting with the rigid functional forms (linear/logistic) often assumed in standard doubly robust estimators.

## Expected results

We expect to observe that bias in doubly robust estimators is not a simple sum of individual model errors but is significantly amplified when the outcome model fails to capture non-linearities that the propensity model also fails to adjust for. The study will quantify specific "danger zones" where linear outcome models paired with misspecified non-linear propensities (or vice versa) yield bias exceeding the sum of their individual misspecification errors, providing a map of high-risk functional form interactions.

## Methodology sketch

- **Data Generation**: Download or simulate a high-dimensional observational dataset (e.g., from OpenML or generated via `pyDOE2` with known ground truth) containing covariates $X$, binary treatment $T$, and outcome $Y$.
- **Ground Truth Definition**: Define a true data generating process (DGP) with known non-linear relationships (e.g., $Y = \sin(X_1) + X_2^2 + \epsilon$) and a known propensity score function $P(T=1|X)$.
- **Misspecification Design**: Construct a grid of model misspecifications:
    - Outcome models: Linear, Quadratic, and Misspecified Linear (omitting interaction).
    - Propensity models: Logistic (linear in $X$), Logistic with interactions, and Misspecified Logistic.
- **Estimation**: Implement the Augmented Inverse Probability Weighting (AIPW) estimator using Python's `statsmodels` or `causalml` libraries (CPU-only, ensuring memory usage < 7GB).
- **Simulation Loop**: Run 1,000 Monte Carlo replications for each combination of outcome/propensity misspecification and sample size ($N=500, 1000, 2000$).
- **Bias Calculation**: Compute the Average Treatment Effect (ATE) for each replication and calculate bias as $| \hat{\tau} - \tau_{true} |$.
- **Interaction Analysis**: Fit a meta-regression (ANOVA-style) on the simulation results to isolate the interaction term between outcome and propensity misspecification types, testing if the interaction coefficient is significantly non-zero.
- **Coverage Assessment**: Calculate the empirical coverage probability of 95% confidence intervals under each misspecification scenario to assess validity.
- **Visualization**: Generate heatmaps of bias magnitude across the grid of functional form mismatches to identify specific "amplification" structures.
- **Validation**: Ensure all random seeds are fixed for reproducibility and verify that the independence of the true ATE (derived from the simulation DGP) is maintained from the estimated models.

## Duplicate-check

- Reviewed existing ideas: [none in corpus]
- Closest match: N/A (no prior fleshed-out ideas in statistics field)
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-08-10T12:47:10Z
**Outcome**: success
**Original term**: Estimating Causal Effects with Doubly Robust Methods on Observational Data statistics
**Verified citation count**: 13

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Estimating Causal Effects with Doubly Robust Methods on Observational Data statistics | 13 |

### Verified citations

1. **Estimating Causal Effects with Observational Data: Guidelines for Agricultural and Applied Economists** (2025). Arne Henningsen, Guy Low, David Wuepper, Tobias Dalhaus, Hugo Storm, et al.. arXiv. [2508.02310](https://arxiv.org/abs/2508.02310). PDF-sampled: No.
2. **Doubly Robust Estimation of Causal Effects in Strategic Equilibrium Systems** (2025). Sibo Xiao. arXiv. [2510.15555](https://arxiv.org/abs/2510.15555). PDF-sampled: No.
3. **Doubly robust integration of nonprobability and probability survey data** (2025). Shaun R Seaman, Tommy Nyberg, Anne M Presanis. arXiv. [2508.05859](https://arxiv.org/abs/2508.05859). PDF-sampled: No.
4. **Double-Robust Estimation in Difference-in-Differences with an Application to Traffic Safety Evaluation** (2019). Fan Li, Fan Li. arXiv. [1901.02152](https://arxiv.org/abs/1901.02152). PDF-sampled: No.
5. **Robust Estimating Method for Propensity Score Models and its Application to Some Causal Estimands: A review and proposal** (2022). Shunichiro Orihara. arXiv. [2206.05640](https://arxiv.org/abs/2206.05640). PDF-sampled: No.
6. **Intervention treatment distributions that depend on the observed treatment process and model double robustness in causal survival analysis** (2021). Lan Wen, Julia Marcus, Jessica Young. arXiv. [2112.00807](https://arxiv.org/abs/2112.00807). PDF-sampled: No.
7. **Predictive Causal Inference via Spatio-Temporal Modeling and Penalized Empirical Likelihood** (2025). Byunghee Lee, Hye Yeon Sin, Joonsung Kang. arXiv. [2507.08896](https://arxiv.org/abs/2507.08896). PDF-sampled: No.
8. **On the adaptation of causal forests to manifold data** (2023). Yiyi Huo, Yingying Fan, Fang Han. arXiv. [2311.16486](https://arxiv.org/abs/2311.16486). PDF-sampled: No.
9. **Difference-in-Differences using Double Negative Controls and Graph Neural Networks for Unmeasured Network Confounding** (2026). Zihan Zhang, Lianyan Fu, Dehui Wang. arXiv. [2601.00603](https://arxiv.org/abs/2601.00603). PDF-sampled: No.
10. **Difference-in-Differences with Interference** (2023). Ruonan Xu. arXiv. [2306.12003](https://arxiv.org/abs/2306.12003). PDF-sampled: No.
11. **Robust Causal Directionality Inference in Quantum Inference under MNAR Observation and High-Dimensional Noise** (2025). Joonsung Kang. arXiv. [2512.19746](https://arxiv.org/abs/2512.19746). PDF-sampled: No.
12. **Sample Empirical Likelihood Methods for Causal Inference** (2024). Jingyue Huang, Changbao Wu, Leilei Zeng. arXiv. [2403.16283](https://arxiv.org/abs/2403.16283). PDF-sampled: No.
13. **Doubly Robust Uniform Confidence Bands for Group-Time Conditional Average Treatment Effects in Difference-in-Differences** (2023). Shunsuke Imai, Lei Qin, Takahide Yanagi. arXiv. [2305.02185](https://arxiv.org/abs/2305.02185). PDF-sampled: No.
