# Data Model: llmXive follow-up: extending EVA-Bench

## Overview

This document defines the data structures, file formats, and schemas for the EVA-Bench extension project. The data model supports the generation of perturbed audio, the storage of evaluation results, and the statistical analysis of latency effects.

## Key Entities

### 1. Scenario
Represents a single entry from the EVA-Bench suite.
*   **ID**: Unique identifier (e.g., `scenario_001`).
*   **Original Audio Path**: Path to the raw audio file.
*   **Turn Boundaries**: List of timestamps (in seconds) indicating turn transitions.
*   **System ID**: Identifier for the voice agent system used.

### 2. PerturbationProfile
Defines the conditions applied to a scenario.
*   **Type**: `latency` or `acoustic`.
*   **Parameters**:
    *   For `latency`: `mean_delay` (ms), `jitter_range` (ms).
    *   For `acoustic`: `snr_db` (dB), `reverberation_time` (s).
*   **Seed**: Random seed used for reproducibility.

### 3. EvaluationResult
The output of the EVA-Bench scoring pipeline for a specific Scenario + PerturbationProfile.
*   **Scenario ID**: FK to Scenario.
*   **Perturbation Profile ID**: FK to PerturbationProfile.
*   **EVA-A Score**: Accuracy score (float).
*   **EVA-X Turn-Taking Score**: Turn-taking metric (float).
*   **EVA-X Progression Score**: Conversation progression metric (float).
*   **Delta Turn-Taking**: Difference from baseline.
*   **Delta Progression**: Difference from baseline.
*   **Status**: `success`, `timeout`, `floor_effect`, `truncated`.

### 4. ThresholdModel
Output of the segmented regression analysis.
*   **Metric**: `turn_taking` or `conversation_progression`.
*   **Knee Point**: Latency value (ms) where the slope changes.
*   **Slope 1**: Linear degradation rate before knee point.
*   **Slope 2**: Linear degradation rate after knee point.
*   **P-value**: Significance of the non-linearity.

## File Formats

### Raw Data
*   **Format**: `.wav` or `.flac` (lossless).
*   **Location**: `data/raw/`
*   **Naming**: `{scenario_id}_{system_id}.wav`

### Processed Data
*   **Perturbed Audio**: `.wav` (same sample rate as original).
    *   Naming: `{scenario_id}_{system_id}_{perturbation_type}_{params}.wav`
*   **Results CSV**: `data/processed/results.csv`
    *   Columns: `scenario_id`, `system_id`, `perturbation_type`, `delay_ms`, `jitter_ms`, `snr_db`, `eva_a`, `eva_x_turn`, `eva_x_prog`, `delta_turn`, `delta_prog`, `status`.

### Analysis Outputs
*   **Model Parameters**: `data/processed/threshold_models.json`
*   **Plots**: `data/processed/figures/` (PDF/PNG)

## Data Flow

1.  **Ingestion**: Raw EVA-Bench audio -> `data/raw/` (Checksummed).
2.  **Perturbation**: Raw Audio + Profile -> Perturbed Audio (`data/processed/audio/`).
3.  **Evaluation**: Perturbed Audio -> Scores (CSV).
4.  **Analysis**: Scores CSV -> Threshold Models (JSON) + Plots.

## Constraints

*   **Max Audio Duration**: 5 minutes (truncation applied if exceeded).
*   **RAM Limit**: Chunked processing for files > 500MB.
*   **Reproducibility**: All random seeds stored in the PerturbationProfile.
