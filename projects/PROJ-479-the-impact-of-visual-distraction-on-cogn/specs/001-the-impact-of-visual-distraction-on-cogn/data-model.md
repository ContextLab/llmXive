# Data Model: The Impact of Visual Distraction on Cognitive Control in Remote Work Environments

## Overview

This document defines the data structures, schemas, and relationships used throughout the project. It ensures data integrity, reproducibility, and alignment with the functional requirements (FRs) and success criteria (SCs).

## Entities

### 1. Participant
Represents an individual in the study (from OpenML).
- **Attributes**:
  - `participant_id` (int): Unique identifier.
  - `reaction_time` (float): Mean reaction time in milliseconds.
  - `accuracy` (float): Proportion of correct trials (0.0 - 1.0).
  - `error_rate` (float): 1 - accuracy.
  - `environment_tag` (str): Environment tag from OpenML (e.g., "Home", "Office").

### 2. Image
Represents a workspace image (from Unsplash).
- **Attributes**:
  - `image_id` (str): Unique identifier from Unsplash.
  - `file_path` (str): Local path to the downloaded image (sanitized, e.g., `img_<hash>.jpg`).
  - `environment_tag` (str): Environment tag from Unsplash (e.g., "Home Office", "Open Plan").
  - `lighting_condition` (str): Lighting condition from Unsplash metadata.
  - `layout_description` (str): Layout description from Unsplash metadata.
  - **PII Note**: EXIF data is stripped and filename is hashed upon download to prevent PII leakage.

### 3. VisualComplexityMetric
Represents a computed visual complexity measure.
- **Attributes**:
  - `metric_name` (str): One of `edge_density`, `color_entropy`, `object_count`.
  - `value` (float): The computed metric value.
  - `image_id` (str): Foreign key to Image.

### 4. LinkedRecord
Represents a participant-image pair linked via proxy.
- **Attributes**:
  - `participant_id` (int): Foreign key to Participant.
  - `image_id` (str): Foreign key to Image.
  - `link_method` (str): "Proxy" (based on environment_tag).

### 5. CognitivePerformanceMetric
Represents a cognitive task outcome.
- **Attributes**:
  - `task_name` (str): `Stroop` or `Flanker`.
  - `metric_type` (str): `accuracy` or `reaction_time`.
  - `value` (float): The measured value.
  - `participant_id` (int): Foreign key to Participant.

## Data Flow

1.  **Raw Data**: Download OpenML cognitive data and Unsplash images.
2.  **Metadata Extraction**: Extract environment tags and lighting conditions from Unsplash API.
3.  **Metrics Extraction**: `02_visual_metrics.py` processes images to generate `VisualComplexityMetric` records.
4.  **Proxy Linkage**: `01_data_acquisition.py` links participants and images based on `environment_tag`.
5.  **Analysis**: `03_analysis.py` and `04_sensitivity.py` process the linked dataset.
6.  **Results**: Outputs are stored in `results/statistics/` and `results/figures/`.

## Schema Definitions

See `contracts/` for formal YAML schemas.