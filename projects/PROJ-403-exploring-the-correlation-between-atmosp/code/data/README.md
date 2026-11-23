# Data Directory

This directory stores all raw and processed data for the project.

## Structure
- `raw/`: Unmodified data downloaded from external sources (e.g., CDS).
- `processed/`: Intermediate and final processed datasets (NetCDF, CSV).
- `metadata.yaml`: Checksums and metadata for raw data files.

## Usage
Do not commit large binary files to git. Ensure `.gitignore` rules are respected.
