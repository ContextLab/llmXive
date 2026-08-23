# Model Limitations and Constraints

This document details the specific limitations, assumptions, and boundaries of the predictive models implemented in this project.

## 1. Data Domain Limitations
The models are trained on EBSD datasets for three specific FCC metals: **Aluminum (Al)**, **Copper (Cu)**, and **Nickel (Ni)**.
- **Exclusion**: Predictions for other FCC metals (e.g., Austenitic Stainless Steels, Silver, Gold) are **not supported**. The stacking fault energy (SFE) and crystallographic slip behavior vary significantly across the periodic table, and the current models do not generalize to these materials.
- **Reduction Range**: The training data covers cold rolling reductions from 0% to 80%. [UNRESOLVED-CLAIM: c_3fab98da — status=not_enough_info] Predictions for reductions >80% (e.g., severe plastic deformation regimes) are considered **extrapolations** and are flagged with a confidence penalty.

## 2. Feature Set Constraints
The current input feature vector includes:
- `reduction_percentage` (float)
- `material_type` (categorical: Al, Cu, Ni)

**Missing Variables**: The following microstructural variables are **not** included in the current model, contributing to residual variance:
- Initial grain size
- Initial texture strength
- Stacking fault energy (SFE) (implicitly captured by material type but not explicitly modeled as a continuous variable)
- Dislocation density
- Temperature during rolling

The `code/analysis/robustness.py` module performs variance decomposition to estimate the impact of these missing factors.

## 3. Symmetry and Physical Constraints
- **Re-indexing**: All orientations are re-indexed to FCC symmetry using `orix` before processing. However, the regression models (Polynomial and Gaussian Process) are **agnostic** to crystallographic symmetry. They treat the texture descriptors (volume fractions) as continuous scalar values.
- **Mass Balance**: The model does not explicitly enforce that the sum of volume fractions (Brass + Copper + S + Goss + Random) equals 1.0. [UNRESOLVED-CLAIM: c_cc9ec17a — status=not_enough_info] While the `code/features/mass_balance.py` module validates this for input data, the model output may theoretically violate this constraint slightly due to regression error. Users should normalize output fractions if strict mass balance is required.

## 4. Extrapolation Risks
The models are interpolative in nature.
- **Lower Bound**: Predictions for reductions < 0% are invalid. [UNRESOLVED-CLAIM: c_332436e4 — status=not_enough_info]
- **Upper Bound**: Predictions for reductions significantly higher than the maximum in the training set (e.g., >90%) are unreliable. [UNRESOLVED-CLAIM: c_a4d5d8c3 — status=not_enough_info] The `code/models/extrapolation.py` module flags such predictions.
- **Confidence Penalty**: When extrapolation is detected, a confidence penalty is applied to the standard error, widening the prediction interval.

## 5. Associational Nature
As per the project's associational framing policy:
- The models identify **statistical correlations** between reduction and texture.
- They do **not** simulate the underlying physical mechanisms (e.g., dislocation glide, twin formation).
- Findings should be reported as "associations" or "trends" rather than causal laws.

## 6. Known Edge Cases
- **Low Reliability Samples**: Samples where >50% of EBSD points are filtered out due to low confidence are excluded from training and prediction (see `code/data/exclusion.py`).
- **Anomalous Trends**: If a sample's texture evolution deviates significantly from standard FCC trends (e.g., unexpected decrease in Brass component), it is flagged by `code/analysis/texture_validation.py` but not necessarily excluded, allowing for the study of anomalies.

## 7. Computational Constraints
- **CPU Only**: The pipeline is optimized for CPU execution. GPU acceleration is not utilized and may lead to compatibility issues with `orix` in some environments.
- **Memory**: Processing large EBSD datasets (>1M points) may require significant RAM. [UNRESOLVED-CLAIM: c_42cc04e8 — status=not_enough_info] The pipeline processes data in chunks where possible, but large consolidated datasets may require high-memory environments.
