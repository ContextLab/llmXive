# Data Model: Assessing Uncertainty Quantification Techniques for Machine‑Learning Predicted Material Properties

## Entities

*   **MaterialSample:**
    *   `composition` (list of floats): Element fractions.
    *   `radius` (float): Atomic radius.
    *   `packing_fraction` (float): Packing fraction.
    *   `formation_energy` (float): Formation energy (target property).
    *   `bulk_modulus` (float): Bulk modulus (target property).
    *   `band_gap` (float): Band gap (target property).
*   **UQPrediction:**
    *   `prediction` (float): Point prediction.
    *   `lower_bound` (float): Lower bound of the prediction interval.
    *   `upper_bound` (float): Upper bound of the prediction interval.
    *   `variance` (float): Predictive variance.
    *   `method` (string): UQ method used (e.g., "DeepEnsemble", "MCDropout", "SparseGP").
    *   `uncertainty_type` (string): 'aleatoric', 'epistemic', or 'total'.
*   **CalibrationMetric:**
    *   `method` (string): UQ method name.
    *   `ece` (float): Expected Calibration Error.
    *   `interval_score` (float): Proper interval score.
    *   `sharpness` (float): Mean interval width.
    *   `coverage` (float): Coverage percentage for a given confidence level.

## Data Flow

1.  Raw data is downloaded from the OQMD Hugging Face dataset.
2.  Data is preprocessed: missing values are handled, and features are scaled.
3.  Data is split into training, validation, and test sets.
4.  A baseline neural network is trained on the training set.
5.  UQ techniques (Deep Ensembles, MC Dropout, Sparse GP) are applied to generate predictions and uncertainty estimates.
6.  Calibration metrics are computed using the validation set.
7.  The best-performing UQ method is selected based on calibration metrics.
8.  The selected UQ method is used for downstream screening.

## Schema (dataset_schema.yaml)

```yaml
$schema: 'http://json-schema.org/draft-07/schema#'
title: OQMD Dataset Schema
description: Schema for the OQMD dataset used in the project.
type: array
items:
  type: object
  properties:
    composition:
      type: array
      items:
        type: number
    radius:
      type: number
    packing_fraction:
      type: number
    formation_energy:
      type: number
    bulk_modulus:
      type: number
    band_gap:
      type: number
  required:
    - composition
    - radius
    - packing_fraction
    - formation_energy
    - bulk_modulus
    - band_gap
```
