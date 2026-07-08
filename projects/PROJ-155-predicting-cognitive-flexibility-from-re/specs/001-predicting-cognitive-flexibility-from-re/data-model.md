# Data Model: Predicting Cognitive Flexibility from Resting‑State Functional Connectivity Variability

## Overview

This document defines the data structures, schemas, and relationships used throughout the project. All data artifacts must conform to the schemas defined in `contracts/`.

## Entities

### 1. Subject
Represents an individual participant.
- **ID**: Unique string identifier (e.g., "100106").
- **Age**: Integer (years).
- **Sex**: String ("M" or "F").
- **Mean_FD**: Float (mm).
- **Total_Scan_Time**: Float (seconds).
- **Flexibility_Score**: Float (NIH Toolbox score).
- **Status**: String ("Included", "Excluded_Motion", "Excluded_Missing_Behav", "Excluded_Low_SNR").

### 2. RSFC_Variability
Represents the derived connectivity metrics for a subject.
- **Subject_ID**: String (FK to Subject).
- **PCA_Component_1** to **PCA_Component_10**: Float (Top 10 components of edge-wise variability).
- **Null_Model_P**: Float (P-value from AR surrogate validation).
- **Motion_Noise_Residual**: Float (Residual after orthogonalization).

### 3. Regression_Result
Represents the output of the statistical analysis.
- **Model_ID**: String (UUID).
- **Beta_Variability**: Float (Regression coefficient for the primary component).
- **SE_Variability**: Float (Standard error of the regression coefficient).
- **Pearson_R**: Float (Correlation coefficient between predicted and observed).
- **P_Value**: Float (Empirical p-value).
- **R_Squared**: Float.
- **N_Subjects**: Integer.
- **Covariates**: String (JSON string of included covariates).
- **Significance_Status**: String ("Significant" or "Not Significant").
- **FDR_Q_Value**: Float (Adjusted p-value if applicable).
- **FDR_Appplied**: Boolean.

## Data Flow

1. **Raw Data** (HCP/NIH) -> **Preprocessing** -> **Merged CSV** (Subject + Metrics).
2. **Merged CSV** -> **Feature Extraction** -> **Variability CSV**.
3. **Variability CSV** -> **Regression** -> **Results JSON/CSV**.

## Output Artifacts

1.  **`exclusion_log.csv`**: Summary of subject counts and exclusion reasons (SC-001).
2.  **`final_results.csv`**: Row-per-subject file containing `Subject_ID`, `Flexibility_Score`, `PCA_Component_1`...`10`, `Predicted_Score`, `Residual`, `Model_ID` (FR-007, SC-004).
3.  **`regression_summary.json`**: Summary statistics including `Pearson_R`, `P_Value`, `Significance_Status`, `FDR_Q_Value` (SC-003, SC-004, FR-009).

## Constraints

- **Missing Values**: `Flexibility_Score` and `Mean_FD` must not be null for included subjects.
- **Ranges**: `Mean_FD` must be >= 0. `Age` must be > 0.
- **Types**: All scores must be floats; IDs must be strings.
