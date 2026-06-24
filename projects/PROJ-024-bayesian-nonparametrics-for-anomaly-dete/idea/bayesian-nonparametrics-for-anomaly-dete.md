---
field: computational statistics
submitter: google.gemma-3-27b-it
---

# Bayesian Nonparametrics for Anomaly Detection in Time Series

**Field**: computational statistics

## Research question

Can an incrementally updated Dirichlet‑process Gaussian mixture model (DP‑GMM) detect anomalies in univariate time‑series streams without pre‑specifying the number of latent mixture components?

## Motivation

Many existing anomaly‑detection pipelines require a fixed number of clusters or assume stationary distributions, which limits adaptability to evolving data streams. Bayesian non‑parametric models such as the DP‑GMM automatically infer the appropriate number of mixture components and provide probabilistic anomaly scores, offering a principled way to handle non‑stationarity while keeping the hyper‑parameter burden low.

## Related work

- [An Encode‑then‑Decompose Approach to Unsupervised Time Series Anomaly Detection on Contaminated Training Data (2025)](https://arxiv.org/abs/2510.18998) — Shows that unsupervised, contamination‑robust pipelines can achieve strong detection performance, motivating a Bayesian‑non‑parametric alternative that is also unsupervised.  
- [Maximally Divergent Intervals for Anomaly Detection (2016)](https://arxiv.org/abs/1610.06761) — Introduces KL‑divergence‑based batch detection; provides a useful baseline metric for comparing our online DP‑GMM scores.  
- [Multiple Change Point Detection and Validation in Autoregressive Time Series Data (2019)](https://arxiv.org/abs/1912.07775) — Discusses change‑point detection in AR models, highlighting the need for methods that can adapt to abrupt regime shifts—exactly what a DP‑GMM can capture.  
- [Time Series Foundational Models: Their Role in Anomaly Detection and Prediction (2024)](https://arxiv.org/abs/2412.19286) — Reviews modern transformer‑based TSFMs and notes the scarcity of Bayesian non‑parametric approaches, underscoring the research gap.  
- [Monte Carlo EM for Deep Time Series Anomaly Detection (2021)](https://arxiv.org/abs/2112.14436) — Demonstrates deep‑learning‑based inference but requires GPUs; our approach stays within CPU‑only constraints while retaining probabilistic scoring.

## Expected results

The DP‑GMM detector is expected to achieve F1‑scores comparable to or better than strong baselines (moving‑average z‑score, ARIMA) on public univariate benchmarks, while using fewer hand‑tuned hyper‑parameters. Success will be demonstrated by (1) higher precision‑recall AUC, (2) runtime < 30 min per dataset, and (3) peak memory consumption < 7 GB. Calibration of the anomaly‑score threshold at the 95th percentile of the posterior‑probability distribution will be validated across injected anomaly rates (1 %–5 %).

## Methodology sketch

- **Data acquisition (≥ 1000 observations per series)**  
  - Download three public univariate time‑series datasets from the UCI repository (e.g., *Electricity Load Diagrams*, *Air Quality*, *Synthetic Anomaly*).  
  - Verify each series contains at least 1 000 time points; discard any that do not meet this threshold (SC‑002).  

- **Synthetic anomaly injection for independent validation**  
  - Inject point anomalies at random positions with magnitudes drawn from a Gaussian tail (1 %–5 % of points).  
  - Ground‑truth anomaly labels are stored separately, ensuring validation independence from model inputs.  

- **Pre‑processing**  
  - Normalize each series to zero mean / unit variance.  
  - Construct overlapping sliding windows (length = 30, stride = 1) to form local observation vectors.  

- **Incremental DP‑GMM implementation**  
  - Use PyMC 4 with ADVI variational inference to fit a stick‑breaking DP‑GMM.  
  - After each new window, update the posterior mixture weights online (streaming mode).  
  - Constrain the number of mixture components implicitly via the concentration parameter α.  

- **Prior‑sensitivity analysis (FR‑024)**  
  - Run the model with three α‑grid values (0.1, 1.0, 10.0) and corresponding Gamma hyper‑priors for component covariances.  
  - Record ELBO trajectories; report mean and variance across runs.  

- **ELBO variance exclusion (FR‑025)**  
  - Exclude ELBO variance from the final performance metric; instead, use the stabilized ELBO mean after convergence as a model‑fit indicator.  

- **Anomaly‑score computation & threshold calibration (SC‑010)**  
  - Compute the negative log posterior predictive probability for each new observation.  
  - Calibrate a static threshold at the 95th percentile of scores on a held‑out clean segment.  
  - Implement an adaptive update: after every 500 observations, recompute the percentile on the most recent clean window.  

- **Baseline models**  
  - Fit ARIMA (using `statsmodels`) and a moving‑average z‑score detector (window = 30) on the same streams.  

- **Performance evaluation**  
  - Compute precision, recall, F1, and PR‑AUC for each method against the injected ground truth.  
  - Perform a paired t‑test on F1‑scores across datasets; apply Bonferroni correction for the three pairwise comparisons (DP‑GMM vs. ARIMA, DP‑GMM vs. MA, ARIMA vs. MA).  

- **Resource validation (SC‑007, SC‑008, User Story 5)**  
  - Profile memory with `memory_profiler`; assert peak RAM < 7 GB.  
  - Time the full end‑to‑end pipeline (download → training → evaluation) and assert total runtime < 30 min per dataset on the GitHub Actions free‑tier runner.  

- **Reproducibility**  
  - Save all hyper‑parameters, random seeds, and environment specifications (`environment.yml`).  
  - Export results (metrics, plots) to a `results/` directory; generate ROC/PR curves and confusion matrices as PNG files.  

## Duplicate-check

- Reviewed existing ideas: none.
- Closest match: N/A.
- Verdict: NOT a duplicate.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-24T18:40:49Z
**Outcome**: success_after_expansion
**Original term**: Bayesian Nonparametrics for Anomaly Detection in Time Series computational statistics
**Verified citation count**: 5

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Bayesian Nonparametrics for Anomaly Detection in Time Series computational statistics | 0 |
| 1 | Dirichlet process mixture models for time‑series anomaly detection | 5 |
| 2 | Infinite hidden Markov models for temporal outlier identification | 0 |
| 3 | Gaussian process change‑point detection in streaming data | 0 |
| 4 | Nonparametric Bayesian change‑point models for fault detection | 0 |
| 5 | Hierarchical Dirichlet process clustering of multivariate time series anomalies | 0 |
| 6 | Bayesian nonparametric state‑space models for anomaly scoring | 0 |
| 7 | Stick‑breaking process priors for online anomaly detection in temporal data | 0 |
| 8 | Chinese restaurant process for sequential outlier detection | 0 |
| 9 | Adaptive Bayesian nonparametric models for streaming time‑series monitoring | 0 |
| 10 | Bayesian nonparametric density estimation for anomaly ranking in temporal datasets | 0 |
| 11 | Sequential Monte Carlo inference for Bayesian nonparametric anomaly detectors | 0 |
| 12 | Bayesian nonparametric regression approaches to time‑series outlier detection | 0 |
| 13 | Nonparametric Bayesian forecasting methods for early anomaly warning | 0 |
| 14 | Bayesian nonparametric process‑control charts for temporal quality monitoring | 0 |
| 15 | Bayesian nonparametric kernel methods for detecting anomalies in sensor time series | 0 |

### Verified citations

1. **An Encode-then-Decompose Approach to Unsupervised Time Series Anomaly Detection on Contaminated Training Data--Extended Version** (2025). Buang Zhang, Tung Kieu, Xiangfei Qiu, Chenjuan Guo, Jilin Hu, et al.. arXiv. [2510.18998](https://arxiv.org/abs/2510.18998). PDF-sampled: No.
2. **Maximally Divergent Intervals for Anomaly Detection** (2016). Erik Rodner, Björn Barz, Yanira Guanche, Milan Flach, Miguel Mahecha, et al.. arXiv. [1610.06761](https://arxiv.org/abs/1610.06761). PDF-sampled: No.
3. **Multiple Change Point Detection and Validation in Autoregressive Time Series Data** (2019). Lijing Ma, Andrew Grant, Georgy Sofronov. arXiv. [1912.07775](https://arxiv.org/abs/1912.07775). PDF-sampled: No.
4. **Time Series Foundational Models: Their Role in Anomaly Detection and Prediction** (2024). Chathurangi Shyalika, Harleen Kaur Bagga, Ahan Bhatt, Renjith Prasad, Alaa Al Ghazo, et al.. arXiv. [2412.19286](https://arxiv.org/abs/2412.19286). PDF-sampled: No.
5. **Monte Carlo EM for Deep Time Series Anomaly Detection** (2021). François-Xavier Aubet, Daniel Zügner, Jan Gasthaus. arXiv. [2112.14436](https://arxiv.org/abs/2112.14436). PDF-sampled: No.
