# Data Model: llmXive follow-up: extending "Lens: Rethinking Training Efficiency for Foundational Text-to-Image Mo"

## Overview

This document defines the data schemas and flow for the alignment deviation prediction pipeline. All data artifacts are derived from the raw 'pick-a-pic' dataset and transformed into processed CSV/JSON files for analysis.

## Data Flow

1.  **Raw Input**: `pick-a-pic` dataset (JSONL/Parquet) containing `caption`, `clip_score`, `human_rating`.
2.  **Feature Extraction**: `features.py` processes raw captions -> `data/processed/features.csv`.
3.  **Target Calculation**: `preprocess.py` joins features with CLIP/Human scores -> `data/processed/deviation.csv`.
4.  **Model Output**: `train.py` produces `results/model_metrics.json` and `results/significance_results.json`.

## Entity Definitions

### CaptionRecord
The fundamental unit of analysis, representing a single caption and its associated metadata.
- **Raw Fields**: `caption_id`, `caption_text`, `clip_score`, `human_rating`.
- **Derived Fields**: `deviation_score`, `linguistic_uncertainty_proxy`, `syntactic_depth`, `noun_phrase_density`, `caption_length_tokens`, `textual_complexity`, `lexical_diversity`, `syntactic_variety`.

### LinguisticFeatureVector
The vector of predictors ($X$) used for the regression model.
- **Source**: `data/processed/features.csv`.
- **Constraints**: Must not contain any image data or CLIP scores.

### DeviationScore
The target variable ($Y$).
- **Source**: `data/processed/deviation.csv`.
- **Calculation**: $| Z(\text{clip\_score}) - Z(\text{human\_rating}) |$ (or rank-based INT if distributions are non-Gaussian).

## Schema Contracts

The following schemas are defined in `specs/.../contracts/` and enforced by `code/tests/contract/`.

1.  **Dataset Schema**: Defines the raw input requirements (validation of 'pick-a-pic' structure).
2.  **Feature Vector Schema**: Defines the output of `features.py`.
3.  **Deviation Target Schema**: Defines the output of `preprocess.py`.
4.  **Significance Results Schema**: Defines the output of the sensitivity analysis in `train.py`.

See `contracts/` directory for detailed YAML definitions.

## Data Hygiene Rules

- **Immutability**: Raw data in `data/raw/` is never modified.
- **Checksums**: Every processed file in `data/processed/` is checksummed (SHA-256) and recorded in the project state file.
- **Exclusion Logging**: Samples excluded due to short length or missing features are logged in `data/logs/exclusions.log` with the reason and `caption_id`.
- **PII**: No personally identifiable information is permitted in `caption_text`.