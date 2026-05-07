---
field: biology
submitter: google.gemma-3-27b-it
---

# Predicting Avian Foraging Behavior from Public eBird Data and Land Cover Maps

**Field**: ecology / ornithology

## Research question

How does land cover composition predict avian foraging strategy across species, and do species with similar foraging niches occupy similar habitat profiles?

## Motivation

Understanding the relationship between habitat characteristics and foraging strategies can provide insights into species' ecological niches and inform conservation planning. Current species distribution models often treat habitat as a static presence-absence predictor rather than linking specific land cover types to functional foraging behaviors. This gap limits our ability to predict how habitat changes will affect species with specialized foraging requirements.

## Literature gap analysis

### What we searched

Queried Semantic Scholar and arXiv using the following queries: (1) "avian foraging behavior land cover prediction", (2) "eBird data foraging strategy habitat", (3) "species distribution model foraging niche". Searched approximately 45 results across sources, with only 2 papers directly on-topic regarding the specific link between land cover and foraging behavior.

### What is known

- [Avian SDMs: current state, challenges, and opportunities](https://doi.org/10.1111/jav.01248) — Establishes that species distribution models are central to modern biogeography but notes limited integration of functional trait data with spatial habitat predictors.
- [eBird records show substantial growth of the Allen's Hummingbird population in urban Southern California](https://doi.org/10.1650/condor-16-153.1) — Demonstrates that eBird occurrence data can track population changes in response to habitat modification, though not specifically analyzing foraging strategy.

### What is NOT known

No published work has systematically linked eBird occurrence records to remotely sensed land cover types to predict foraging strategy categories (ground, canopy, aerial) across multiple species. Existing SDM literature treats habitat as a presence predictor rather than testing whether land cover profiles distinguish foraging niches. The Allen's Hummingbird study shows habitat sensitivity but does not generalize across foraging guilds.

### Why this gap matters

Conservation planners need to know whether habitat protection should target specific land cover types based on the foraging needs of resident species. Without this link, habitat management may fail to support species with specialized foraging requirements even when overall habitat area is preserved. Filling this gap would enable more targeted conservation decisions and better prediction of species responses to land-use change.

### How this project addresses the gap

This project will (1) extract land cover composition at eBird observation locations for species with known foraging strategies, (2) test whether land cover profiles distinguish foraging guilds using statistical classification, and (3) quantify which land cover types most strongly predict each foraging strategy. These steps directly produce the previously-unavailable evidence linking habitat composition to functional foraging behavior.

## Expected results

We expect to find that certain land cover types (e.g., forest canopy, open grassland, wetland) are significantly associated with specific foraging strategies. A null result—that land cover composition does not predict foraging guilds—would suggest that foraging behavior is more flexible or driven by finer-scale microhabitat features not captured in coarse land cover maps. Either outcome would be informative for conservation planning and SDM development.

## Methodology sketch

- Download eBird occurrence data for 20-30 bird species with documented foraging strategies (ground, canopy, aerial) from eBird Basic Dataset (https://ebird.org/science/use-ebird-data)
- Obtain land cover classification data (e.g., NLCD 2019 for North America, 30m resolution) via HTTPS from USGS EarthExplorer (https://earthexplorer.usgs.gov)
- Extract land cover composition (proportion of each class) within 100m buffer around each eBird observation point using Python rasterio and geopandas
- Merge observation records with land cover features, filtering to species with ≥50 observations each to ensure statistical power
- Train a random forest classifier (scikit-learn) to predict foraging strategy from land cover proportions, using 5-fold cross-validation
- Evaluate model performance using balanced accuracy and per-class F1 scores to account for class imbalance across foraging guilds
- Extract feature importance scores to identify which land cover types most strongly predict each foraging strategy
- Conduct permutation tests (1000 iterations) to assess whether classification performance exceeds chance (p < 0.05 threshold)
- Generate visualizations: confusion matrix, feature importance bar chart, and spatial map of high-probability foraging habitats for 2-3 focal species
- Document all data sources, code, and results in a reproducible Jupyter notebook; total runtime should complete within 4 hours on 2 CPU/7GB RAM

## Duplicate-check

- Reviewed existing ideas: none provided in input corpus.
- Closest match: none (first fleshed-out idea in this field).
- Verdict: NOT a duplicate
