# Data Directory

This directory stores raw and processed data for the TriSplat extension pipeline.

## Structure
- `raw/`: Original datasets (e.g., RealEstate10K shards)
- `processed/`: Processed data, checksums, and benchmark results
- `figures/`: Generated plots and visualizations

## Note
Data is streamed from RealEstate10K via `datasets` library. No large files are stored locally unless explicitly downloaded for caching.
