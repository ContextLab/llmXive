# Spec: Examining the Impact of Auditory Feedback on Motor Sequence Learning

## Overview
This project investigates the neural correlates of motor sequence learning under different auditory feedback conditions. We utilize fMRI data to analyze brain activation patterns and correlate them with behavioral learning rates.

## Data Source
**Dataset**: ds000246 (OpenNeuro)
**Description**: A motor sequence learning task with auditory feedback manipulation.

## Functional Requirements

### FR-001: Data Acquisition
The system must download the ds000246 dataset from OpenNeuro.
**Constraint**: Only subjects sub-01 through sub-10 are downloaded to fit within the 14GB compute budget.

### FR-002: Preprocessing
The system must run fMRIPrep on downloaded data with specific parameters:
- Output spaces: MNI152NLin2009cAsym
- No reconall
- Motion correction enabled
- Normalization enabled

### FR-003: Quality Control
The system must exclude subjects with head motion > 2mm displacement.

### FR-004: First-Level Analysis
The system must compute contrast maps for "perturbed" (delayed + pitch-shifted) vs "normal" conditions.
**Statistical Test**: One-sample t-test against zero for group analysis.
**Threshold**: p < 0.10 for pilot adjustment.

### FR-005: Group-Level Analysis and Behavioral Correlation
The system must perform a group-level one-sample t-test on contrast maps.
**Metric Definition**: The learning rate is defined as the **global learning rate slope (independent of condition)**.
**Correlation**: Pearson correlation between auditory cortex activation and the global learning rate slope.

### FR-006: Visualization
The system must generate thresholded statistical maps and scatter plots of brain-behavior correlations.

## User Stories

### US1: Data Acquisition and Preprocessing
As a researcher, I want to download and preprocess the fMRI data so that I can analyze brain activity.
**Acceptance Criteria**:
- ds000246 subset (sub-01 to sub-10) is downloaded.
- fMRIPrep derivatives are generated.
- Subjects with motion > 2mm are excluded.

### US2: Statistical Modeling
As a researcher, I want to fit GLMs and perform group analysis so that I can identify significant brain clusters.
**Acceptance Criteria**:
- First-level GLMs are fit.
- Contrast maps are generated.
- Group-level one-sample t-test is performed.
- FDR correction is applied.

### US3: Brain-Behavior Correlation
As a researcher, I want to correlate brain activation with behavioral metrics so that I can understand the neural basis of learning.
**Acceptance Criteria**:
- Learning rates are calculated from behavioral data.
- Correlation between activation and learning rate is computed.
- Visualizations are generated.

## Assumptions
- The dataset ds000246 is available on OpenNeuro.
- The compute environment has sufficient RAM (14GB limit) and CPU for fMRIPrep.
- The "global learning rate slope (independent of condition)" is the appropriate metric for correlating with neural activity in this context.

## Constitution Principles

### Principle VI: Data Integrity
We will use the corrected dataset ds000246, ensuring all analyses are based on real, verified data sources. No synthetic data will be used for final results.

## Statistical Analysis Plan

1. **First-Level**: GLM per subject with conditions: normal, delayed, pitch-shifted.
2. **Contrast**: (delayed + pitch-shifted) - normal.
3. **Group-Level**: One-sample t-test against zero on contrast maps.
4. **Correction**: Voxel-wise FDR (q < 0.05).
5. **Behavioral**: Linear regression of RT vs trial index to get slope (global, independent of condition).
6. **Correlation**: Pearson's r between ROI beta values and learning rate slope.

## Configuration Files

- `stats_config.yaml`: GLM parameters, FDR threshold, ROI definitions.
- `docker_config.env`: fMRIPrep version tag.

## Output Artifacts

- `data/processed/valid_subjects.txt`
- `data/processed/contrast_maps/`
- `data/processed/fdr_clusters.csv`
- `data/processed/learning_rates.csv`
- `figures/brain_behavior_correlation.png`
- `docs/report_summary.csv`