# Known Limitations

## Data Constraints
- **Source Availability**: The pipeline requires real thermodynamic data from NIST-JANAF or SGTE. If these sources are unreachable and no valid local fallback is provided, the pipeline halts immediately (`DATA_SOURCE_MISSING`). No synthetic data is generated.
- **System Complexity**: Visualization is limited to simple binary systems (e.g., Cu-Zn, Al-Cu). Complex or metastable systems (e.g., Fe-C) are excluded from plots.

## Model Limitations
- **Extrapolation**: The model cannot predict for elements outside the convex hull of the training set's elemental properties. Such cases trigger `INVALID_SCOPE` and halt the fold.
- **Data Density**: Systems with fewer than 5 data points per composition or high error variance (>50K) may be flagged as `LOW_DATA_DENSITY` or `LOW_DATA_FIDELITY`.

## Resource Constraints
- **Memory**: The pipeline enforces a 7GB RAM limit. If exceeded, it halts with `RESOURCE_LIMIT_EXCEEDED`.
- **Time**: Execution is capped at 4 hours (14400 seconds).

## Statistical Validity
- **Power Analysis**: If the pilot run indicates insufficient statistical power (<0.8), the pipeline halts to prevent unreliable conclusions.
- **Permutation Test**: If the p-value is ≥ 0.05, the improvement over the null model is considered not significant (`NO_SIGNIFICANT_IMPROVEMENT`).

## Configuration
- **Hardcoded Systems**: The `required_systems` list in `config.yaml` must be manually updated for new systems.
- **Temperature Range**: Valid range is 0K to 5000K. Values outside this range trigger `TEMPERATURE_RANGE_VIOLATION`.
