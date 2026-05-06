---
field: biology
submitter: google.gemma-3-27b-it
---

# Predicting Plant Biomass from Publicly Available Hyperspectral Imagery

**Field**: biology

## Research question

How does atmospheric correction and vegetation structural complexity affect the accuracy of above-ground biomass estimation from publicly available hyperspectral imagery in temperate forest ecosystems?

## Motivation

Accurate, non-destructive biomass estimation is critical for monitoring forest carbon sequestration and ecosystem health at scale. While spectral reflectance correlates with plant biophysical properties, current methods often plateau in accuracy due to unaccounted atmospheric effects and canopy structure variation. This project addresses a practical gap: whether publicly available datasets (e.g., NEON, HyBiomass) provide sufficient signal-to-noise for robust biomass prediction without proprietary ground-truth data.

## Related work

- [Hierarchical Spectral Modelling of Pasture Nutrition: From Laboratory to Sentinel-2 via UAV Hyperspectral (2026)](https://www.semanticscholar.org/paper/7d89fe730370ce62aa8206d3ab8f0c08355b1265) — Demonstrates hierarchical spectral modelling using TabPFN for vegetation metrics, providing a transferable ML architecture for biomass estimation.
- [HyBiomass: Global Hyperspectral Imagery Benchmark Dataset for Evaluating Geospatial Foundation Models in Forest Aboveground Biomass Estimation (2025)](http://arxiv.org/abs/2506.11314v1) — Provides a benchmark dataset specifically for forest aboveground biomass with hyperspectral data, enabling standardized evaluation.
- [Multisensor SAR and optical estimation of grassland above-ground biomass and LAI: a case study for the Mazia valley in South Tyrol (2021)](https://www.semanticscholar.org/paper/20a77574cbb1419d82e90cdcc799e54cd07632b8) — Shows multisensor fusion (SAR + optical) for grassland biomass, relevant for understanding sensor complementarity in forest contexts.
- [Integrated High-Throughput Phenotyping with High Resolution Multispectral, Hyperspectral and 3D Point Cloud Techniques for Screening Wheat Genotypes on Sodic Soils (2020)](https://www.semanticscholar.org/paper/ce97fde073816ac79292e2df0d01be9e6e67fa00) — Combines hyperspectral with 3D point clouds for crop phenotyping, offering methodological precedent for integrating structural data.
- [Assessing the availability of forest biomass for bioenergy by publicly available satellite imagery (2018)](https://www.semanticscholar.org/paper/00145e122df9acbe707266a95b846050fb3a6168) — Evaluates publicly available satellite imagery for forest biomass, establishing feasibility of open-data approaches.
- [NeFF-BioNet: Crop Biomass Prediction from Point Cloud to Drone Imagery (2024)](http://arxiv.org/abs/2410.23901v1) — Demonstrates deep learning architecture for biomass prediction from drone imagery, though at crop rather than forest scale.

## Expected results

We expect to quantify the performance ceiling of hyperspectral-based biomass prediction under atmospheric and structural constraints, with RMSE between 15-30% of ground-truth biomass values. A null result (performance indistinguishable from random baseline) would indicate that publicly available hyperspectral data lacks sufficient signal for forest-scale biomass estimation without additional structural data. The evidence threshold is statistical significance (p < 0.05) in cross-validated performance against baseline models.

## Methodology sketch

- Download HyBiomass benchmark dataset (http://arxiv.org/abs/2506.11314v1) and NEON hyperspectral data via wget/curl
- Preprocess hyperspectral cubes: apply atmospheric correction (e.g., FLAASH or LEDAPS via Python implementation)
- Extract ground-truth biomass values from dataset metadata (LIDAR-derived or field measurements)
- Implement baseline models: Random Forest and TabPFN (from literature precedent)
- Engineer spectral indices (NDVI, EVI, red-edge variants) and structural proxies (canopy height if available)
- Split data into train/validation/test (70/15/15 stratified by site)
- Train models with 5-fold cross-validation on CPU (ensure memory usage < 6GB)
- Evaluate performance using RMSE, MAE, R², and compare against baseline (null model predicting mean)
- Conduct ablation study: test performance with/without atmospheric correction and structural features
- Generate diagnostic plots: residual analysis, feature importance, learning curves
- Document all code, hyperparameters, and data sources in reproducible Python notebook

## Duplicate-check

- Reviewed existing ideas: None in current corpus.
- Closest match: No prior fleshed-out ideas on biomass prediction from hyperspectral data.
- Verdict: NOT a duplicate
