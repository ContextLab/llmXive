# Data Model: Narrative Archaeology

## Overview

This document defines the data structures, schemas, and transformations used in the Narrative Archaeology pipeline. All data artifacts are checksummed and stored in `data/` or `results/`.

## Entities

### NeuralPattern
- **Description**: A vector representing the BOLD signal amplitude across voxels in a specific ROI at a specific timepoint.
- **Attributes**:
  - `subject_id`: str
  - `phase`: str ("early_encoding" or "late_encoding")
  - `roi`: str ("hippocampus", "mPFC", "PCC", "lateral_temporal")
  - `timepoints`: list[float]
  - `event_labels`: list[str]

### NarrativeEvent
- **Description**: A discrete unit of the story defined by its type, timestamp, and semantic content.
- **Attributes**:
  - `event_id`: str
  - `type`: str ("plot", "character", "theme")
  - `onset`: float (seconds)
  - `duration`: float (seconds)
  - `semantic_features`: list[float] (from BERT)

### DecodingModel
- **Description**: A trained linear classifier mapping semantic features to narrative labels.
- **Attributes**:
  - `model_type`: str ("ridge", "svm")
  - `weights`: list[float]
  - `accuracy`: float
  - `chance_level`: float
  - `p_value`: float

## Data Flow

1. **Raw Data**: Downloaded from OpenNeuro (via HuggingFace).
2. **Preprocessed Data**: NIfTI files after realignment, normalization, smoothing.
3. **Segmented Data**: CSV mapping timepoints to event labels (output of `segment.py`).
4. **ROI Timecourses**: Extracted from preprocessed data for specific ROIs.
5. **Semantic Features**: Extracted from story text using BERT.
6. **Decoding Results**: Accuracy metrics, weights, p-values.

## Schema Definitions

### Dataset Schema
- **Input**: Raw NIfTI, JSON event files.
- **Output**: Preprocessed NIfTI, segmented CSV.

### Output Schema
- **RSA Results**: JSON with dissimilarity matrices, p-values.
- **Decoding Results**: JSON with accuracy, chance level, p-values per category.

## Transformation Rules

- **HRF Convolution**: Event labels convolved with HRF to align with BOLD signal.
- **ROI Masking**: Timecourses extracted using standard MNI masks.
- **Normalization**: Z-score normalization per subject per ROI.
- **Permutation**: Labels shuffled repeatedly to generate null distribution.