# llmXive Implementation Guide

## Overview

This document provides implementation details for the llmXive automated science pipeline,
focusing on CPU-tractable feature distillation for video analysis.

## Architecture

### Directory Structure

```
code/
├── src/
│ ├── cli/ # Command-line interfaces
│ ├── config.py # Configuration constants
│ ├── data/ # Data processing modules
│ │ ├── models.py # Data structures
│ │ ├── download.py # Dataset fetching
│ │ ├── preprocess.py # Feature extraction
│ │ └── profiles.py # Profiling utilities
│ ├── models/ # Machine learning modules
│ │ ├── train.py # Model training
│ │ ├── metrics.py # Correlation analysis
│ │ └── evaluate.py # Evaluation utilities
│ ├── reports/ # Report generation
│ │ └── generate.py
│ └── utils.py # Utility functions
├── scripts/ # Executable scripts
│ ├── run_pipeline.py
│ ├── checksum_data.py
│ ├── generate_timing_profile.py
│ ├── generate_sensitivity_analysis.py
│ └── generate_sensitivity_matrix.py
├── tests/ # Test suite
└── requirements.txt # Dependencies

data/
├── raw/ # Raw dataset files
├── processed/ # Processed features
└── results/ # Analysis results

reports/ # Generated reports
state/ # Pipeline state
```

## Core Modules

### Feature Extraction (src/data/preprocess.py)

Implements CPU-tractable feature extraction:
- **Optical Flow**: Farneback algorithm with sampling (every 5th frame)
- **HOG Density**: Histogram of Oriented Gradients for motion patterns
- **Audio Features**: Spectral centroid, zero-crossing rate, RMS energy

Key optimizations:
- Frame sampling to reduce computation
- Graceful handling of missing audio
- Parallel batch processing support

### Correlation Analysis (src/models/metrics.py)

Implements statistical analysis:
- Pearson and Spearman correlation
- Bootstrap confidence intervals (1000 iterations)
- Threshold sweep analysis for sensitivity testing

### Evaluation (src/models/evaluate.py)

Provides evaluation utilities:
- Baseline comparisons (mean predictor, shuffled features)
- Timing projections for 10k clip scaling
- Stability and flip rate calculation

## Execution Flow

1. **Data Fetching**: Download EvalVerse dataset from Zenodo
2. **Feature Extraction**: Process videos to extract features
3. **Model Training**: Train Ridge/Lasso/XGBoost models
4. **Correlation Analysis**: Calculate correlations with human scores
5. **Sensitivity Analysis**: Test threshold robustness
6. **Feasibility Profiling**: Validate CPU constraints

## Configuration

All configuration is managed through `src/config.py`:
- Dataset URLs and DOIs
- Random seeds for reproducibility
- Path constants
- Threshold values

## Running the Pipeline

```bash
# Fetch dataset
python scripts/download_data.py

# Run full pipeline
python scripts/run_pipeline.py

# Generate reports
python scripts/generate_timing_profile.py
python scripts/generate_sensitivity_analysis.py
python scripts/generate_sensitivity_matrix.py
```

## CPU Optimization

The pipeline is optimized for CPU execution:
- OpenCV for video processing (no GPU required)
- librosa for audio analysis
- Frame sampling (every 5th frame) for optical flow
- Batch processing with error handling
- Memory profiling with psutil

## Validation Gates

The pipeline includes validation gates:
- **T040**: Global error rate check (< 5%)
- **T041**: VLM proxy correlation check (r ≥ 0.70)
- **T021**: Memory and time feasibility check

Gates must pass (exit 0) for the pipeline to proceed.
