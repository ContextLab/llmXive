# Specification: Correlational Analysis of CSA Practices and Yield Stability

## Research Question
Does the adoption of Climate-Smart Agricultural (CSA) practices correlate with improved yield stability in smallholder farms, independent of financial access?

## Hypothesis
H1: Higher CSA index is associated with lower yield variability (higher stability scores) after controlling for financial access (HFIAS).

## Data Sources
- LSMS-ISA surveys (Malawi, Tanzania)
- Sentinel-2 satellite imagery (NDVI time series)

## Variables
- **Dependent**: Yield Stability Score (1/CV of NDVI)
- **Independent**: CSA Index (sum of practice adoption)
- **Control**: HFIAS (Household Food Insecurity Access Scale)

## Methodology
1. Spatial join of household plots to satellite pixels
2. NDVI time-series aggregation for growing seasons
3. Multivariate regression with robust standard errors
4. Sensitivity analysis on cloud cover thresholds

## Limitations
- Observational design (no causal claims)
- Spatial fuzzing for privacy
- Sample size constraints
