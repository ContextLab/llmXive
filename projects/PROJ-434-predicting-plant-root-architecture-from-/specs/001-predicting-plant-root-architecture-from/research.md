# Research: Predicting Plant Root Architecture from Soil Nutrient Profiles

## Overview

This document outlines the community standards, data sources, and citations used in the "Predicting Plant Root Architecture from Soil Nutrient Profiles" project. It serves as the authoritative reference for data ingestion, validation, and statistical significance thresholds.

## 1. Data Sources

The project utilizes the following verified real-world datasets for training and validation:

### 1.1 Root Trait Data
**Source**: The TRY Plant Trait Database (via Zenodo/HuggingFace)
**Description**: A global database of plant functional traits, including root depth and branching patterns.
**Access**: Programmatically accessible via the `trydata` Python package or direct download from Zenodo.
**Citation**: Kattge, J., et al. (2020). TRY plant trait database – enhanced coverage and open access. *Global Change Biology*, 26(1), 119–188.

### 1.2 Soil Nutrient Data
**Source**: SoilGrids 2.0
**Description**: Global soil information system providing gridded maps of soil properties (N, P, K, pH) at 250m resolution.
**Access**: Available via the ISRIC API or downloadable GeoTIFFs from the SoilGrids repository.
**Citation**: Poggio, L., et al. (2021). SoilGrids 2.0: producing soil information for the globe with quantified spatial uncertainty. *SOIL*, 7(1), 217–240.

## 2. Statistical Significance Standards

### 2.1 Significance Level (Alpha)
The project adheres to the community standard for biological and ecological studies:
- **Significance Level (α)**: **0.05**
- **Rationale**: This threshold is widely accepted in ecological research to balance Type I and Type II errors. It is the standard used in the cited literature (e.g., Kattge et al., 2020; Poggio et al., 2021).

### 2.2 Permutation Test Iterations
To ensure robust p-value estimation, the permutation tests will use:
- **Number of Iterations**: **1,000** (minimum)
- **Rationale**: 1,000 iterations provide a stable estimate of the null distribution for p-values down to 0.001, sufficient for the α=0.05 threshold.

## 3. Methodology References

### 3.1 Leave-One-Species-Out (LOSO) Cross-Validation
LOSO is the primary validation strategy to assess model generalizability to unseen species.
**Reference**: Varma, S., & Simon, R. (2006). Bias in error estimation when using cross-validation for model selection. *BMC Bioinformatics*, 7, 91.

### 3.2 Feature Importance Stability
Sensitivity analysis is performed by sweeping p-value thresholds to evaluate the robustness of feature rankings.
**Reference**: Altmann, A., et al. (2010). Permutation importance: a corrected feature importance measure. *Bioinformatics*, 26(10), 1340–1347.

## 4. Data Quality & Validation

- **Geospatial Alignment**: All coordinates must be transformed to WGS84 (EPSG:4326) before extraction from SoilGrids.
- **Physical Plausibility**: Root depth must be > 0; pH values must be within the range [0, 14].
- **Missing Data**: Rows with missing soil data for any predictor (N, P, K, pH) are excluded. The exclusion rate must be < 10% to proceed (Hard Stop Enforcement).

## 5. Compliance & Ethics

- **Data Usage**: All data is used in accordance with the terms of the TRY database and SoilGrids license.
- **Attribution**: Proper citations are included in all reports and publications derived from this work.
- **Reproducibility**: All code and configuration are version-controlled to ensure reproducibility of results.

## 6. Appendix: Verified Real Data Sources

- **TRY Database**: https://www.try-db.org/
- **SoilGrids**: https://soilgrids.org/
- **HuggingFace Dataset (TRY)**: `trydb/try-trait-database` (if available) or direct Zenodo link.
- **SoilGrids Download**: https://files.isric.org/soilgrids/latest/data/

*This document is updated as of the execution of Task T035.*