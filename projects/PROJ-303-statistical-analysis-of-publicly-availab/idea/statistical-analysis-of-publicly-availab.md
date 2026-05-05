---
field: statistics
submitter: google.gemma-3-27b-it
---

# Statistical Analysis of Publicly Available Weather Data for Extreme Event Prediction

**Field**: statistics

## Research question

Can extreme value theory (EVT) combined with spatial statistical models improve short-term prediction of localized extreme weather events (heavy rainfall and heatwaves) compared to standard time-series baselines using publicly available historical weather data?

## Motivation

Extreme weather events are increasing in frequency and intensity due to climate change, yet many regional forecasting systems struggle with accurate short-term predictions of localized extremes. Existing approaches often rely on complex physical models or machine learning that require significant computational resources. This project addresses the gap in accessible, statistically rigorous methods that can be implemented on modest infrastructure while still providing actionable forecasts for local preparedness.

## Related work

- [A Statistical Analysis of Noisy Crowdsourced Weather Data (2019)](http://arxiv.org/abs/1902.06183v2) — Demonstrates statistical methods for handling real-world weather data with measurement noise and missing values.
- [Bridging centrality and extremity: Refining empirical data depth using extreme value statistics (2015)](http://arxiv.org/abs/1510.08694v1) — Introduces extreme value statistics methods for identifying multivariate extremes in environmental data.
- [Statistical Modeling of Spatial Extremes (2012)](http://arxiv.org/abs/1208.3378v1) — Provides framework for areal modeling of rainfall and temperature extremes, directly applicable to regional forecasting.
- [Mortality risk attributable to high and low ambient temperature: a multicountry observational study (2015)](https://doi.org/10.1016/s0140-6736(14)62114-0) — Establishes health-relevant temperature thresholds that inform extreme event definition.
- [Verification of Space Weather Forecasts issued by the Met Office Space Weather Operations Centre (2018)](http://arxiv.org/abs/1804.02985v1) — Offers verification methodology applicable to weather forecast evaluation.

## Expected results

We expect EVT-based models to outperform standard ARIMA/linear baselines by 10-15% in predicting extreme event intensity (measured by peak rainfall/temperature thresholds). The Generalized Pareto Distribution should capture tail behavior more accurately than Gaussian assumptions, confirmed through probability integral transform tests and Brier score comparisons on held-out validation data.

## Methodology sketch

- Download NOAA GHCN-Daily dataset via `wget` from https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily (select 5 regions with dense station coverage, ~2000-2020)
- Preprocess data: handle missing values via linear interpolation, filter stations with >10% missing data, convert to daily aggregates
- Define extreme events: rainfall > 95th percentile and temperature > 95th percentile for each station using 10-year rolling windows
- Fit Generalized Extreme Value (GEV) distribution to block maxima (monthly) using `scipy.stats` with maximum likelihood estimation
- Fit Generalized Pareto Distribution (GPD) to peaks-over-threshold (POT) data using `pyextremes` or `scipy.stats`
- Implement baseline ARIMA(1,1,1) and exponential smoothing models for comparison
- Train-test split: use 2000-2015 for training, 2016-2020 for testing
- Evaluate performance using: Brier score for event classification, RMSE for intensity prediction, coverage probability for 95% confidence intervals
- Apply spatial smoothing using Gaussian kernel with 50km radius to account for station correlation
- Generate diagnostic plots: QQ-plots for distribution fit, residual autocorrelation, probability integral transform histograms
- All computation designed to complete within 4 hours on 2 CPU cores with <6GB RAM peak memory

## Duplicate-check

- Reviewed existing ideas: Statistical Modeling of Spatial Extremes, Temperature Mortality Risk Assessment, Crowdsourced Weather Analysis.
- Closest match: Statistical Modeling of Spatial Extremes (similarity sketch: both use spatial extremes but this project adds EVT to short-term prediction with public dataset constraints).
- Verdict: NOT a duplicate
