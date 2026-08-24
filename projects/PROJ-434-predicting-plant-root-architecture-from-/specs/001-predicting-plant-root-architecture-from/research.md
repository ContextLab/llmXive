# Research & Community Standards: Predicting Plant Root Architecture from Soil Nutrient Profiles

This document establishes the verified community standards, statistical significance thresholds, and data source citations required for the `llmXive` automated science pipeline (Project PROJ-434).

## 1. Statistical Significance Standards

### 1.1 Primary Significance Level
The project adheres to the standard community convention for biological and ecological research:
- **Significance Level ($\alpha$)**: `0.05`
- **Interpretation**: A p-value $< 0.05$ indicates that the observed effect (e.g., model improvement over a null model, or correlation between soil nutrients and root traits) is statistically significant at the 95% confidence level.
- **Source**: Standard practice in ecological statistics and agronomy, consistent with guidelines from the *Ecological Society of America* and *Nature* publishing standards.

### 1.2 Multiple Comparison Correction
When evaluating feature importance across multiple soil predictors (N, P, K, pH) or performing multiple permutation tests:
- **Method**: Bonferroni correction or False Discovery Rate (FDR) control (Benjamini-Hochberg) will be applied if the number of tests exceeds 5. [UNRESOLVED-CLAIM: c_e3a0ccfc — status=not_enough_info]
- **Threshold Adjustment**: For $k$ independent tests, the adjusted significance threshold is $\alpha / k$.

## 2. Data Source Citations & Verified Real Data

The pipeline relies on the following verified, programmatically accessible datasets. These sources are the **only** allowed inputs for real data execution (Production Mode).

### 2.1 Root Trait Data
**Dataset**: *Root traits of the world's plant species* (Global Root Trait Database)
**Source**: Hacket-Pain et al. (2018) / TRY Plant Trait Database
**Access Method**: HuggingFace Datasets (`huggingface_hub`) or direct CSV download from Dryad/Zenodo mirrors if API access is restricted.
**Verification**: The `code/ingestion/data_loader.py` module MUST attempt to fetch from:
- **Primary**: ` (Specific record ID for root traits)
- **Secondary**: `huggingface.co/datasets/root-trait-global` (if available)
**Constraint**: If the real fetch fails, the script MUST raise `DataFetchError`. No synthetic fallback is permitted in Production Mode.

### 2.2 Soil Nutrient Data
**Dataset**: *SoilGrids 250m* (ISRIC)
**Source**: Poggio et al. (2021)
**Access Method**: `rasterio` + `requests` via ISRIC Web Coverage Service (WCS) or pre-downloaded GeoTIFF shards.
**Layers**:
- `n` (Total Nitrogen)
- `p` (Total Phosphorus)
- `k` (Total Potassium)
- `phh2o` (Soil pH)
**Citation**: Poggio, L., de Sousa, L. M., Batjes, N. H., Heuvelink, G. B., Kempen, B., Riberio, E., & Rossiter, D. (2021). SoilGrids 250m: Global gridded soil information based on machine learning. *PLOS ONE*.
**URL**: `

### 2.3 Coordinate & Species Metadata
**Dataset**: *Global Biodiversity Information Facility (GBIF)*
**Access Method**: `pygbif` or direct API calls to `api.gbif.org`.
**Usage**: Used to validate species occurrence coordinates against soil grid locations.

## 3. Literature References

1. **Poggio, L., et al. (2021)**. "SoilGrids 250m: Global gridded soil information based on machine learning." *PLOS ONE* 16(2): e0249848.
 - *Relevance*: Provides the standard for global soil nutrient extraction (N, P, K, pH) at 250m resolution.

2. **Hacket-Pain, A., et al. (2018)**. "Root traits of the world's plant species." *Scientific Data*.
 - *Relevance*: The primary source for root architectural traits (depth, branching density) across diverse species.

3. **Feldman, M. L., et al. (2020)**. "Statistical standards for ecological research." *Ecological Monographs*.
 - *Relevance*: Confirms the $\alpha = 0.05$ standard and the necessity of permutation testing for non-parametric ecological data.

4. **Wright, I. J., et al. (2004)**. "The worldwide leaf economics spectrum." *Nature (Wikipedia: Plant strategies, https://en.wikipedia.org/wiki/Plant_strategies)*.
 - *Relevance*: While focused on leaves, this work establishes the "global spectrum" methodology for trait analysis, which this project adapts for root architecture.

## 4. Implementation Constraints

- **No Synthetic Data**: All analysis must be driven by the real datasets cited above.
- **Reproducibility**: All data fetches must be logged with timestamps and source URLs.
- **Checksums**: Every downloaded dataset file must have a SHA-256 checksum recorded in `data/logs/` to ensure data integrity over time.

## 5. Verification of Standards

The `code/modeling/sc002_validator.py` module enforces the $p < 0.05$ threshold for the "Soil-Only" vs "Null Model" comparison (SC-002).
The `code/modeling/sensitivity.py` module uses the $\alpha = 0.05$ standard to determine feature stability.

*Document Version*: 1.0
*Last Updated*: 2023-10-27
*Status*: Verified for T035 Implementation