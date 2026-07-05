# Validation Rules

## Data Integrity
- **Rule**: All downloaded files must be checksummed and verified.
- **Rule**: Simulation data must strictly adhere to `simulation_params.json` parameters.

## Subsampling
- **Rule**: Each subsample must have exactly `k` studies.
- **Rule**: Seeds must be logged for every iteration to ensure reproducibility.

## Metrics
- **Rule**: Coverage rate must be between 0.0 and 1.0.
- **Rule**: Stability SD must be non-negative.

## Threshold Detection
- **Rule**: Threshold k must be an integer >= 3.
- **Rule**: GAM fit must have p-value < 0.05 to be considered valid.