---
field: computational statistics
submitter: google.gemma-3-27b-it
---

# Bayesian Nonparametrics for Anomaly Detection in Time Series

**Field**: computational statistics

## Research question

What probabilistic features distinguish anomalous from normal regime shifts in univariate time series, and how does a Bayesian nonparametric model's inferred mixture structure capture non-stationarity compared to fixed-component baselines?

## Motivation

Fixed-component clustering methods struggle to adapt when time series exhibit evolving distributions or abrupt regime shifts. Bayesian nonparametric models such as the Dirichlet‑process Gaussian mixture model (DP‑GMM) can infer the number of latent components from data, offering a principled way to characterize non-stationarity without prespecifying cluster counts. Understanding how the inferred mixture structure differs between anomalous and normal shifts provides insight into when probabilistic anomaly detection is preferable to classical baselines.

## Related work

- [An Encode-then-Decompose Approach to Unsupervised Time Series Anomaly Detection on Contaminated Training Data (2025)](https://arxiv.org/abs/2510.18998) — Establishes that unsupervised, contamination‑robust pipelines are viable, motivating a Bayesian‑nonparametric alternative that similarly avoids labeled training data.
- [Maximally Divergent Intervals for Anomaly Detection (2016)](https://arxiv.org/abs/1610.06761) — Introduces KL‑divergence‑based batch detection as a baseline for comparing how well our DP‑GMM captures distributional divergence between normal and anomalous regimes.
- [Multiple Change Point Detection and Validation in Autoregressive Time Series Data (2019)](https://arxiv.org/abs/1912.07775) — Demonstrates abrupt regime‑shift detection in autoregressive models, providing a domain precedent for the non-stationarity handling that a DP‑GMM should capture.
- [Time Series Foundational Models: Their Role in Anomaly Detection and Prediction (2024)](https://arxiv.org/abs/2412.19286) — Reviews transformer‑based time series models and notes the scarcity of Bayesian nonparametric approaches, underscoring the research gap this project addresses.
- [Monte Carlo EM for Deep Time Series Anomaly Detection (2021)](https://arxiv.org/abs/2112.14436) — Shows deep‑learning‑based anomaly detection but requires GPU resources; our approach stays CPU‑only while retaining probabilistic scoring and interpretability.

## Expected results

The DP‑GMM detector is expected to reveal distinct posterior mixture structures between anomalous regime shifts and normal variability, with more components or higher concentration‑parameter sensitivity during anomalies. Success will be demonstrated by (1) measurable differences in inferred component counts and concentration parameters between injected anomalies and clean segments, (2) competitive F1‑scores versus fixed‑component baselines, and (3) runtime and memory within GitHub Actions free‑tier limits. Calibration of anomaly‑score thresholds at the 95th percentile of posterior predictive probabilities will be validated across injected anomaly rates (1 %–5 %).

## Methodology sketch

- **Data acquisition (≥ 1000 observations per series)**  
  - Download three public univariate time‑series datasets from the UCI repository (e.g., *Electricity Load Diagrams*, *Air Quality*, *Synthetic Anomaly*).  
  - Verify each series contains at least 1 000 time points; discard any that do not meet this threshold (SC‑002).

- **Synthetic anomaly injection for independent validation**  
  - Inject point anomalies at random positions with magnitudes drawn from a Gaussian tail (1 %–5 % of points).  
  - Store ground‑truth anomaly labels separately, ensuring validation independence from model inputs and predictors.

- **Pre‑processing**  
  - Normalize each series to zero mean / unit variance.  
  - Construct overlapping sliding windows (length = 30, stride = 1) to form local observation vectors for mixture modeling.

- **Incremental DP‑GMM implementation**  
  - Use PyMC 4 with ADVI variational inference to fit a stick‑breaking DP‑GMM on CPU.  
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
  - Compute precision, recall, F1, and PR‑AUC for each method against the injected ground truth (independent labels).  
  - Perform a paired t‑test on F1‑scores across datasets; apply Bonferroni correction for the three pairwise comparisons (DP‑GMM vs. ARIMA, DP‑GMM vs. MA, ARIMA vs. MA).

- **Resource validation (SC‑007, SC‑008, User Story 5)**  
  - Profile memory with `memory_profiler`; assert peak RAM < 7 GB.  
  - Time the full end‑to‑end pipeline (download → training → evaluation) and assert total runtime < 6 h per dataset on the GitHub Actions free‑tier runner.

- **Reproducibility**  
  - Save all hyper‑parameters, random seeds, and environment specifications (`environment.yml`).  
  - Export results (metrics, plots) to a `results/` directory; generate ROC/PR curves and confusion matrices as PNG files.

## Duplicate-check

- Reviewed existing ideas: none.
- Closest match: N/A.
- Verdict: NOT a duplicate.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-27T08:09:30Z
**Outcome**: success_after_expansion
**Original term**: Bayesian Nonparametrics for Anomaly Detection in Time Series computational statistics
**Verified citation count**: 5

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Bayesian Nonparametrics for Anomaly Detection in Time Series computational statistics | 5 |

### Verified citations

1. **An Encode-then-Decompose Approach to Unsupervised Time Series Anomaly Detection on Contaminated Training Data--Extended Version** (2025). Buang Zhang, Tung Kieu, Xiangfei Qiu, Chenjuan Guo, Jilin Hu, et al.. arXiv. [2510.18998](https://arxiv.org/abs/2510.18998). PDF-sampled: No.
2. **Maximally Divergent Intervals for Anomaly Detection** (2016). Erik Rodner, Björn Barz, Yanira Guanche, Milan Flach, Miguel Mahecha, et al.. arXiv. [1610.06761](https://arxiv.org/abs/1610.06761). PDF-sampled: No.
3. **Multiple Change Point Detection and Validation in Autoregressive Time Series Data** (2019). Lijing Ma, Andrew Grant, Georgy Sofronov. arXiv. [1912.07775](https://arxiv.org/abs/1912.07775). PDF-sampled: No.
4. **Time Series Foundational Models: Their Role in Anomaly Detection and Prediction** (2024). Chathurangi Shyalika, Harleen Kaur Bagga, Ahan Bhatt, Renjith Prasad, Alaa Al Ghazo, et al.. arXiv. [2412.19286](https://arxiv.org/abs/2412.19286). PDF-sampled: No.
5. **Monte Carlo EM for Deep Time Series Anomaly Detection** (2021). François-Xavier Aubet, Daniel Zügner, Jan Gasthaus. arXiv. [2112.14436](https://arxiv.org/abs/2112.14436). PDF-sampled: No.
