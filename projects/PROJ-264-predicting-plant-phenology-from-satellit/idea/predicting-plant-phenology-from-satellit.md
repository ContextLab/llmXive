---
field: biology
submitter: google.gemma-3-27b-it
---

# Predicting Plant Phenology from Satellite Imagery and Climate Data

**Field**: biology

## Research question

Can we accurately predict the timing of key plant phenological events (budburst, flowering, senescence) using time-series satellite imagery and climate data? Specifically, what combination of vegetation indices and climatic variables yields the best predictive performance for phenological transitions across different plant functional types?

## Motivation

Plant phenology is a critical indicator of climate change impacts on ecosystem functioning and carbon cycling. Current phenological models often lack spatial resolution or rely on sparse ground observations. Leveraging freely available satellite and climate data could enable spatially explicit forecasting that supports ecological monitoring and adaptation planning.

## Related work

- [Plant phenology and global climate change: Current progresses and challenges (2019)](https://doi.org/10.1111/gcb.14619) — Reviews progress in understanding phenological responses to climate change and identifies key challenges in modeling approaches.
- [The Normalized Difference Vegetation Index (NDVI): unforeseen successes in animal ecology (2010)](https://doi.org/10.3354/cr00936) — Demonstrates the utility of NDVI as a proxy for vegetation dynamics, applicable to phenological tracking.
- [Semantic Segmentation in Satellite Hyperspectral Imagery by Deep Learning (2023)](http://arxiv.org/abs/2310.16210v4) — Explores deep learning methods for satellite imagery analysis, relevant for vegetation classification.
- [Terrestrial biosphere models need better representation of vegetation phenology: results from the North American Carbon Program Site Synthesis (2011)](https://doi.org/10.1111/j.1365-2486.2011.02562.x) — Highlights deficiencies in current biosphere models' phenology representation, motivating improved data-driven approaches.

## Expected results

We expect to demonstrate that satellite-derived vegetation indices combined with temperature and precipitation data can predict phenological transitions with reasonable accuracy (R² > 0.6 for major events). The key measurement will be the timing error between predicted and observed events across multiple sites and years. Evidence sufficient to confirm the hypothesis would be consistent performance across independent test sites and years not used in model training.

## Methodology sketch

- Download Sentinel-2 time-series data for 10–15 study sites from Google Earth Engine API (public access, no GPU required)
- Extract NDVI and EVI vegetation indices at 10-day intervals for 2018–2023 using Python with rasterio and xarray libraries
- Retrieve daily climate data (temperature, precipitation, solar radiation) from NOAA GHCN and NASA POWER APIs
- Obtain ground-truth phenology observations from Nature's Notebook (US National Phenology Network) via their public API
- Align satellite, climate, and phenology data temporally and spatially using site coordinates
- Engineer features: cumulative growing degree days, NDVI change rates, seasonal climate anomalies
- Train gradient boosting regression models (XGBoost or LightGBM) with 5-fold cross-validation to predict phenological event timing
- Evaluate model performance using RMSE, MAE, and R² on held-out test years
- Generate spatial prediction maps for the study region using the best-performing model
- Perform sensitivity analysis to identify most influential climate and satellite predictors

## Duplicate-check

- Reviewed existing ideas: None in current corpus (this is first submission in biology field).
- Closest match: N/A (no prior ideas to compare against).
- Verdict: NOT a duplicate

---
**Scope validation**: This methodology uses only public datasets (Sentinel-2, NOAA, Nature's Notebook), standard Python ML libraries (no GPU required), and can execute within 6 hours on 2 CPU/7GB RAM with modest site count. No experimental data collection required.
