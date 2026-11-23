# Project Specification: Machine Learning Prediction of Fracture Toughness

## Overview
This project aims to predict the fracture toughness (K_IC) of metallic alloys
from their microstructure images using deep learning.

## Functional Requirements

### FR-001: Data Ingestion
The system shall ingest raw microstructure images and associated metadata.

### FR-002: Preprocessing
Images shall be standardized to 128x128 grayscale with intensity normalization.

### FR-003: Model Training
A 3-block CNN shall be trained to predict K_IC values.

### FR-004: Baseline Comparison
Performance shall be compared against Linear Regression and Random Forest baselines.

### FR-005: Statistical Validation
A Wilcoxon signed-rank test shall be used to validate performance improvements.

### FR-006: Explainability - Grad-CAM
The system shall generate Grad-CAM heatmaps to visualize the regions of the
microstructure that most influence the model's prediction. These heatmaps
are required for interpretability and validation of physical relevance.

### FR-007: Explainability - Stability
Grad-CAM heatmaps shall be validated for stability under image augmentations
(rotations, noise, brightness) to ensure robust feature attribution.

## Data Assumptions
- Sample size: ≥ 500 images (initial assumption, actual generated dataset is larger).
- Input format: CSV file with image paths and K_IC values.
- No JSON side-car files are required for each image.

## Configuration
- Split seed: 42
- Image size: 128x128
- Batch size: 32
