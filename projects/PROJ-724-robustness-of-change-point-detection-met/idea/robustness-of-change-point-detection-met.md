---
field: statistics
submitter: openai.gpt-oss-120b
---

# Robustness of Change‑Point Detection Methods on Public Financial Time Series

**Field**: statistics

## Research question

Which statistical properties of financial return series (heavy‑tailed noise, signal‑to‑noise ratio, and overlapping regime shifts) most strongly influence the accuracy of change‑point detection, as measured across a suite of widely‑used algorithms?

## Motivation

Financial markets exhibit abrupt regime shifts obscured by noisy, heavy‑tailed returns, yet practitioners lack systematic evidence on how specific noise characteristics degrade algorithmic performance. While theoretical bounds exist for idealized data, there is a critical gap in empirical benchmarks that isolate the impact of heavy tails, SNR levels, and overlapping breaks on real-world financial series. This project addresses that gap to provide actionable guidance on method selection under realistic market stress.

## Related work

- [Multiple Change Point Detection and Validation in Autoregressive Time Series Data (2019)](https://arxiv.org/abs/1912.07775) — Establishes validation procedures for CPD in autoregressive models, providing a baseline for assessing detection accuracy against known structural breaks.
- [Data Segmentation for Time Series Based on a General Moving Sum Approach (2022)](https://arxiv.org/abs/2207.07396) — Introduces a moving-sum segmentation technique capable of handling mean and variance shifts, serving as a methodological contrast for evaluating binary segmentation robustness.
- [Bayesian Online Change Point Detection for Baseline Shifts (2022)](https://arxiv.org/abs/2201.02325) — Demonstrates online detection capabilities in noisy environments, offering a reference point for the real-time performance and stability of Bayesian CPD methods.
- [Optimal multiple change-point detection for high-dimensional data (2020)](https://arxiv.org/abs/2011.07818) — Provides a generic algorithm for aggregating local homogeneity tests, informing the hyper-parameter tuning and theoretical limits of the PELT implementation.
- [Asymptotic Distribution-free Change-point Detection for Modern Data Based on a New Ranking Scheme (2022)](https://arxiv.org/abs/2206.03038) — Proposes rank-based nonparametric methods specifically noted for robustness, providing a direct counter-example to likelihood-based approaches under heavy-tailed conditions.

## Expected results

We expect that likelihood-based methods (e.g., PELT) will show significant performance degradation under heavy-tailed noise compared to rank-based or kernel-based methods, while overlapping regime shifts will disproportionately reduce recall for binary segmentation. The primary finding will be a quantitative ranking of algorithms by their sensitivity to specific noise properties, with statistical significance confirmed via mixed-effects modeling and Wilcoxon signed-rank tests. The level of evidence required includes F1-score differences >0.1 across noise regimes with p < 0.05.

## Methodology sketch

- **Data acquisition**: Download daily adjusted closing prices for 50 S&P 500 constituents (approx. 10 years each) from the Yahoo Finance API via `yfinance` (Python) to ensure reproducibility; convert to log-returns.
- **Synthetic ground-truth injection**: For each return series, inject 3–5 synthetic change-points at random dates with controlled parameters: mean shifts, variance shifts, and combined shifts; systematically vary noise distributions (Gaussian vs. Student-t with df=3) and SNR levels.
- **Algorithm implementation**: Execute four CPD methods using open-source libraries (`ruptures`, `changepoint`, `bayesian_changepoint_detection`) with standardized hyper-parameters: PELT, Binary Segmentation, Bayesian Online CPD, and Kernel-based CPD.
- **Performance evaluation**: Compute precision, recall, and F1-scores by comparing detected change-points to synthetic ground-truth within a ±5-day tolerance window; record wall-clock runtime for each method.
- **Statistical analysis**: Fit linear mixed-effects models with method, noise type, SNR, and overlap as fixed effects and time series ID as a random effect to isolate the influence of each statistical property on accuracy.
- **Robustness testing**: Conduct paired Wilcoxon signed-rank tests to determine if performance differences between methods are statistically significant across each stress condition (α = 0.05).
- **Independent validation**: Validate the robustness conclusions by re-running the analysis on a subset of series with injected synthetic breaks but *without* heavy-tailed noise to establish a baseline, ensuring the observed degradation is specifically due to the noise properties and not the detection algorithm's inherent limitations.
- **Reproducibility**: Package all code in a single Python/R workflow compatible with GitHub Actions free-tier runners (2 CPU, 7GB RAM), ensuring the full pipeline (download to analysis) completes within 6 hours.

## Duplicate-check

- Reviewed existing ideas: *(none)*.
- Closest match: *(none)*.
- Verdict: **NOT a duplicate**.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-08-25T21:15:53Z
**Outcome**: success
**Original term**: Robustness of Change‑Point Detection Methods on Public Financial Time Series statistics
**Verified citation count**: 11

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Robustness of Change‑Point Detection Methods on Public Financial Time Series statistics | 11 |

### Verified citations

1. **Multiple Change Point Detection and Validation in Autoregressive Time Series Data** (2019). Lijing Ma, Andrew Grant, Georgy Sofronov. arXiv. [1912.07775](https://arxiv.org/abs/1912.07775). PDF-sampled: No.
2. **Maximally Divergent Intervals for Anomaly Detection** (2016). Erik Rodner, Björn Barz, Yanira Guanche, Milan Flach, Miguel Mahecha, et al.. arXiv. [1610.06761](https://arxiv.org/abs/1610.06761). PDF-sampled: No.
3. **Bayesian Online Change Point Detection for Baseline Shifts** (2022). Ginga Yoshizawa. arXiv. [2201.02325](https://arxiv.org/abs/2201.02325). PDF-sampled: No.
4. **Confirmatory Bayesian Online Change Point Detection in the Covariance Structure of Gaussian Processes** (2019). Jiyeon Han, Kyowoon Lee, Anh Tong, Jaesik Choi. arXiv. [1905.13168](https://arxiv.org/abs/1905.13168). PDF-sampled: No.
5. **On High-Dimensional Change-Point Detection Based on Pairwise Distances** (2025). Spandan Ghoshal, Bilol Banerjee, Anil K. Ghosh. arXiv. [2511.10078](https://arxiv.org/abs/2511.10078). PDF-sampled: No.
6. **Equivalence relations and $L^p$ distances between time series with application to the Black Summer Australian bushfires** (2020). Nick James, Max Menzies. arXiv. [2002.02592](https://arxiv.org/abs/2002.02592). PDF-sampled: No.
7. **Data Segmentation for Time Series Based on a General Moving Sum Approach** (2022). Claudia Kirch, Kerstin Reckruehm. arXiv. [2207.07396](https://arxiv.org/abs/2207.07396). PDF-sampled: No.
8. **Asymptotic nonparametric statistical analysis of stationary time series** (2019). Daniil Ryabko. arXiv. [1904.00173](https://arxiv.org/abs/1904.00173). PDF-sampled: No.
9. **Optimal multiple change-point detection for high-dimensional data** (2020). Emmanuel Pilliat, Alexandra Carpentier, Nicolas Verzelen. arXiv. [2011.07818](https://arxiv.org/abs/2011.07818). PDF-sampled: No.
10. **Some Clustering-based Change-point Detection Methods Applicable to High Dimension, Low Sample Size Data** (2021). Trisha Dawn, Angshuman Roy, Alokesh Manna, Anil K. Ghosh. arXiv. [2111.14012](https://arxiv.org/abs/2111.14012). PDF-sampled: No.
11. **Asymptotic Distribution-free Change-point Detection for Modern Data Based on a New Ranking Scheme** (2022). Doudou Zhou, Hao Chen. arXiv. [2206.03038](https://arxiv.org/abs/2206.03038). PDF-sampled: No.
