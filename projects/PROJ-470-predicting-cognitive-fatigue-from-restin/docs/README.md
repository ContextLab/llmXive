# Predicting Cognitive Fatigue from Resting-State EEG Complexity

## Project Overview
This project aims to predict cognitive fatigue using complexity measures from resting-state EEG data.

## Pipeline Parameters
The pipeline parameters are defined in `code/config.yaml`:
- `filter_low`: 1 Hz
- `filter_high`: 40 Hz
- `artifact_threshold`: 100 µV
- `random_seed`: 42
- `min_participants`: 30
- `notch_freq`: 50 Hz

## Data Sources
Data is sourced from public EEG datasets (Sleep-EDF, SHHS).

## Statistical Interpretation
Results are interpreted using correlation coefficients, p-values, and confidence intervals.

## Usage
Follow the steps in `docs/quickstart.md` to run the pipeline.
