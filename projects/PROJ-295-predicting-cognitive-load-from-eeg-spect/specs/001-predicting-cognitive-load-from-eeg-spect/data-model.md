# Data Model: Predicting Cognitive Load from EEG Spectral Power Changes During Naturalistic Viewing

## 1. Overview

This document defines the data structures, schemas, and transformation logic for the project. All data flows from the raw OpenNeuro dataset through preprocessing to the final feature matrix and model outputs.

## 2. Data Flow Diagram

```mermaid
graph TD
    A[Raw EEG (ds000246)] -->|Download & Verify| B(Manifest: checksums)
    B --> C[Preprocessing: Filter, Downsample, ICA]
    C --> D[Clean Epochs]
    D -->|Feature Extraction| E[Spectral Features: Theta/Alpha Power]
    D -->|Label Generation| F[Gaze Variance Proxy]
    E --> G[Feature Matrix: [n_epochs, n_channels*2]]
    F --> H[Label Vector: [n_epochs]]
    G & H --> I[Ridge Regression Model]
    I --> J[Results: R2, RMSE, P-values]
    J --> K[Sensitivity Analysis: Window Variation]
```

## 3. Entity Definitions

### 3.1 Raw Data
-   **Source**: OpenNeuro ds000246.
-   **Format**: BIDS (Brain Imaging Data Structure) compliant (`.edf`, `.tsv` for events, `gaze.tsv` for eye-tracking).
-   **Key Fields**:
    -   `subject_id`: Unique identifier for each participant.
    -   `session_id`: Session identifier (if applicable).
    -   `task`: "naturalistic_viewing".
    -   `run`: Run number.
    -   `EEG_Data`: Time-series data (channels x time).
    -   `Events`: Onset, duration, and type of video segments.
    -   `Gaze_Data`: X, Y coordinates of gaze fixation.

### 3.2 Processed Data (Intermediate)
-   **Clean Epochs**: Time-locked segments of EEG data (e.g., 2 seconds per epoch) after artifact removal.
-   **Attributes**:
    -   `epoch_id`: Unique identifier (derived from subject, run, time).
    -   `subject_id`: Link to raw subject.
    -   `start_time`: Timestamp relative to stimulus onset.
    -   `duration`: Duration in seconds.
    -   `data_shape`: (n_channels, n_samples).

### 3.3 Feature Matrix
-   **Structure**: 2D array (numpy/pandas DataFrame).
-   **Dimensions**: `[n_epochs, n_features]`.
-   **Features**:
    -   `theta_power_{channel}`: Mean power in 4–7 Hz band.
    -   `alpha_power_{channel}`: Mean power in 8–12 Hz band.
    -   `theta_alpha_ratio_{channel}`: (Optional, derived).
-   **Normalization**: Min-max scaling per subject (as per US-2).

### 3.4 Label Vector
-   **Structure**: 1D array (numpy/pandas Series).
-   **Values**: Continuous cognitive load score derived from gaze variance.
-   **Range**: Normalized [0, 1] per subject.

### 3.5 Model Outputs
-   **Coefficients**: Ridge regression weights per feature.
-   **Metrics**: R², RMSE, Pearson r.
-   **Statistics**: P-values (corrected).

## 4. Transformation Logic

### 4.1 Preprocessing (FR-001, FR-002)
1.  **Filter**: 1–45 Hz bandpass (Butterworth, 4th order).
2.  **Downsample**: To 250 Hz.
3.  **Line Noise**: Remove 50/60 Hz notch.
4.  **ICA**: Identify and remove components corresponding to eye blinks (based on topography and time course).
5.  **Epoching**: Segment data around video events.

### 4.2 Feature Extraction (FR-003)
1. **PSD**: Compute Power Spectral Density using Welch's method (window size: 2s, overlap: [deferred]).
2.  **Band Power**: Integrate PSD over theta (4–7 Hz) and alpha (8–12 Hz).
3.  **Vectorization**: Flatten channel-band pairs into a single feature vector.

### 4.3 Label Generation (FR-004)
1.  **Gaze Variance**: Calculate variance of X and Y gaze coordinates within the epoch window.
2.  **Normalization**: Min-max scaling per subject to handle inter-subject variability.

### 4.4 Modeling (FR-005, FR-006)
1.  **Split**: Subject-wise 5-fold cross-validation.
2.  **Train**: Ridge Regression with alpha tuning.
3.  **Evaluate**: Compare against mean-baseline (predicting the mean of the training set).

## 5. Data Quality & Integrity

-   **Missing Data**: Epochs with >5% missing sensor data are flagged and excluded (US-2).
-   **Outliers**: Extreme gaze variance values (e.g., >3 SD) are inspected but not automatically excluded unless defined as artifacts.
-   **Checksums**: All processed files are checksummed (SHA-256) and recorded in `data/manifest.yaml`.
-   **Quality Checks**:
    -   **SC-004**: Pipeline calculates epoch retention rate post-ICA. **Halt if < 70%**.
    -   **SC-005**: Pipeline validates that theta/alpha power values are non-zero and stable (low variance) before modeling.
    -   **FR-008**: Sensitivity analysis records R² for varying gaze windows (1s, 2s, 4s).