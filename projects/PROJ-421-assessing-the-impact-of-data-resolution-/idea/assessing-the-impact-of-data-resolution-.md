---
field: statistics
submitter: google.gemma-3-27b-it
---

# Assessing the Impact of Data Resolution on Statistical Power in Publicly Available Spatial Datasets

**Field**: statistics

## Research question

How does the spatial resolution (aggregation level) of gridded environmental data modulate the statistical power to detect spatial autocorrelation in heterogeneous landscapes?

## Motivation

Researchers frequently select data resolution based on storage or computational constraints rather than inferential requirements. If lower resolutions systematically reduce the ability to detect true spatial patterns (Type II error), studies may draw invalid negative conclusions about environmental processes. Quantifying this trade-off ensures resources are allocated to resolutions that preserve inferential validity.

## Literature gap analysis

### What we searched

Queries targeted "spatial resolution statistical power", "modifiable areal unit problem power", and "spatial autocorrelation resolution sensitivity" across Semantic Scholar and OpenAlex. The initial retrieval yielded few results directly linking resolution changes to hypothesis test power curves.

### What is known

- [SoilGrids250m: Global gridded soil information based on machine learning (2017)](https://doi.org/10.1371/journal.pone.0169748) — Establishes that global spatial datasets exist at fixed resolutions (e.g., 250m) with documented accuracy, but does not analyze how changing that resolution affects downstream statistical hypothesis testing power.

### What is NOT known

No published work has quantified the relationship between pixel aggregation size and the Type II error rate of standard spatial autocorrelation tests (e.g., Moran's I) across varying levels of underlying heterogeneity. Specifically, the resolution threshold at which signal is lost remains uncharacterized for common land cover metrics.

### Why this gap matters

Filling this gap enables researchers to perform a priori power analysis for spatial study designs, preventing wasted funding on underpowered surveys. It also informs data providers about the inferential limits of their coarser-resolution products.

### How this project addresses the gap

This project systematically resamples high-resolution public land cover data to coarser grids and measures the resulting power of Moran's I tests. The methodology directly maps resolution changes to power curves, producing the previously unavailable evidence on detection thresholds.

## Expected results

We expect to observe a non-linear decline in statistical power as resolution coarsens, with a distinct threshold where spatial signal becomes indistinguishable from noise. This evidence will confirm that resolution choice is an inferential parameter, not just a storage constraint.

## Methodology sketch

- Download a high-resolution subset (e.g., 30m) of National Land Cover Database (NLCD) for a single state (e.g., Colorado) via USGS EarthExplorer API.
- Create a series of aggregated rasters (e.g., 60m, 120m, 240m, 480m) using nearest-neighbor resampling to preserve categorical integrity.
- Compute Moran's I statistics for each resolution level using the `pysal` Python library on a CPU-only environment.
- Simulate null distributions (1000 permutations per resolution) to estimate p-values and effect sizes.
- Calculate statistical power by comparing observed statistics against simulated effect sizes at varying alpha levels.
- Plot power curves against resolution to identify the inflection point where power drops below 0.80.

## Duplicate-check

- Reviewed existing ideas: None provided in context.
- Closest match: None.
- Verdict: NOT a duplicate
