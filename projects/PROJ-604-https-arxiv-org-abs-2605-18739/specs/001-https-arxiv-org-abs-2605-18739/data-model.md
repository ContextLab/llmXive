# Data Model: Reproduce & Validate LongLive-2.0 NVFP4 Infrastructure

## 1. Overview

This document defines the data structures, schemas, and relationships required for the validation pipeline. Since the project focuses on *software infrastructure* rather than *data analysis*, the data model is centered around **Configuration**, **Execution State**, and **Output Artifacts**.

## 2. Core Entities

### 2.1 Configuration (YAML)
Defines the parameters for the inference run.
*   **Source**: `configs/inference.yaml` or `configs/inference_nvfp4.yaml`
*   **Fields**:
    *   `model_name`: String (e.g., "LongLive-2.0-5B")
    *   `quantization_mode`: Enum ["NVFP4", "FP16", "FP32"]
    *   `sequence_length`: Integer (Number of frames)
    *   `prompt`: String
    *   `output_path`: String (Relative path)
    *   `use_sequence_parallel`: Boolean
    *   `random_seed`: Integer (Fixed for reproducibility and control cases)
    *   `checkpoint_path`: String (Path to the model weights, e.g., `models/LongLive-2.0-5B`)

### 2.2 Execution Metrics (JSON)
Captured at runtime to validate constraints.
*   **Source**: `results/metrics.json`
*   **Contract**: `contracts/metrics_report.schema.yaml`
*   **Fields**:
    *   `start_time`: ISO 8601 Timestamp
    *   `end_time`: ISO 8601 Timestamp
    *   `duration_seconds`: Float
    *   `peak_ram_gb`: Float
    *   `quantization_mode_used`: String
    *   `status`: Enum ["SUCCESS", "OOM", "ERROR", "TIMEOUT"]
    *   `checkpoint_status`: Enum ["FOUND", "MISSING"]
    *   `error_code`: String (e.g., "CHECKPOINT_NOT_FOUND", "OOM", "IMPORT_ERROR")
    *   `has_nan`: Boolean
    *   `artifact_path`: String
    *   `hardware_context`: String
    *   `random_seed`: Integer

### 2.3 Output Artifact (Video)
The generated video file.
*   **Source**: `outputs/<timestamp>.mp4`
*   **Format**: MP4 or WebM
*   **Validation**: File header check, duration > 0s, no corruption.

## 3. Data Flow

1.  **Input**: `configs/*.yaml` + `prompt` (synthetic or file).
2.  **Processing**:
    *   Load Config -> Validate Fields.
    *   Load Weights -> Check Existence -> Set `checkpoint_status`.
    *   Pre-flight Memory Estimation -> Select `inference.py` or `inference_sp.py`.
    *   Run Inference -> Monitor RAM/Time.
 * Check Numerical Stability ([deferred] sample scan).
3.  **Output**:
    *   Video File (Artifact).
    *   Metrics JSON (Report) conforming to `contracts/metrics_report.schema.yaml`.

## 4. Constraints & Rules

*   **RAM Constraint**: `peak_ram_gb` must be ≤ 7.0.
*   **Trigger Threshold**: Pre-flight estimation triggers fallback (SP or reduced frames) if estimated RAM > 6.5GB (leaving 0.5GB safety buffer).
*   **Time Constraint**: `duration_seconds` must be ≤ 21600 (6 hours).
*   **Stability**: `has_nan` must be `false`.
*   **Checkpoint**: If weights are missing, the process must terminate with `status: ERROR`, `checkpoint_status: MISSING`, and `error_code: CHECKPOINT_NOT_FOUND`.

## 5. Schema Definitions

*   `contracts/inference_output.schema.yaml`: Validates the video file metadata and existence.
*   `contracts/metrics_report.schema.yaml`: Validates the structure of `results/metrics.json`. Explicitly references `error_code` (including "CHECKPOINT_NOT_FOUND") and `checkpoint_status` for FR-006 compliance.