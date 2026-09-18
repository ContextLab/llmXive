# Architecture Documentation

## System Overview

This document describes the high-level architecture of the Plant Secondary Metabolite Prediction Pipeline.

## Components

### 1. Data Layer (`code/data/`)

- **download.py**: Handles fetching genomic data from NCBI RefSeq and Phytozome, and metabolite data from PMDB/MetaboLights. Implements retry logic and size filtering.
- **preprocess.py**: Contains antiSMASH wrapper, BGC-to-metabolite mapping, and metabolite harmonization (InChIKey normalization, log-transformation).
- **align.py**: Merges genomic and metabolomic data by species, filters partial rows, and calculates alignment success rates.

### 2. Modeling Layer (`code/modeling/`)

- **phylo.py**: Loads phylogenetic trees, constructs covariance matrices, and implements Phylogenetic Generalized Least Squares (PGLS) regression.
- **train.py**: Implements model training with PCA dimensionality reduction, Leave-One-Out CV, and 5-fold CV strategies.
- **eval.py**: Model evaluation, permutation baselines, sensitivity analysis, and metrics reporting.

### 3. Configuration and Utilities

- **config.py**: Pydantic-based configuration management for species lists, thresholds, and paths.
- **utils/logging.py**: Centralized logging setup with file and console handlers.
- **utils/refactor_utils.py**: Helper functions for code cleanup and refactoring.

### 4. Data Models

Pydantic schemas for type-safe data handling:
- `Species`: Species metadata
- `BGCFeature`: Biosynthetic Gene Cluster features
- `Metabolite`: Metabolite profiles
- `ModelOutput`: Model prediction results

## Data Flow

1. **Download**: Raw data fetched from external sources → `data/raw/`
2. **Preprocess**: antiSMASH analysis, harmonization → `data/interim/`
3. **Align**: Merge and filter → `data/processed/aligned_matrix.csv`
4. **Model**: Training and evaluation → `data/processed/metrics.json`
5. **Report**: Final report generation → `data/processed/final_report.md`

## Design Principles

- **Modularity**: Each user story can be implemented and tested independently.
- **Schema Enforcement**: Pydantic models ensure data validity throughout the pipeline.
- **Phylogenetic Awareness**: Models account for evolutionary relationships.
- **Reproducibility**: Checksums and timestamps track all artifacts.

## Extensibility

New data sources can be added by implementing new download functions in `download.py`.
New models can be added to `train.py` following the existing interface.