# Data Model: Quantifying Neural Representation Drift

## 1. Overview

This document defines the data structures for the drift analysis pipeline. All data flows through the following schemas, ensuring type safety and reproducibility.

## 2. Core Entities

### NeuralPopulationMatrix
A 2D matrix representing averaged spike rates for a specific training day.
*   **Shape**: `(Units, Conditions)`
*   **Filter**: Units must be present in ≥80% of sessions.
*   **Exclusion**: Performance-modulated units (error-related) are removed.

### RepresentationalDissimilarityMatrix (RDM)
A symmetric matrix representing the distance between neural population activity patterns across different training days.
*   **Shape**: `(Days, Days)`
*   **Values**: Pearson correlation distance (1 - r).
*   **Usage**: Off-diagonal elements are used to fit the drift rate.

### DriftRate
A scalar value `b` representing the linear rate of increase in representational distance over time.
*   **Derived From**: Linear regression of RDM off-diagonals vs. time.
*   **Metadata**: Standard error, p-value, R-squared.

### LearningCurve
Time-series of behavioral success rates per subject.
*   **Fields**: `subject_id`, `day`, `success_rate`, `trials_count`.
*   **Derived Metric**: `time_to_success` (interpolated day when success rate reaches threshold).

## 3. Data Flow

1.  **Ingest**: Raw spike data + Behavioral logs -> `RawData` (JSON/Parquet).
2.  **Preprocess**: `RawData` -> `NeuralPopulationMatrix` (per day).
3.  **Compute**: `NeuralPopulationMatrix` (Day A, Day B) -> `RDM` (Day A vs Day B).
4.  **Fit**: `RDM` -> `DriftRate` (per subject).
5.  **Correlate**: `DriftRate` + `LearningCurve` -> `CorrelationResult`.

## 4. Schema Definitions

### Input Schema (Synthetic/Real)
*   `spike_counts`: `int` (Units × Conditions × Days)
*   `behavioral_success`: `float` (0.0 - 1.0) (Trials × Days)
*   `subject_id`: `string`

### Output Schema (Drift Results)
*   `subject_id`: `string`
*   `drift_rate`: `float` (b)
*   `drift_se`: `float` (Standard Error)
*   `p_value`: `float`
*   `model_type`: `string` ("linear", "exponential", "non_drifting")
