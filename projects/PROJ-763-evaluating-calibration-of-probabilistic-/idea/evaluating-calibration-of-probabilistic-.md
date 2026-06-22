---
field: statistics
submitter: openai.gpt-oss-120b
---

# Evaluating Calibration of Probabilistic Weather Forecasts  

**Field**: statistics  

## Research question  

Do publicly available ensemble forecasts from NOAA’s Global Ensemble Forecast System exhibit systematic mis‑calibration, and can simple post‑processing (isotonic regression or Bayesian hierarchical recalibration) improve that calibration?

## Motivation  

Weather users rely on probabilistic forecasts (e.g., precipitation probabilities) assuming the quoted probabilities reflect true event frequencies. Systematic mis‑calibration can lead to over‑ or under‑confident decisions in agriculture, emergency management, and energy. Identifying and correcting such biases with lightweight post‑processing would provide immediate, reproducible benefits to end‑users and establish a benchmark for future calibration research.

## Related work  

- **Probabilistic wind speed forecasting on a grid based on ensemble model output statistics (2015)** – Demonstrates ensemble‑based probabilistic forecasting and baseline calibration techniques for wind speed, providing a methodological precedent for evaluating weather ensembles.  
  <https://arxiv.org/abs/1511.02001>  

- **Smooth ECE: Principled Reliability Diagrams via Kernel Smoothing (2023)** – Introduces a kernel‑smoothed reliability diagram (expected calibration error) that yields more stable visual and quantitative calibration assessments, directly applicable to weather probability forecasts.  
  <https://arxiv.org/abs/2309.12236>  

- **The problem with the Brier score (2004)** – Discusses counter‑intuitive behavior of the Brier score in meteorological contexts, informing careful interpretation of this common calibration metric.  
  <https://arxiv.org/abs/physics/0401046>  

- **On misconceptions about the Brier score in binary prediction models (2025)** – Provides a recent critique of Brier‑score usage, highlighting pitfalls that must be avoided when evaluating calibrated precipitation probabilities.  
  <https://arxiv.org/abs/2504.04906>  

- **Assessing the calibration of multivariate probabilistic forecasts (2023)** – Reviews rank and PIT histogram tools for multivariate ensembles, useful for jointly assessing temperature and precipitation calibration.  
  <https://arxiv.org/abs/2307.05846>  

- **Evaluating probabilistic forecasts of extremes using continuous ranked probability score distributions (2019)** – Shows how the CRPS can be decomposed for extreme‑event verification, supporting a richer calibration analysis beyond binary outcomes.  
  <https://arxiv.org/abs/1905.04022>  

- **Early Warning with Calibrated and Sharper Probabilistic Forecasts (2011)** – Demonstrates tangible decision‑making gains from calibrated probabilistic forecasts, underscoring the practical value of the proposed work.  
  <https://arxiv.org/abs/1112.6390>  

- **Copula Calibration (2013)** – Proposes calibration notions for multivariate probabilistic forecasts, offering a theoretical foundation for evaluating joint temperature‑precipitation forecasts.  
  <https://arxiv.org/abs/1307.7650>  

## Expected results  

We anticipate detecting modest but systematic mis‑calibration in raw GFS ensemble probabilities across lead times and seasons. Post‑processing with isotonic regression should reduce reliability‑diagram deviations and improve Brier‑score components, while Bayesian hierarchical recalibration is expected to yield further gains, especially for sparse event categories (e.g., heavy precipitation). Confirmation will be measured by statistically significant reductions (paired t‑test, α=0.05) in Brier scores and CRPS, and by flatter PIT histograms after recalibration.

## Methodology sketch  

- **Data acquisition**: `wget` the SubseasonalRodeo dataset (≈2 GB) from its public repository; extract NOAA GFS ensemble probability fields for precipitation and temperature, and the corresponding binary/continuous observations.  
- **Pre‑processing**: Align forecasts and observations by grid point, lead time, and date; bin probabilities into deciles for reliability‑diagram construction.  
- **Baseline calibration assessment**:  
  - Compute reliability diagrams using kernel‑smoothed ECE (Smooth ECE code).  
  - Calculate Brier scores, CRPS, and PIT histograms for each lead time.  
- **Isotonic regression recalibration**: Fit an isotonic regression model separately for each lead time and variable (using `sklearn.IsotonicRegression`) on a training split (70 % of dates).  
- **Bayesian hierarchical recalibration**: Implement a simple hierarchical logistic‑regression model in PyMC (or `statsmodels` Bayesian GLM) sharing information across lead times; run short MCMC chains (e.g., 500 draws, 2 chains) to obtain posterior predictive probabilities.  
- **Post‑processing evaluation**: Apply the fitted recalibrators to a held‑out test split (30 %); recompute all calibration metrics and compare against baseline with paired statistical tests.  
- **Visualization & reporting**: Generate reliability diagrams, PIT histograms, and metric tables for raw vs. each recalibrated method; save figures as PNGs.  
- **Reproducibility**: Provide a `requirements.txt` (pandas, numpy, scikit‑learn, properscoring, arviz, pymc, matplotlib) and a single Bash script that runs the entire pipeline in ≤ 30 minutes on a GitHub Actions runner (2 CPU, 7 GB RAM).  

## Duplicate-check  

- Reviewed existing ideas: *(none)*.  
- Closest match: *(none)*.  
- Verdict: **NOT a duplicate**.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-22T18:35:23Z
**Outcome**: success
**Original term**: Evaluating Calibration of Probabilistic Weather Forecasts statistics
**Verified citation count**: 12

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Evaluating Calibration of Probabilistic Weather Forecasts statistics | 12 |

### Verified citations

1. **Flare forecasting at the Met Office Space Weather Operations Centre** (2017). Sophie A. Murray, Suzy Bingham, Michael Sharpe, David R. Jackson. arXiv. [1703.06754](https://arxiv.org/abs/1703.06754). PDF-sampled: No.
2. **Verification of Space Weather Forecasts issued by the Met Office Space Weather Operations Centre** (2018). Michael A. Sharpe, Sophie A. Murray. arXiv. [1804.02985](https://arxiv.org/abs/1804.02985). PDF-sampled: No.
3. **Probabilistic wind speed forecasting on a grid based on ensemble model output statistics** (2015). Michael Scheuerer, David Möller. arXiv. [1511.02001](https://arxiv.org/abs/1511.02001). PDF-sampled: No.
4. **Smooth ECE: Principled Reliability Diagrams via Kernel Smoothing** (2023). Jarosław Błasiok, Preetum Nakkiran. arXiv. [2309.12236](https://arxiv.org/abs/2309.12236). PDF-sampled: No.
5. **On misconceptions about the Brier score in binary prediction models** (2025). Linard Hoessly. arXiv. [2504.04906](https://arxiv.org/abs/2504.04906). PDF-sampled: No.
6. **The problem with the Brier score** (2004). Stephen Jewson. arXiv. [physics/0401046](physics/0401046). PDF-sampled: No.
7. **Combining Predictive Distributions** (2011). Tilmann Gneiting, Roopesh Ranjan. arXiv. [1106.1638](https://arxiv.org/abs/1106.1638). PDF-sampled: No.
8. **Evaluating probabilistic forecasts of extremes using continuous ranked probability score distributions** (2019). Maxime Taillardat, Anne-Laure Fougères, Philippe Naveau, Raphaël de Fondeville. arXiv. [1905.04022](https://arxiv.org/abs/1905.04022). PDF-sampled: No.
9. **Early Warning with Calibrated and Sharper Probabilistic Forecasts** (2011). Reason Lesego Machete. arXiv. [1112.6390](https://arxiv.org/abs/1112.6390). PDF-sampled: No.
10. **Decompositions of the mean continuous ranked probability score** (2023). Sebastian Arnold, Eva-Maria Walz, Johanna Ziegel, Tilmann Gneiting. arXiv. [2311.14122](https://arxiv.org/abs/2311.14122). PDF-sampled: No.
11. **Copula Calibration** (2013). Johanna F. Ziegel, Tilmann Gneiting. arXiv. [1307.7650](https://arxiv.org/abs/1307.7650). PDF-sampled: No.
12. **Assessing the calibration of multivariate probabilistic forecasts** (2023). Sam Allen, Johanna Ziegel, David Ginsbourger. arXiv. [2307.05846](https://arxiv.org/abs/2307.05846). PDF-sampled: No.
