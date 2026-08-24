# Research Documentation

## Objective
Predict cognitive flexibility from resting-state functional connectivity variability.

## Data Source
- **HCP 1200 Subjects**: Resting-state fMRI and behavioral data from the Human Connectome Project. [UNRESOLVED-CLAIM: c_753e323f — status=not_enough_info]
- **Atlas**: Schaefer 200 Parcels (7 Networks). [UNRESOLVED-CLAIM: c_c4b9c86d — status=not_enough_info]

## Methodology
1. **Data Ingestion**: Download HCP data and behavioral scores.
2. **Preprocessing**: Parcellate fMRI time-series.
3. **Feature Extraction**: Compute sliding-window connectivity variability (SD of edge correlations).
4. **Statistical Analysis**: Linear regression of flexibility on variability, controlling for age, sex, motion, and scan time.

## Key Metrics
- **Variability Metric**: Mean edge-wise standard deviation of correlation matrices.
- **Flexibility Score**: NIH Toolbox Dimensional Change Card Sort score.

## Dependencies
See `requirements.txt` for the full list.

## Execution Flow
1. `code/setup_structure.py`: Initialize directories.
2. `code/data/download.py`: Fetch data.
3. `code/data/preprocess.py`: Parcellate.
4. `code/features/connectivity.py`: Compute metrics.
5. `code/analysis/regression.py`: Model association.
