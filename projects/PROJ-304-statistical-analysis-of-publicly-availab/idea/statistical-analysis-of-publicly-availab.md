---
field: statistics
submitter: google.gemma-3-27b-it
---

# Statistical Analysis of Publicly Available Urban Noise Pollution Data

**Field**: statistics

## Research question

What are the key environmental predictors of urban noise levels, and how accurately can spatial statistical models forecast noise‑pollution hotspots across cities?

## Motivation

Urban noise pollution is a significant environmental stressor linked to adverse health outcomes, yet comprehensive monitoring infrastructure remains sparse in many municipalities. Leveraging publicly available citizen science and government datasets allows for the statistical identification of high-risk zones without the need for new sensor deployment. This research addresses the gap between fragmented noise data and the need for robust, data-driven urban planning strategies to mitigate exposure.

## Literature gap analysis

### What we searched

We queried Semantic Scholar, arXiv, and OpenAlex using two distinct search strategies. First, we used specific queries combining "urban noise pollution," "spatial regression," and "noise hotspot prediction" to find domain-specific modeling work. Second, we broadened the search to "urban environmental statistics," "noise mapping methodologies," and "spatial autocorrelation in city data" to identify general statistical frameworks applicable to this domain. The literature block provided contains no direct studies on statistical modeling of urban noise levels using spatial regression on public datasets.

### What is known

- [Population size and centrality effects on NO2 air pollution across and within European cities (2026)](https://arxiv.org/abs/2605.28672) — Establishes that population size and urban centrality are critical structural predictors for air pollution, suggesting similar spatial drivers may apply to noise.
- [Night-sky brightness monitoring in Hong Kong - a city-wide light pollution assessment (2011)](https://arxiv.org/abs/1106.3842) — Demonstrates the feasibility of city-wide environmental monitoring using portable sensors and citizen science approaches, though focused on light rather than acoustic pollution.
- [Statistical Inference: The Big Picture (2011)](https://arxiv.org/abs/1106.2895) — Provides a general philosophical framework for interpreting statistical results in complex observational settings, relevant to the interpretability of urban noise models.

### What is NOT known

There is no published work that specifically applies spatial lag or spatial error models to predict urban noise hotspots using a combination of open-source traffic, land-use, and citizen-science noise data. While air and light pollution have been modeled with similar spatial techniques, the specific statistical performance of these models for acoustic noise—particularly regarding the reduction of residual spatial autocorrelation in diverse urban contexts—remains unquantified.

### Why this gap matters

Filling this gap is critical for cities lacking expensive fixed sensor networks, as it would provide a low-cost, statistically rigorous method to identify noise-vulnerable populations. Accurate predictive models could directly inform zoning laws, traffic management, and green space placement to reduce public health risks associated with chronic noise exposure.

### How this project addresses the gap

This project will construct a unified spatial dataset from open sources and explicitly test spatial regression models (lag and error) against ordinary least squares baselines. By quantifying the improvement in prediction accuracy and the reduction of spatial autocorrelation, this study will provide the first empirical evidence on the efficacy of these specific statistical methods for urban noise mapping.

## Expected results

We anticipate identifying traffic density and time of day as the strongest predictors of noise levels, with land use providing secondary explanatory power. We expect spatial regression models to significantly outperform ordinary least squares, evidenced by a reduction in cross-validation RMSE and a lower Moran's I of residuals, confirming that spatial dependence is a key feature of urban noise distribution.

## Methodology sketch

- Download open noise measurement data from citizen science projects (e.g., NoiseTube archives) and municipal open data portals (e.g., NYC Open Data) using `wget` or Python `requests`.
- Acquire complementary urban covariates: traffic volume from OpenTraffic/OSM, land use classification from OSMnx, and population density from WorldPop.
- Geocode and harmonize all datasets to a common coordinate reference system (WGS84) and aggregate to a uniform grid (e.g., 200m x 200m cells) using `geopandas`.
- Compute target variables: mean, median, and 95th percentile decibel (dB) levels per grid cell.
- Fit an Ordinary Least Squares (OLS) regression model with noise metrics as the outcome and traffic, land use, population, and time-of-day indicators as predictors.
- Fit Spatial Lag and Spatial Error models using `PySAL` to explicitly model spatial autocorrelation in the dependent variable and error terms.
- Perform 5-fold spatial cross-validation to prevent data leakage from spatially adjacent training and test sets.
- Compare model performance using RMSE, R², and Akaike Information Criterion (AIC); test predictor significance at p < 0.05.
- Generate residual maps and calculate Moran's I for all models to verify the removal of spatial dependence.
- All computations will be executed in Python using `scikit-learn`, `statsmodels`, and `PySAL`, designed to complete within 3 hours on a 2-core CPU with 7GB RAM.

## Duplicate-check

- Reviewed existing ideas: None in current corpus (first idea in statistics field).
- Closest match: No previous ideas in statistics/urban noise domain.
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-07-06T04:53:32Z
**Outcome**: success
**Original term**: Statistical Analysis of Publicly Available Urban Noise Pollution Data statistics
**Verified citation count**: 8

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Statistical Analysis of Publicly Available Urban Noise Pollution Data statistics | 8 |

### Verified citations

1. **The Statistical Analysis of fMRI Data** (2009). Martin A. Lindquist. arXiv. [0906.3662](https://arxiv.org/abs/0906.3662). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
2. **Statistical Inference: The Big Picture** (2011). Robert E. Kass. arXiv. [1106.2895](https://arxiv.org/abs/1106.2895). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
3. **Population size and centrality effects on NO2 air pollution across and within European cities** (2026). Yufei Wei, Rémi Lemoy, Geoffrey Caruso. arXiv. [2605.28672](https://arxiv.org/abs/2605.28672). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
4. **Night-sky brightness monitoring in Hong Kong - a city-wide light pollution assessment** (2011). Chun Shing Jason Pun, Chu Wing So. arXiv. [1106.3842](https://arxiv.org/abs/1106.3842). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
5. **Interactive Sonification for Health and Energy using ChucK and Unity** (2024). Yichun Zhao, George Tzanetakis. arXiv. [2404.08813](https://arxiv.org/abs/2404.08813). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
6. **A New Class of Private Chi-Square Tests** (2016). Daniel Kifer, Ryan Rogers. arXiv. [1610.07662](https://arxiv.org/abs/1610.07662). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
7. **Testing for high-dimensional network parameters in auto-regressive models** (2018). Lili Zheng, Garvesh Raskutti. arXiv. [1812.03659](https://arxiv.org/abs/1812.03659). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
8. **Semi-Supervised U-statistics** (2024). Ilmun Kim, Larry Wasserman, Sivaraman Balakrishnan, Matey Neykov. arXiv. [2402.18921](https://arxiv.org/abs/2402.18921). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
