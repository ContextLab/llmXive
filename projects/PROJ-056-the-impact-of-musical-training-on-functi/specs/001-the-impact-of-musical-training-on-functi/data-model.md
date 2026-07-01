# Data Model: The Impact of Musical Training on Functional Connectivity in Adolescent Brains

## 1. Overview

This document defines the data structures, schemas, and relationships used in the project. All data artifacts are versioned and checksummed. The model supports the generation of synthetic data for validation and the ingestion of real data if a verified source becomes available.

## 2. Entity Definitions

### 2.1 Subject
Represents an individual participant.
- **Attributes**:
  - `subject_id`: Unique identifier (string).
  - `group`: Categorical (`"musician"`, `"non_musician"`).
  - `years_of_training`: Float (0.0 for non-musicians, ≥1.0 for musicians).
  - `age`: Float (years).
  - `sex`: Categorical (`"M"`, `"F"`).
  - `motion_score`: Float (FD or similar metric).
  - `ses_score`: Float (socioeconomic status proxy).
- **Constraints**:
  - `group` must be `"musician"` if `years_of_training` ≥ 1.0.
  - `years_of_training` must be 0.0 if `group` is `"non_musician"`.

### 2.2 ConnectivityMatrix
Represents the functional connectivity data for a subject.
- **Attributes**:
  - `subject_id`: Link to Subject.
  - `atlas`: Name of parcellation (e.g., `"Schaefer200"`).
  - `n_rois`: Integer (number of regions).
  - `z_matrix`: 2D Array (n_rois x n_rois) of Fisher z-transformed correlations.
  - `networks`: Dictionary mapping network names (e.g., `"auditory"`, `"motor"`, `"executive"`) to lists of ROI indices.
- **Constraints**:
  - Matrix must be symmetric.
  - Diagonal must be 0 (or 1 if correlation, but z-transform of 1 is infinite, so typically 0).
  - Values must be within valid z-score range (typically -3 to 3).

### 2.3 StatisticalResult
Represents the output of a hypothesis test.
- **Attributes**:
  - `connection_id`: String (e.g., `"ROI_1_ROI_2"`).
  - `network`: String (e.g., `"auditory"`).
  - `test_statistic`: Float (t-value).
  - `p_value`: Float (uncorrected).
  - `q_value`: Float (FDR-corrected).
  - `effect_size`: Float (Cohen's d).
  - `confidence_interval`: Tuple (lower, upper).
  - `is_significant`: Boolean (based on primary threshold).
  - `threshold_sensitivity`: Dictionary mapping thresholds to significance status.

### 2.4 NetworkComponent
Represents a connected component from NBS.
- **Attributes**:
  - `component_id`: Integer.
  - `size`: Integer (number of edges).
  - `p_value_fwer`: Float (family-wise error corrected).
  - `edges`: List of `connection_id`.

## 3. File Formats

### 3.1 Input Data (Synthetic or Real)
- **Format**: CSV (for tabular data), NIfTI (for imaging, if real).
- **Location**: `data/raw/`

### 3.2 Processed Data
- **Format**: Parquet (for tabular data), NumPy `.npy` (for matrices).
- **Location**: `data/processed/`

### 3.3 Output Results
- **Format**: CSV (for statistical results), JSON (for NBS components).
- **Location**: `data/results/`

## 4. Data Flow

1. **Ingestion**: `download.py` loads raw data or generates synthetic data.
2. **Preprocessing**: `preprocess.py` filters subjects, matches confounders, and generates `Subject` records.
3. **Connectivity**: `connectivity.py` computes `ConnectivityMatrix` for each subject.
4. **Analysis**: `stats.py` and `correlation.py` generate `StatisticalResult` and `NetworkComponent`.
5. **Validation**: `tests/contract/` verifies output against schemas.
