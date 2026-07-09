# Data Model: Narrative Archaeology: Reverse-Engineering Story Memories from Brain Data

## 1. Overview

This document defines the data structures and schemas used throughout the pipeline. All data flows from raw NIfTI files to derived CSV/Parquet tables, adhering to the "Data Hygiene" principle (no in-place modifications).

## 2. Core Entities

### 2.1 NeuralPattern
- **Definition**: A vector of BOLD signal amplitudes across voxels in a specific ROI at a specific timepoint.
- **Source**: Derived from preprocessed NIfTI files via ROI masking.
- **Shape**: `[n_voxels, n_timepoints]` per subject per ROI.
- **Contract**: `dataset.schema.yaml` (subset: timepoints, event_labels).

### 2.2 NarrativeEvent
- **Definition**: A discrete unit of the story defined by type, timestamp, and semantic content.
- **Source**: `events.tsv` from OpenNeuro ds000234.
- **Attributes**: `onset`, `duration`, `trial_type`, `text_content`.
- **Contract**: `event_schema.yaml`.

### 2.3 DecodingModel
- **Definition**: A trained linear classifier mapping **Neural Patterns** to narrative labels.
- **Attributes**: `weights`, `bias`, `accuracy`, `cross_validation_folds`.
- **Input**: Neural Pattern (ROI timecourse).
- **Target**: Narrative Label.
- **Contract**: `decoding_result_schema.yaml`, `model_output.schema.yaml`.

## 3. Data Flow

1. **Raw**: `sub-XX/ses-XX/func/sub-XX_ses-XX_task-story_bold.nii.gz`
2. **Preprocessed**: `derivatives/fmriprep/sub-XX/func/sub-XX_ses-XX_task-story_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz`
3. **Segmented**: `data/segmented_events.csv` (aligned with BOLD timecourse)
4. **Extracted**: `data/roi_timecourses/{roi}_{subject}.csv`
5. **Semantic**: `data/semantic_features/{subject}.parquet` (used for RSA/covariates only)
6. **Results**: `results/decoding_accuracy.csv`, `results/rsa_dissimilarity.csv`, `results/cross_subject_results.csv`

## 4. Schema Mapping

| Data Model Entity | Contract Schema File | Description |
| :--- | :--- | :--- |
| **NeuralPattern** | `dataset.schema.yaml` | Defines the structure of preprocessed fMRI data and event alignment. |
| **NarrativeEvent** | `event_schema.yaml` | Defines the structure of segmented narrative events. |
| **DecodingModel** | `decoding_result_schema.yaml`, `model_output.schema.yaml` | Defines the structure of decoding results and model outputs. |
| **Cross-Subject Result** | `cross_subject_result_schema.yaml` | Defines the structure of LOSO validation metrics. |

## 5. Schema Constraints

- **Checksums**: All raw data files must have a corresponding `.sha256` file.
- **PII**: No raw text containing PII is stored; only anonymized event labels are used.
- **Versioning**: All derived files include a `version` field matching the code hash.