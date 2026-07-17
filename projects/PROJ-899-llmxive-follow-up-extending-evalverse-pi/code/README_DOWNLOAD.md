# EvalVerse Dataset Download Guide

## Overview
This document explains how to download and cache the EvalVerse dataset for use in the llmXive project.

## Dataset Source
The EvalVerse dataset is obtained from Zenodo:
- Record ID: 13130186
- Dataset: EvalVerse - A Large-Scale Dataset for Evaluating Video-Language Models
- URL: https://zenodo.org/records/13130186

## Download Process

### Automatic Download
The dataset is automatically downloaded when you run the pipeline for the first time. The download script (`src/data/download.py`) will:
1. Check if the dataset already exists in `data/raw/`
2. If not, download it from Zenodo
3. Extract it to `data/raw/`
4. Compute and store a checksum for verification

### Manual Download
If you prefer to download manually:
1. Visit the Zenodo record: https://zenodo.org/records/13130186
2. Download the dataset archive (typically `evalverse_dataset.tar.gz`)
3. Extract it to `data/raw/`

## Directory Structure
After download, the dataset will be organized as follows:
```
data/
├── raw/ # Extracted dataset files
├── cache/ # Downloaded archives (temporary)
└── processed/ # Processed data (generated later)
```

## Verification
The download script computes a SHA-256 checksum of the downloaded archive and stores it in `state/evalverse_checksum.txt`. This ensures data integrity.

## Troubleshooting

### Download Fails
- Check your internet connection
- Ensure Zenodo is accessible
- Verify you have sufficient disk space (dataset is ~7GB)

### Extraction Fails
- Ensure you have enough disk space
- Check that the archive is not corrupted
- Try re-downloading if the checksum doesn't match

### Dataset Not Found
- Verify the Zenodo record ID is correct
- Check if the dataset has been moved or updated
- Contact the maintainers if issues persist

## Next Steps
After successful download:
1. Run `scripts/checksum_data.py` to verify the download
2. Proceed with data preprocessing and feature extraction
3. Run the full pipeline to generate results

## Data License
Please refer to the Zenodo record for the dataset's license information and usage terms.