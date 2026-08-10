# Data Model: Assessing the Stability of Statistical Model Performance Across Data Subsets

## Overview

This document defines the data structures, schemas, and relationships used throughout the pipeline. The system is designed to process data in a streaming fashion where possible, but intermediate results are materialized as CSV files for transparency and reproducibility.

## Entity Definitions

### 1. Dataset Metadata
Represents the characteristics of a loaded dataset.
-   `dataset_id`: Integer (OpenML ID).
-   `name`: String (Dataset name).
-   `n_samples`: Integer.
-   `n_features`: Integer.
-   `source`: String ("UCI" or "OpenML").
-   `checksum`: String (SHA-256 of raw file).

### 2. EvaluationRun
Represents a single model evaluation within a specific fold and repeat.
-   `dataset_id`: Integer.
-   `model_name`: String ("LogisticRegression", "RandomForest", "LinearSVC").
-   `fold_id`: Integer (1-10).
-   `repeat_id`: Integer (1-10).
-   `accuracy`: Float (0.0 - 1.0).
-   `f1_score`: Float (0.0 - 1.0).

### 3. StabilityMetric
Aggregated metrics for a (Dataset, Model) pair.
-   `dataset_id`: Integer.
-   `model_name`: String.
-   `mean_accuracy`: Float.
-   `std_accuracy`: Float.
-   `cv_accuracy`: Float.
-   `mean_f1`: Float.
-   `std_f1`: Float.
-   `cv_f1`: Float.

### 4. CorrelationResult
Result of the correlation analysis.
-   `dataset_property`: String ("n_samples" or "n_features").
-   `metric_type`: String ("cv_accuracy" or "cv_f1").
-   `correlation_coefficient`: Float.
-   `p_value`: Float.
-   `p_value_adjusted`: Float (Bonferroni corrected).
-   `significant`: Boolean.

### 5. PermutationResult
Result of the variance comparison test.
-   `dataset_id`: Integer.
-   `model_a`: String.
-   `model_b`: String.
-   `metric_type`: String ("accuracy" or "f1").
-   `test_statistic`: Float.
-   `p_value`: Float.
-   `p_value_adjusted`: Float.
-   `significant`: Boolean.

## File Formats

### Input: Raw Datasets
-   **Format**: CSV or ARFF (handled by `openml`).
-   **Location**: `data/raw/`

### Output: Intermediate Results
-   **Format**: CSV (Comma Separated Values).
-   **Encoding**: UTF-8.
-   **Delimiter**: `,`.
-   **Header**: Yes.

### Output: Final Report
-   **Format**: Markdown.
-   **Location**: `results/final_report.md`.

## Data Flow

1.  **Download**: `download_data.py` -> `data/raw/{dataset_id}.csv`.
2.  **Evaluate**: `run_evaluation.py` reads `data/raw/`, writes `results/stability_metrics.csv` (temporarily) or accumulates in memory then writes `results/raw_evaluations.csv` (optional debug).
    *   *Correction*: The plan will aggregate immediately in `run_evaluation.py` to save I/O, writing directly to `results/stability_metrics.csv` after all repeats for a dataset are done.
3.  **Analyze**: `analyze_stability.py` reads `results/stability_metrics.csv` -> writes `results/correlation_results.csv` and `results/permutation_results.csv`.
4.  **Report**: `report_generator.py` reads all CSVs -> writes `results/final_report.md`.
