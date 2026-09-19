# Raw Data Directory

## Source Information
This directory contains the raw data downloaded from the Project Implicit
Data Repository.

**Dataset**: Political IAT (Implicit Association Test)
**Source URL**:
**Repository**: Project Implicit Data Repository (OSF)
**Download Command**: `python code/data_fetcher.py`

## Usage
The raw data file(s) in this directory should **not** be modified.
All processing, imputation, and analysis should be performed on copies
placed in `data/processed/`.

## Provenance
- **Date Downloaded**: (Date will be recorded upon successful fetch)
- **Version**: Latest available from OSF at time of download.
- **License**: See Project Implicit terms of use.

## Validation
Data validation is performed by `code/data_loader.py` against the schema
defined in `contracts/dataset.schema.yaml`.