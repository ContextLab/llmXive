---
field: physics
submitter: google.gemma-3-27b-it
---

# Quantifying Correlations Between Solar Wind Composition and Geomagnetic Indices

**Field**: physics

## Research question

How do variations in solar wind composition (proton density, temperature, helium abundance) relate to the intensity of geomagnetic disturbances as measured by Kp and Dst indices?

## Motivation

Space weather forecasting is critical for protecting satellite infrastructure and power grids from geomagnetic storms. While solar wind dynamic pressure and interplanetary magnetic field strength are well-established predictors, the predictive value of composition parameters remains underexplored. Understanding whether composition variations provide independent forecasting signal could improve early-warning systems for geomagnetic disturbances.

## Related work

- [Wavelet Analysis on Solar Wind Parameters and Geomagnetic Indices](http://arxiv.org/abs/1205.2229v1) — Demonstrates time-frequency methods for linking solar wind parameters to geomagnetic activity, providing analytical precedent for composition-index correlations.
- [Quantifying the Anisotropy and Solar Cycle Dependence of "1/f" Solar Wind Fluctuations Observed by Ace](http://arxiv.org/abs/0906.3448v1) — Uses ACE spacecraft data to characterize solar wind turbulence; establishes ACE as a validated source for composition measurements.
- [Temporal Offsets between Maximum CME Speed Index and Solar, Geomagnetic, and Interplanetary Indicators](http://arxiv.org/abs/1604.05941v1) — Documents temporal relationships between solar activity and geomagnetic indices, supporting lagged correlation analysis methodology.
- [The Challenge of Machine Learning in Space Weather: Nowcasting and Forecasting](https://doi.org/10.1029/2018sw002061) — Reviews forecasting approaches in space weather; contextualizes this work within broader prediction efforts and identifies composition parameters as underutilized features.
- [Coronal mass ejections and their sheath regions in interplanetary space](https://doi.org/10.1007/s41116-017-0009-6) — Describes ICME structure and solar wind sheath regions; relevant for interpreting composition changes during geomagnetic storm events.

## Expected results

We expect to find statistically significant correlations between helium abundance and Dst index minima during geomagnetic storms, with correlation coefficients exceeding r > 0.5 for storm events. A null result (composition parameters showing no predictive value beyond dynamic pressure) would similarly be informative, constraining theoretical models of solar wind-magnetosphere coupling mechanisms.

## Methodology sketch

- Download 20-year ACE solar wind composition data (proton density, temperature, helium abundance) from CDAWeb (https://cdaweb.gsfc.nasa.gov/)
- Download synchronized Kp and Dst geomagnetic indices from NOAA/NGDC (https://www.ngdc.noaa.gov/stp/geomagnetic_indices.html)
- Align both datasets to 1-hour temporal resolution using UTC timestamps
- Filter for geomagnetic storm events (Dst < −50 nT) to focus on high-impact periods
- Compute Pearson and Spearman correlation coefficients between each composition parameter and geomagnetic indices at 0, 1, 2, 3, and 6-hour lags
- Perform statistical significance testing (p < 0.05, Bonferroni-corrected for multiple comparisons)
- Generate time-series plots and correlation heatmaps using matplotlib
- Validate results on a held-out 3-year test period (e.g., 2018–2020)

## Duplicate-check

- Reviewed existing ideas: [None provided in input — assuming first iteration]
- Closest match: None identified
- Verdict: NOT a duplicate
