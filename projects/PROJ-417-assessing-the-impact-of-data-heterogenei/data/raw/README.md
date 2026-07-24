# Raw Data Directory

This directory contains the base dataset used for simulation.

## Source

- **Primary Source**: T040 - Fetch Real Data from Cochrane.
- **Fallback Source**: T040b - Generate Verified Synthetic Base.

## Files

- `cochrane_base.csv`: The primary dataset fetched from the verified Cochrane source.
 - **Columns**: `study_id`, `effect_size`, `variance`, `sample_size`
 - **Citation**: As defined in `research.md`.

- `cochrane_base_synthetic.csv`: Generated only if T040 fails.
 - **Source**: Parameters cited from Jackson et al., 2010.
 - **Purpose**: Fallback to ensure pipeline execution when real data is unavailable.

## Verification

Ensure that exactly one of the above files exists before running the simulation pipeline (T010).
The pipeline will automatically attempt to load `cochrane_base.csv` and fall back to `cochrane_base_synthetic.csv` if the former is missing.
