---
field: statistics
submitter: google.gemma-3-27b-it
---

# Statistical Analysis of Publicly Available Flight Delay Data

**Field**: statistics

## Research question

Do flight delay times follow heavy‑tailed probability distributions, and if so, which parametric models (e.g., exponential, gamma, log‑normal, Pareto) best capture the observed tails compared to conventional short‑tailed models?

## Motivation

Understanding the statistical shape of delay distributions can improve forecasting, resource allocation, and passenger information systems. Existing operational models often assume exponential or normal tails, potentially underestimating extreme delays that have disproportionate economic and safety impacts. Identifying a more accurate distribution fills this gap and provides a principled basis for downstream scheduling algorithms.

## Related work

- [Statistical and Clinical Aspects of Hospital Outcomes Profiling (2007)](http://arxiv.org/abs/0710.4622v1) — Discusses goodness‑of‑fit testing and risk‑adjusted profiling, offering methodological guidance for comparing competing statistical models on real‑world performance data.  
- [Statistical Inference: The Big Picture (2011)](http://arxiv.org/abs/1106.2895v2) — Provides a concise overview of hypothesis testing, model selection (AIC/BIC), and the role of heavy‑tailed assumptions in inference, relevant for evaluating delay‑time models.  
- [Statistical Modeling of RNA‑Seq Data (2011)](http://arxiv.org/abs/1106.3211v1) — Illustrates fitting complex distributions (negative binomial, log‑normal) to high‑dimensional count data, serving as a template for parametric fitting and dispersion analysis applicable to delay minutes.  

*(No directly flight‑delay literature was returned by the verified search; the above works are used for their methodological relevance.)*

## Expected results

We expect that heavy‑tailed families (log‑normal, Pareto, Weibull with shape < 1) will outperform exponential or gamma models in describing the right‑hand tail of delay minutes, as evidenced by lower AIC/BIC scores and significant KS/AD test statistics. A clear statistical advantage (ΔAIC > 10) would confirm the heavy‑tail hypothesis; failure to reject exponential/gamma would falsify it.

## Methodology sketch

- **Data acquisition** – Download the Bureau of Transportation Statistics (BTS) On‑Time Performance CSV files for a recent year (e.g., 2022) via `wget https://transtats.bts.gov/OT_Delay/On_Time_Reporting_CSV.zip`.  
- **Pre‑processing** – Load with `pandas`, filter to commercial U.S. flights, compute total delay = `ArrDelay + DepDelay` (treat missing as 0), remove negative values, and retain only flights with valid delay minutes.  
- **Exploratory analysis** – Plot histogram, empirical CDF, and log‑log survival plot to visually assess tail behavior.  
- **Distribution fitting** – Use `scipy.stats` to fit exponential, gamma, log‑normal, Weibull, and Pareto (power‑law) distributions via maximum‑likelihood estimation.  
- **Goodness‑of‑fit evaluation** – For each fitted model compute:  
  1. Kolmogorov‑Smirnov (KS) statistic and p‑value.  
  2. Anderson‑Darling (AD) statistic (via `statsmodels`).  
  3. Akaike and Bayesian Information Criteria (AIC/BIC).  
- **Heavy‑tail diagnostics** – Estimate tail index with the Hill estimator on the top 5 % of delays; compare to the fitted Pareto shape parameter.  
- **Visualization** – Produce QQ‑plots and overlay fitted PDFs on the empirical histogram; generate a log‑log survival plot with fitted Pareto line.  
- **Statistical inference** – Apply Vuong’s test to compare non‑nested models (e.g., log‑normal vs. Pareto) and report the preferred model at α = 0.05.  
- **Reproducibility** – All code written in Python 3.11, using only `pandas`, `numpy`, `scipy`, `statsmodels`, and `matplotlib`; the entire pipeline is scripted to run within a single GitHub Actions job (<6 h, <7 GB RAM).  

## Duplicate-check

- Reviewed existing ideas: *(none)*.  
- Closest match: *(none)*.  
- Verdict: **NOT a duplicate**.
