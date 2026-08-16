# Research: llmXive Follow-up: Teacher Entanglement vs. Scalar Distillation Loss

## Overview
This document outlines the research parameters, data sources, and verification protocols for the llmXive follow-up study focusing on teacher entanglement versus scalar distillation loss.

## Verified Datasets

To satisfy Constitution Principle II (Verified Accuracy), the following dataset has been identified and verified for use in this pipeline.

### Primary Dataset
- **Dataset ID**: `z-reward/z-reward-v1`
- **Source**: Hugging Face Datasets
- **Description**: A multi-modal reward dataset containing prompts, image URLs, teacher scores across four rubric dimensions (Alignment, Realism, Aesthetics, Plausibility), student scalar outputs, and human annotations.
- **Checksum**: `TBD` (Placeholder to be updated upon successful download and verification in T037)
- **Verification Status**: Pending initial download and column validation.

### Fallback Dataset
- **Dataset ID**: `z-reward/z-reward-v2`
- **Source**: Hugging Face Datasets
- **Description**: Alternative version of the Z-Reward dataset if the primary version is unavailable or structurally incompatible.
- **Checksum**: `TBD`
- **Verification Status**: Pending.

### Local Archive Fallback
- **Environment Variable**: `Z_REWARD_ARCHIVE_PATH`
- **Description**: Path to a local `.zip` or `.parquet` archive if remote download is not feasible.
- **Verification**: Requires manual checksum verification against known good values.

## Data Schema Expectations
The dataset is expected to conform to the provisional schema defined in `contracts/dataset.schema.yaml`. Key fields include:
- `prompt`: String
- `image_url`: String
- `teacher_scores`: Object (Alignment, Realism, Aesthetics, Plausibility)
- `student_scalar`: Float
- `human_annotations`: Object (Alignment, Realism, Aesthetics, Plausibility)
- `primary_dimension`: String

## Reproducibility Notes
All data loading logic is implemented in `code/download_zreward.py` (T037). The script enforces strict verification:
1. Attempts to load the Primary Dataset.
2. Falls back to the Fallback Dataset only if the primary verification fails.
3. Falls back to Local Archive only if both remote sources fail.
4. Raises a `RuntimeError` if no real data source is found, ensuring no synthetic data is used for final results.

## Execution Order
This research document must be finalized before the execution of T037 (Download Z-Reward evaluation dataset).