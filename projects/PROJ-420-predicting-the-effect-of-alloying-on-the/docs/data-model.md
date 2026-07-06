# Data Model

This document describes the data structures used in the pipeline.

## Core Entities

### AlloyRecord

Represents a single alloy entry with composition and properties.

- `alloy_id`: Unique identifier
- `composition`: Dictionary of element -> atomic fraction
- `poissons_ratio`: Measured Poisson's ratio
- `youngs_modulus`: Young's modulus in GPa
- `bulk_modulus`: Bulk modulus in GPa (optional)
- `measurement_method`: Method used to determine Poisson's ratio
- `source`: Data source identifier
- `provenance`: Metadata for independence verification

### ModelMetrics

Stores evaluation metrics for trained models.

- `model_type`: Type of model (e.g., Random Forest)
- `mae`: Mean Absolute Error
- `rmse`: Root Mean Squared Error
- `r2`: R-squared score
- `cv_scores`: Cross-validation scores
- `timestamp`: Training timestamp

## File Formats

- Raw data: JSON
- Processed data: CSV
- Models: Pickle (.pkl)
- Metrics: JSON
