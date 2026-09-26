# Predicting Plant Defense Allocation from Publicly Available Transcriptomic Data

## Project Overview

This project implements an automated pipeline to predict plant defense allocation strategies from publicly available RNA-seq data.

## Directory Structure

```
code/
├── src/
│ ├── analysis/ # Analysis modules (DE, modeling, etc.)
│ ├── cli/ # Command line interfaces
│ ├── data/ # Data acquisition and preprocessing
│ └── utils/ # Utilities (config, logging, schemas)
├── scripts/ # Runner scripts for each module
├── tests/ # Test suites
├── data/
│ ├── raw/ # Raw and synthetic data files
│ ├── processed/ # Processed data artifacts
│ ├── traits/ # Trait data
│ ├── manifests/ # Data manifests and metadata
│ └── synthetic/ # Synthetic validation data
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Quickstart

See `quickstart.md` for detailed instructions on running the pipeline in both synthetic and real modes.

## Running with Real Data

1. Configure `TRY_API_KEY` environment variable if accessing TRY database.
2. Ensure network access to NCBI/SRA and Open Tree of Life APIs.
3. Run with `--mode real` flag:
 ```bash
 python code/scripts/run_download.py --mode real
 ```

## Validation

Use synthetic mode (`--mode synthetic`) to validate pipeline structure without real data dependencies.
