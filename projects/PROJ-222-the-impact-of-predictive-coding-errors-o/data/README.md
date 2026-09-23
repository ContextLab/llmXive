# Dataset Metadata and Status

## Overview
This directory contains dataset metadata, exclusion logs, and status information for the time perception analysis project.

## Verified Datasets
# MANUAL DATASET INJECTION PROTOCOL (T050)
# The researcher MUST manually add a new dataset entry below.
# Format: - id: <ID>, source: <OpenML|HF>, url: <URL>
# Example (replace with real, verified source):
# - id: openml.org/d/12345
# source: OpenML
# url: https://www.openml.org/search?type=data&id=12345
# - id: hf-dataset-name
# source: HF
# url:

## Dataset IDs
Dataset IDs are listed in `dataset_ids.txt`.

## Exclusion Log
Datasets that failed validation are logged in `data/processed/exclusion_log.json`.

## Dataset Exclusions

## Status
- **Valid datasets**: Will be listed here after successful download and validation
- **Excluded datasets**: Listed above with reasons

## Checksums
SHA256 checksums are computed during download and stored in the exclusion log for verification.

## Sampling Strategy
- Streaming full dataset or first N=5000 trials as per SC-004.
- Logged in `analysis/verification_log.json`.
## Dataset Status

- **# Dataset IDs for time perception studies**: failed
- **# Format: OpenML dataset ID (numeric) or HuggingFace dataset ID (string)**: failed
- **# OpenML datasets**: failed
- **42278**: failed
- **42279**: downloaded
- **42280**: downloaded
- **# HuggingFace datasets**: failed
- **# Add verified datasets here as they are discovered**: failed
- **# Example: psycholab/time-perception**: failed
