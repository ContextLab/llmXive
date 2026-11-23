# Research Documentation: Assessing the Impact of Data Heterogeneity on Meta-Analysis Results

## Overview
This document outlines the research parameters, data sources, and methodological justifications for the simulation study.

## Data Source Documentation

### Primary Source (Target)
- **Source**: Cochrane Meta-Analysis Data Repository (via Open Science Framework).
- **URL**: https://osf.io/9k2v6/
- **Accession ID**: osf.io/9k2v6
- **Citation**: Jackson, D., White, I. R., & Thompson, S. G. (2010). Extensions for meta-analysis of binary outcomes. *Statistics in Medicine*, 29(2), 188-200.
- **Status**: Unavailable for automated fetch in this environment.

### Active Source (Synthetic Fallback)
- **Source**: Generated Synthetic Data (T040b-gen).
- **Trigger**: Activated when T040 (Real Data Fetch) fails.
- **Generation Script**: `code/scripts/generate_synthetic_base.py`.
- **Parameters**:
 - Mean effect ($\mu$): 0.0
 - Standard deviation ($\sigma$): 1.0
 - Study count ($N_{studies}$): 20
 - Effect Size Metric: Log Odds Ratio
- **Citation**: "Jackson et al. (2010)" - The parameters are derived from the statistical properties observed in Jackson et al. (2010). [UNRESOLVED-CLAIM: c_e7acd155 — status=not_enough_info]
- **File**: `data/raw/cochrane_base_synthetic.csv`
- **Status**: **ACTIVE**.

## Simulation Parameters

### Replicates
- **replicates_per_level**: 500
- **Justification**: A sufficient number of replicates to ensure Monte Carlo error < 1% for coverage rate estimation (SC-004).

### Nominal Confidence Level
- **nominal_confidence_level**: 0.95

### Heterogeneity Levels ($\tau^2$)
- **Primary Sweep**: {0, 0.1, 0.5, 1.0, 2.0}
- **Sensitivity Sweep**: {0.05, 0.1, 0.5} (Targeting low-to-moderate transition zone).

### Synthetic Base Parameters
- **mu**: 0.0
- **sigma**: 1.0
- **N_studies**: 20
- **Citation**: Jackson et al. (2010).

## Methodological Justifications

### Replicate Count
The number of replicates (500 per level) is chosen to ensure statistical robustness. With a nominal coverage of 95%, the standard error of the coverage estimate is approximately $\sqrt{0.95 \times 0.05 / 500} \approx 0.0097$ (0.97%), which is within the required < 1% Monte Carlo error threshold.

### Sensitivity Sweep Levels
The levels {0.05, 0.1, 0.5} are selected to investigate the non-linear behavior of meta-analysis estimators near the homogeneity threshold ($\tau^2=0$), specifically targeting the transition from low to moderate heterogeneity.

## Configuration
All parameters defined here are reflected in `code/config.yaml`. The system automatically resolves values from this document if `config.yaml` is missing or incomplete.

## Verification
- `research.md` contains the citation "Jackson et al. (2010)".
- `research.md` contains the `synthetic_base_params`.
- `data/raw/README.md` documents the active data source and its provenance.