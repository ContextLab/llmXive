---
field: physics
submitter: google.gemma-3-27b-it
---

# Investigating the Relationship Between Stellar Flare Frequency and Exoplanet Atmospheric Retention

**Field**: physics

## Research question

How does the cumulative high-energy flare flux from host stars correlate with the estimated atmospheric mass loss rates of close-in exoplanets?

## Motivation

Atmospheric retention is a prerequisite for planetary habitability, particularly for planets orbiting active M-dwarf stars. While theoretical models suggest flares drive atmospheric erosion, a quantitative empirical link between observed flare frequencies and specific atmospheric loss rates remains under-constrained. Addressing this gap will refine habitability assessments for the thousands of exoplanets discovered by TESS and Kepler.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and OpenAlex for terms including "stellar flare frequency exoplanet atmosphere erosion," "TESS flare habitability correlation," and "space weather atmospheric escape exoplanets." The search returned a limited set of results focusing either on general habitability impacts or methodological flare detection rather than direct quantitative correlation.

### What is known

- [Impact of space weather on climate and habitability of terrestrial-type exoplanets (2019)](https://openalex.org/W3103168219) — Establishes the theoretical framework that space weather significantly influences the climate and habitability potential of terrestrial exoplanets.
- [Flare Statistics for Young Stars from a Convolutional Neural Network Analysis of TESS Data (2020)](https://doi.org/10.3847/1538-3881/abac0a) — Provides robust methods for detecting and cataloging stellar flares in TESS photometric data, enabling large-scale flare statistics.

### What is NOT known

No published work has quantitatively mapped the observed flare frequency rates from specific TESS exoplanet hosts to modeled atmospheric mass loss rates for those specific planets. Existing literature treats space weather impacts broadly or focuses on flare detection methodology without linking the two to planetary retention outcomes.

### Why this gap matters

Filling this gap is critical for distinguishing between potentially habitable and sterilized worlds around active stars. Without empirical constraints on flare-driven erosion, habitability models rely on uncertain assumptions about stellar activity levels, potentially overestimating the number of viable exoplanets.

### How this project addresses the gap

This project directly cross-matches TESS flare catalogs with exoplanet orbital parameters to compute cumulative high-energy flux and applies energy-limited escape models to estimate retention rates. The resulting statistical correlation provides the first empirical constraint on the relationship between observed flare activity and atmospheric erosion for a specific sample of exoplanets.

## Expected results

We expect to observe a statistically significant negative correlation between cumulative flare flux and estimated atmospheric retention probability for close-in exoplanets. Confirmation will rely on a Spearman rank correlation coefficient (ρ < -0.3, p < 0.05), while a null result would suggest shielding mechanisms or non-flare dominated erosion processes are more significant than currently modeled.

## Methodology sketch

- Retrieve TESS flare event catalogs from the Mikulski Archive for Space Telescopes (MAST) via `wget` or `astroquery`.
- Download exoplanet orbital and physical parameters (radius, mass, semi-major axis) from the NASA Exoplanet Archive API.
- Filter the dataset to include only planets orbiting M-dwarf hosts with sufficient flare detection history (≥10 events).
- Calculate cumulative XUV flux received by each planet based on flare frequency and host star luminosity.
- Estimate atmospheric mass loss rates using an energy-limited escape model implemented in Python (`astropy`, `numpy`).
- Perform a Spearman rank correlation test between cumulative flare flux and estimated mass loss rates.
- Generate diagnostic plots (scatter plot with regression line) and store results in CSV format.
- Ensure all data processing steps are executed within a single Python script to fit within the 6-hour GitHub Actions runtime limit.

## Duplicate-check

- Reviewed existing ideas: None provided in context.
- Closest match: None.
- Verdict: NOT a duplicate
