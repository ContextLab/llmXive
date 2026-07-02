# Data Model: Investigating Network Centrality in ASD Resting-State fMRI

## Overview

This document defines the data structures, schemas, and flow for the project. All artifacts are versioned and checksummed.

## Entity Definitions

### Participant
Represents a single subject in the study.
*   **Attributes**:
    *   `subject_id`: Unique string identifier (e.g., "ABIDE_001").
    *   `diagnosis`: Enum {"ASD", "Control"}.
    *   `age`: Integer (years).
    *   `sex`: Enum {"M", "F"}.
    *   `motion_mean_fd`: Float (Mean Framewise Displacement).
    *   `exclusion_reason`: String (null if included).

### TimeSeries
Preprocessed fMRI signal for a single participant.
*   **Attributes**:
    *   `subject_id`: String.
    *   `roi_count`: Integer (400).
    *   `timepoints`: Integer.
    *   `data`: Float32 array (shape: `timepoints` x `roi_count`).
    *   `source`: String (e.g., "OpenNeuro ds0002800").

### ConnectivityMatrix
Pearson correlation matrix between ROIs.
*   **Attributes**:
    *   `subject_id`: String.
    *   `matrix`: Float32 array (shape: `roi_count` x `roi_count`).
 * `threshold`: Float (e.g., 0.15 for top [deferred]).
    *   `is_binary`: Boolean.

### CentralityMetrics
Graph topology measures per node.
*   **Attributes**:
    *   `subject_id`: String.
    *   `degree`: Float array (length 400).
    *   `betweenness`: Float array (length 400).
    *   `eigenvector`: Float array (length 400).
    *   `threshold`: Float.

### GroupComparisonResult
Statistical test results.
*   **Attributes**:
    *   `metric_name`: String (e.g., "degree").
    *   `roi_index`: Integer.
    *   `mean_asd`: Float.
    *   `mean_control`: Float.
    *   `t_statistic`: Float.
    *   `p_value`: Float.
    *   `q_value`: Float (FDR corrected).
    *   `significant`: Boolean.

### ClassificationResult
Model performance metrics.
*   **Attributes**:
    *   `fold`: Integer.
    *   `accuracy`: Float.
    *   `auc`: Float.
    *   `confusion_matrix`: Array of 4 integers.

### PreprocessingLog (NEW)
Records the provenance of the pre-processed data used.
*   **Attributes**:
    *   `source_dataset`: String (e.g., "OpenNeuro ds0002800").
    *   `fmriprep_version`: String (extracted from BIDS sidecars).
    *   `total_attempts`: Integer.
    *   `successful_outputs`: Integer.
    *   `excluded_count`: Integer.
    *   `exclusion_reasons`: Array of strings.
    *   `success_rate`: Float (calculated: `successful_outputs` / `total_attempts`).
    *   `subset_size`: Integer (number of participants processed in this run).

### CentralityCompletenessReport (NEW)
Records the completeness of centrality computation.
*   **Attributes**:
    *   `total_participants`: Integer.
    *   `participants_with_full_data`: Integer.
    *   `total_rois`: Integer (400).
    *   `rois_with_full_data`: Integer.
    *   `completeness_rate`: Float (calculated: `participants_with_full_data` / `total_participants`).

### CollinearityDiagnostics (NEW)
Documents pairwise correlations between centrality metrics.
*   **Attributes**:
    *   `metric_pair`: String (e.g., "degree_betweenness").
    *   `correlation_coefficient`: Float.
    *   `p_value`: Float.
    *   `interpretation`: String (descriptive framing).

### SensitivityAnalysisResult (NEW)
Captures the results of the threshold sensitivity analysis.
*   **Attributes**:
    *   `threshold_10pct`: Object (nodes significant, count).
    *   `threshold_15pct`: Object (nodes significant, count).
    *   `threshold_20pct`: Object (nodes significant, count).
    *   `jaccard_10_15`: Float.
    *   `jaccard_15_20`: Float.
    *   `jaccard_10_20`: Float.
    *   `nodes_significant_all`: Integer.

## Data Flow

1.  **Raw**: Download pre-processed ABIDE derivatives (NIfTI, CSV) from OpenNeuro.
2.  **Processed**: Time-series extracted from ROIs (no re-preprocessing).
3.  **Derived**:
    *   Correlation matrices.
    *   Centrality metrics.
    *   Statistical test results (CSV).
    *   Classification metrics (JSON).
    *   **Logs**: `PreprocessingLog`, `CentralityCompletenessReport`.
    *   **Diagnostics**: `CollinearityDiagnostics`, `SensitivityAnalysisResult`.
4.  **Output**: Visualizations (PNG), Paper-ready tables (Markdown/CSV).

## Storage Constraints

*   **Raw Data**: Pre-processed derivatives. Estimated size: a subset used in CI.
*   **Processed**: Float32 arrays. A moderate number of participants * a moderate number of timepoints * 400 ROIs * 4 bytes ≈ a moderate data volume.
*   **Derived**: Negligible size.
*   **CI Strategy**: The CI runner will process a **subset** (e.g., 20 participants) or the full available subset to stay within 7GB RAM and 6h runtime. **Subset Processing** is explicitly logged in `PreprocessingLog`.
