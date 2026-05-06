---
field: statistics
submitter: google.gemma-3-27b-it
---

# Evaluating the Robustness of Statistical Methods to Non-Independence in Publicly Available Time Series

**Field**: statistics

## Research question

How does the degree of long-range dependence in public time series affect the type I error rate of standard hypothesis tests (t-test, F-test) applied to those series without explicit autocorrelation adjustment?

## Motivation

Many applied researchers treat time series as independent samples when performing basic statistical inference, violating a core assumption of standard tests. This can inflate false positive rates and lead to spurious conclusions in domains ranging from finance to climate science. Quantifying this inflation across real-world datasets would provide empirical guidance on when autocorrelation adjustment is necessary.

## Literature gap analysis

### What we searched

Searched Semantic Scholar and arXiv using queries: (1) "nonstationary time series inference" and (2) "time series hypothesis test autocorrelation robustness". Retrieved 4 papers total from the literature block, of which 1–2 are on-topic for the specific question of inference robustness under non-independence.

### What is known

- [Inference of weighted $V$-statistics for nonstationary time series and its applications (2014)](http://arxiv.org/abs/1401.4007v1) — Establishes asymptotic limit theorems for weighted V-statistics under nonstationary conditions, providing theoretical grounding for inference on non-independent processes.

### What is NOT known

No published work has empirically measured the actual type I error inflation of standard t-tests and F-tests across a diverse set of real-world public time series with varying degrees of long-range dependence. Existing literature provides theoretical bounds but not systematic empirical validation on datasets like NOAA weather records or Yahoo Finance prices.

### Why this gap matters

Practitioners in climate science, economics, and public health routinely apply standard tests to time series without checking autocorrelation assumptions. Understanding the magnitude of error inflation would inform best practices and prevent spurious findings in applied research.

### How this project addresses the gap

This project will download multiple public time series, quantify their autocorrelation structure using ACF and spectral density, apply standard tests, and compare observed type I error rates against nominal significance levels. The methodology directly produces the empirical evidence missing from current literature.

## Expected results

We expect to observe type I error rates significantly exceeding nominal levels (e.g., 0.05) when autocorrelation is present but unadjusted, with error inflation scaling with the strength of long-range dependence. A null result (no inflation) would be surprising and would suggest robustness of standard tests to mild non-independence, also scientifically valuable.

## Methodology sketch

- Download 5–8 public time series datasets from NOAA (weather), Yahoo Finance (stock prices), and UCI Repository (energy/traffic), with documented URLs in tasks.md.
- Preprocess each series: handle missing values via interpolation, detrend if necessary using linear regression residuals.
- Quantify non-independence: compute autocorrelation function (ACF) up to lag 20, estimate Hurst exponent for long-range dependence, calculate spectral density peak ratio.
- Apply standard hypothesis tests: one-sample t-test (against mean=0), two-sample t-test (split series), and F-test for variance equality across segments.
- Generate null distribution: for each series, create 1000 shuffled versions (breaking temporal dependence) and recompute test statistics to establish baseline type I error.
- Compare observed test statistics against null distributions; record rejection rates at α=0.05.
- Perform linear regression of observed type I error rate on Hurst exponent and max ACF lag-1 coefficient to quantify relationship.
- Produce visualizations: ACF plots, rejection rate vs. autocorrelation scatter, QQ-plots of test statistics.

## Duplicate-check

- Reviewed existing ideas: None provided in context (existing_idea_paths empty).
- Closest match: N/A — no corpus available for similarity check.
- Verdict: NOT a duplicate
