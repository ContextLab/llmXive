# Data Model: llmXive follow-up: extending "AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distil"

## Overview
This document defines the data structures, schemas, and relationships used throughout the project. All data artifacts are stored in `data/` and validated against the schemas in `contracts/`.

## Entities

### 1. VideoClip
Represents a single 16-frame video segment.
*   **ID**: Unique string (e.g., `ucf101_001_01`).
*   **Source**: Origin dataset (UCF101 or Kinetics-400).
*   **Path**: Relative path to the frame sequence or video file.
*   **Frames**: Integer (fixed at 16).
*   **FPS**: Integer (fixed at 30).

### 2. ContinuityScore (Ground Truth)
Manual annotation of temporal continuity.
*   **ClipID**: Foreign key to VideoClip.
*   **Score**: Float [0.0, 1.0]. 0.0 = Perfect Continuity, 1.0 = Maximum Discontinuity.
*   **AnnotatorID**: String (identifier for the human annotator).
*   **RubricScore**: Integer [1, 5] (raw Likert score).
*   **Status**: String ("valid", "discarded_ambiguous"). Ambiguous clips (where annotators differ by >1 point) are marked as discarded and excluded from final analysis.
*   **SourceCodeHash**: String (SHA-256 of the analysis function used to process this clip, for traceability).

### 3. DivergenceMetric
Computed numerical instability metric.
*   **ClipID**: Foreign key to VideoClip.
*   **DivergenceScore**: Float (MSE normalized by dimension D).
*   **BaselineSteps**: Integer (N=500 or N=200).
*   **Kurtosis**: Float (temporal pattern feature).
*   **Clustering**: Float (temporal pattern feature).
*   **Status**: String ("success", "failed", "skipped").

### 4. AnalysisResult
Aggregated statistical results.
*   **MetricType**: String ("Pearson", "Spearman", "Logistic", "t-test").
*   **Value**: Float (correlation coefficient, accuracy, or t-statistic).
*   **PValue**: Float.
*   **ConfidenceInterval**: String (e.g., "95% CI: [0.1, 0.3]").
*   **SourceCodeHash**: String (SHA-256 of the analysis function used, for traceability).

## Data Flow
1.  **Raw**: `data/raw/` contains downloaded video files.
2.  **Annotations**: `data/annotations/continuity_scores.csv` contains manual scores. Ambiguous clips are marked as "discarded_ambiguous".
3.  **Processed**: `data/processed/divergence_metrics.csv` contains computed metrics.
4.  **Final**: `data/processed/correlation_results.csv` and `data/processed/sensitivity_report.csv` contain analysis outputs.

## Validation Rules
*   **Score Range**: ContinuityScore must be $\in [0.0, 1.0]$.
*   **Variance**: The variance of ContinuityScore distribution must be $\ge 0.05$ (unless bimodal).
*   **Completeness**: Every VideoClip in the analysis set must have a corresponding DivergenceMetric (or a "failed" status).
*   **Blinding**: No metadata regarding source dataset or pre-computed cut labels is included in the annotation input.
*   **Traceability**: Every result in `AnalysisResult` must include a `SourceCodeHash` linking to the specific code block that generated it.