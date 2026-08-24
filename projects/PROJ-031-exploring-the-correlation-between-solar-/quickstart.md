# Quickstart Guide for PROJ-031

This guide outlines the steps to run the full pipeline for exploring the correlation between solar flare characteristics and geomagnetic storm intensities.

## Prerequisites

- Python 3.11+
- Dependencies installed via `pip install -r requirements.txt`

## Execution Steps

Run the following commands in order to execute the full pipeline:

1. **Ingest Data**: Download GOES, CME, Dst, and Kp data.
 ```bash
 python code/ingest.py
 ```

2. **Align Events**: Match solar events with geomagnetic storms.
 ```bash
 python code/align.py
 ```

3. **Validate Alignment**: Check schema compliance.
 ```bash
 python code/validate.py data/processed/aligned_events.csv contracts/aligned_event.schema.yaml
 ```

4. **Filter Analysis Subset**: Remove recurrent storms for clean analysis.
 ```bash
 python code/filter_analysis_subset.py
 ```

5. **Run Analysis**: Compute correlations and regression models.
 ```bash
 python code/analysis.py
 ```

6. **Log Quality Metrics**: Record data quality stats.
 ```bash
 python code/log_data_quality.py
 ```

7. **Profile Pipeline**: Measure execution time and memory.
 ```bash
 python code/profiler.py
 ```

## Expected Outputs

After successful execution, the following files should be present:

- `data/raw/dst_indices.csv`
- `data/raw/kp_indices.csv`
- `data/processed/aligned_events.csv`
- `data/processed/analysis_subset.csv`
- `results/metrics.json`
- `results/figures/` (plots)

## Troubleshooting

- **Missing Data Files**: Ensure `code/ingest.py` has network access to NOAA/CDAWeb.
- **Schema Validation Errors**: Check `contracts/` for updated schemas.
- **Memory Errors**: The pipeline is designed to stream data; ensure sufficient RAM or reduce dataset size if testing locally.