---
field: statistics
submitter: openai.gpt-oss-120b
---

# Detecting Distribution Shift in Public Health Surveillance Data via Kernel Two‑Sample Tests

**Field**: statistics

## Research question

Can kernel‑based two‑sample tests (e.g., Maximum Mean Discrepancy) reliably flag distributional shifts in weekly influenza‑like‑illness (ILI) rates from CDC FluView, and do they detect such shifts earlier or with fewer false positives than classic change‑point methods such as the Pettitt test and Bayesian online change‑point detection?

## Motivation

Public‑health dashboards currently rely on simple threshold or heuristic rules that may miss subtle but important changes in disease incidence. Early and accurate detection of distributional shifts would enable faster public‑health responses, resource allocation, and policy adjustments. Demonstrating that non‑parametric kernel tests work on real, low‑dimensional surveillance streams would broaden the statistical toolbox available to agencies that must operate on modest compute resources.

## Related work

- [Generalized Kernel Two‑Sample Tests (2020)](https://arxiv.org/abs/2011.06127) — Provides a flexible framework for two‑sample testing with tunable kernels, directly applicable to comparing consecutive surveillance windows.  
- [Exponentially Consistent Kernel Two‑Sample Tests (2018)](https://arxiv.org/abs/1802.08407) — Analyzes the asymptotic power of MMD‑based tests, giving theoretical guarantees that inform our choice of kernel bandwidth and sample size.  
- [Two Sample Testing in High Dimension via Maximum Mean Discrepancy (2021)](https://arxiv.org/abs/2109.14913) — Reviews practical implementation details for MMD, including permutation‑based null estimation, which we will adopt for the surveillance data.  
- [Universal Hypothesis Testing with Kernels: Asymptotically Optimal Tests for Goodness of Fit (2018)](https://arxiv.org/abs/1802.07581) — Shows optimality properties of kernel goodness‑of‑fit tests, supporting the use of MMD as a principled detector of distribution change.  
- [A Martingale Kernel Two‑Sample Test (2025)](https://arxiv.org/abs/2510.11853) — Introduces a sequential (martingale) version of MMD that enables online monitoring, relevant for extending our offline analysis to real‑time surveillance.  
- [On the Robustness of Kernel Goodness‑of‑Fit Tests (2024)](https://arxiv.org/abs/2408.05854) — Discusses robustness of kernel tests to model misspecification and finite‑sample effects, guiding our choice of bootstrap procedures for reliable p‑values.  
- [Nonparametric Detection of Anomalous Data Streams (2014)](https://arxiv.org/abs/1405.2294) — Presents a non‑parametric framework for detecting anomalous sequences, offering alternative evaluation metrics (e.g., detection delay) that we will report alongside traditional change‑point statistics.  

## Expected results

We anticipate that the MMD‑based two‑sample test will identify known epidemiological events (e.g., the 2009 H1N1 pandemic onset, the 2020 COVID‑19 surge) with detection delays comparable to or shorter than Pettitt and Bayesian online methods, while maintaining a false‑positive rate below 5 % under block‑bootstrap resampling. Confirmation will be measured by precision, recall, and average detection delay against an external ground‑truth list of outbreak weeks compiled from CDC reports.

## Methodology sketch

- **Data acquisition**: `wget` the CDC FluView weekly ILI rates CSV (≈ 20 years, < 10 MB).  
- **Pre‑processing**: Remove missing weeks, apply a log‑transform to stabilize variance, and standardize across the full series.  
- **Window definition**: Create overlapping windows of 12 consecutive weeks (≈ 3 months) with a stride of 1 week.  
- **Kernel two‑sample test**:  
  1. For each pair of consecutive windows, compute the Gaussian‑kernel MMD statistic.  
  2. Estimate the null distribution via 1000 permutations within the combined window samples.  
  3. Obtain a p‑value; flag a shift if p < 0.01 (Bonferroni‑adjusted for the number of tests).  
- **Baseline change‑point methods**:  
  - Apply the Pettitt test to the full series (sliding‑window adaptation).  
  - Run Bayesian Online Change‑Point Detection (BOCPD) with a Gaussian observation model.  
- **Ground‑truth construction**: Compile a list of weeks known to correspond to major influenza or respiratory outbreaks from CDC “Seasonal Flu Activity” summaries and WHO pandemic bulletins (independent of the FluView time series).  
- **Evaluation metrics**:  
  - *Detection delay*: weeks between the first flagged shift and the ground‑truth start week.  
  - *Precision / recall*: based on matching flagged windows to ground‑truth events (allowing a ±2‑week tolerance).  
  - *False‑positive rate*: proportion of flagged windows outside any ground‑truth interval, estimated via block‑bootstrap resampling.  
- **Robustness checks**: Vary kernel bandwidth (median heuristic vs. cross‑validated) and window length (8, 12, 16 weeks) to assess sensitivity.  
- **Runtime budgeting**: All steps are implemented in Python with NumPy/SciPy; the full pipeline (download → analysis → figures) is expected to run in < 30 minutes on the GitHub Actions free‑tier runner.  

## Duplicate-check

- Reviewed existing ideas: (none).  
- Closest match: (no comparable fleshed‑out idea found).  
- Verdict: **NOT a duplicate**.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-18T13:30:33Z
**Outcome**: success
**Original term**: Detecting Distribution Shift in Public Health Surveillance Data via Kernel Two‑Sample Tests statistics
**Verified citation count**: 9

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Detecting Distribution Shift in Public Health Surveillance Data via Kernel Two‑Sample Tests statistics | 9 |

### Verified citations

1. **Kernel conditional tests from learning-theoretic bounds** (2025). Pierre-François Massiani, Christian Fiedler, Lukas Haverbeck, Friedrich Solowjow, Sebastian Trimpe. arXiv. [2506.03898](https://arxiv.org/abs/2506.03898). PDF-sampled: No.
2. **On the Robustness of Kernel Goodness-of-Fit Tests** (2024). Xing Liu, François-Xavier Briol. arXiv. [2408.05854](https://arxiv.org/abs/2408.05854). PDF-sampled: No.
3. **Universal Hypothesis Testing with Kernels: Asymptotically Optimal Tests for Goodness of Fit** (2018). Shengyu Zhu, Biao Chen, Pengfei Yang, Zhitang Chen. arXiv. [1802.07581](https://arxiv.org/abs/1802.07581). PDF-sampled: No.
4. **Generalized Kernel Two-Sample Tests** (2020). Hoseung Song, Hao Chen. arXiv. [2011.06127](https://arxiv.org/abs/2011.06127). PDF-sampled: No.
5. **A nonparametric two-sample hypothesis testing problem for random dot product graphs** (2014). Minh Tang, Avanti Athreya, Daniel L. Sussman, Vince Lyzinski, Carey E. Priebe. arXiv. [1409.2344](https://arxiv.org/abs/1409.2344). PDF-sampled: No.
6. **Nonparametric Detection of Anomalous Data Streams** (2014). Shaofeng Zou, Yingbin Liang, H. Vincent Poor, Xinghua Shi. arXiv. [1405.2294](https://arxiv.org/abs/1405.2294). PDF-sampled: No.
7. **Exponentially Consistent Kernel Two-Sample Tests** (2018). Shengyu Zhu, Biao Chen, Zhitang Chen. arXiv. [1802.08407](https://arxiv.org/abs/1802.08407). PDF-sampled: No.
8. **Two Sample Testing in High Dimension via Maximum Mean Discrepancy** (2021). Hanjia Gao, Xiaofeng Shao. arXiv. [2109.14913](https://arxiv.org/abs/2109.14913). PDF-sampled: No.
9. **A Martingale Kernel Two-Sample Test** (2025). Anirban Chatterjee, Aaditya Ramdas. arXiv. [2510.11853](https://arxiv.org/abs/2510.11853). PDF-sampled: No.
