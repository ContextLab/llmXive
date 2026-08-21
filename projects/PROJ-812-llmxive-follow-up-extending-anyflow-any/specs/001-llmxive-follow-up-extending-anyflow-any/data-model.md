# Data Model: llmXive follow-up: extending "AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distil"

## Overview

This document defines the data structures, schemas, and relationships for the project. All data artifacts are stored in `data/` and versioned via checksums.

## Entities

### 1. VideoClip
A short video segment (16 frames @ 30fps) extracted from a source repository.
*   **ID**: `video_id` (string, unique)
*   **Source**: `source_url` (string, URL of original repository)
*   **Path**: `local_path` (string, relative path to `.mp4` file in `data/raw/`)
*   **Frames**: `num_frames` (int, fixed at 16)
*   **FPS**: `fps` (int, fixed at 30)
*   **Category**: `category` (string, e.g., "continuous", "cut", "mixed")

### 2. ContinuityScore
Manual ground-truth label assigned by a human annotator.
*   **VideoID**: `video_id` (string, FK to VideoClip)
*   **Score**: `score` (float, 0.0 to 1.0, derived from 1-5 Likert scale)
*   **Annotator**: `annotator_id` (string, captured at script start)
*   **Timestamp**: `annotated_at` (ISO 8601, captured automatically)
*   **Rubric**: `rubric_version` (string, e.g., "v1.0-Likert5")

### 3. DivergenceMetric
Computed numerical instability score for a video clip.
*   **VideoID**: `video_id` (string, FK to VideoClip)
*   **Metric**: `divergence_value` (float)
*   **BaselineSteps**: `baseline_n` (int, e.g., 500, 200)
*   **Features**: `features` (JSON, containing `kurtosis`, `temporal_clustering`, etc.)
*   **Status**: `status` (string, "success", "failed", "skipped")
*   **Error**: `error_msg` (string, if failed)

### 4. SensitivityReport
Aggregated results of threshold and resolution sweeps.
*   **Threshold**: `threshold` (float, e.g., 0.01, 0.05)
*   **BaselineSteps**: `baseline_n` (int)
*   **TruePositive**: `tp` (int)
*   **FalsePositive**: `fp` (int)
*   **TrueNegative**: `tn` (int)
*   **FalseNegative**: `fn` (int)
*   **Accuracy**: `accuracy` (float)

### 5. VarianceReport
Statistical summary of the ContinuityScore distribution and stability check.
*   **Variance**: `variance` (float)
*   **Mean**: `mean` (float)
*   **StdDev**: `std_dev` (float)
*   **Bimodal**: `is_bimodal` (boolean, result of Hartigan's Dip Test)
*   **DipPValue**: `dip_p_value` (float)
*   **Kappa**: `kappa` (float, inter-annotator agreement from pilot)
*   **StabilityMet**: `stability_met` (boolean, result of Constitution VI check)
*   **DeltaR**: `delta_r` (float, change in correlation after noise perturbation)

## Data Flow

1.  **Download**: `download.py` (with pre-flight URL check) → `data/raw/videos/` (VideoClip)
2.  **Calibration**: `annotate.py` (calibration mode) → `data/raw/calibration_scores.csv`
3.  **Annotation**: `annotate.py` (main mode) → `data/raw/ground_truth.csv` (ContinuityScore)
4.  **Validation**: `validate.py` → `data/processed/variance_report.csv` (VarianceReport)
5.  **Inference**: `inference.py` → `data/processed/divergence_metrics.csv` (DivergenceMetric)
6.  **Analysis**: `analysis.py` → `data/processed/correlation_results.csv`, `data/processed/sensitivity_report.csv` (SensitivityReport)
7.  **Reporting**: `report.py` (embeds `variance_report.csv`) → Final Report

## Constraints

*   **Immutability**: `data/raw` files are never modified. Derivations are written to new files in `data/processed`.
*   **Checksums**: Every file in `data/` has a corresponding SHA256 hash in `data/checksums.txt`.
*   **Schema Validation**: All CSVs must conform to the schemas defined in `contracts/`.