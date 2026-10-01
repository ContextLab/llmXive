# Data Model: Reef-Species Unified Dataset

## Overview
This document describes the schema of the final analysis-ready dataset
used for predicting coral bleaching susceptibility. The dataset integrates
environmental data (NOAA), reef geometries (UNEP), species traits (Coral Trait DB),
and bleaching events (ReefBase) into a unified 5-km grid structure.

## Dataset Statistics
- **Total Rows**: 0
- **Total Columns**: 0
- **Feature Columns**: 0
- **Target Column**: bleaching_label

## Column Definitions

| Column Name | Type | Description | Source | Missing? |
|:--- |:--- |:--- |:--- |:--- |

## Data Quality Notes

### Missing Value Handling
- Missing values in critical columns (SST, DHW, thermal tolerance) were imputed
 using nearest temporal neighbors within a 30-day window.
- Rows without valid neighbors were excluded from the final dataset.

### Feature Engineering
- **Lagged Features**: 30-day rolling means of environmental variables.
- **Interaction Terms**: Product of DHW and thermal tolerance.
- **VIF Filtering**: Features with Variance Inflation Factor > 5 were removed
 to reduce multicollinearity.

### Definitional Circularity Check
- DHW is derived from SST. The pipeline verified this relationship and
 **dropped DHW** from the final feature set to avoid definitional circularity.

## Usage
This dataset is intended for training machine learning models to predict
coral bleaching susceptibility based on environmental conditions and
species-specific traits.

## Version Information
- **Schema Version**: 1.0
- **Generated**: 2024-01-01 00:00:00
- **Dependencies**: pandas, numpy, scikit-learn, xgboost
