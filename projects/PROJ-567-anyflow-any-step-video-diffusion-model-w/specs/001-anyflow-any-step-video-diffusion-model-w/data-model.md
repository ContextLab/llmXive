# Data Model: AnyFlow Reproduction & Validation

## Overview

This document defines the data structures, schemas, and validation rules for the AnyFlow reproduction pipeline. It ensures that the generated artifacts and evaluation reports are consistent, valid, and ready for automated testing.

## Entities

### 1. ModelCheckpoint
Represents the pre-trained weights used for inference.
- **Type**: File path string
- **Constraints**: Must exist locally; must be a `.safetensors` or `.pth` file.
- **Size Limit**: Must fit within 7GB RAM when loaded (implies < 3GB file size for 1.3B model).

### 2. InferenceConfig
Configuration for the diffusion model run.
- **Fields**:
  - `prompt`: Text string of moderate length.
  - `steps`: Integer (min positive, max 100).
  - `resolution`: Tuple (width, height).
  - `device`: String (must be "cpu").
  - `seed`: Integer (for reproducibility).

### 3. GeneratedVideo
The output artifact.
- **Type**: File path string (`.mp4`).
- **Validation Rules**:
  - File size > 0 bytes.
  - Frame count >= 10.
  - Valid header (detectable by `opencv` or `ffmpeg`).
  - Not a constant/black frame (variance > threshold).

### 4. EvaluationReport
The structured output of the CPU-tractable evaluation (SSIM, Optical Flow).
- **Type**: JSON object.
- **Fields**:
  - `video_path`: String.
  - `metrics`: Object containing SSIM (Temporal Consistency) and Optical Flow (Motion Activity) scores.
  - `reference_claims`: Object containing textual claims from the paper (e.g., "smooth motion", "high fidelity") for context. **Note: No numeric comparison is performed.**
  - `status`: String ("PASS", "FAIL", "SKIP").
  - `notes`: String (human-readable explanation, including "Aesthetic Quality: Unmeasurable on CPU" if applicable).

## Data Flow

1.  **Input**: `InferenceConfig` + `ModelCheckpoint`
2.  **Process**: `Inference Engine` -> `GeneratedVideo`
3.  **Process**: `GeneratedVideo` -> `Validation Engine` -> `EvaluationReport`
4.  **Output**: `EvaluationReport` (JSON) + `GeneratedVideo` (MP4)

## Contracts (Schemas)

The following schemas are defined in the `contracts/` directory to be used for automated validation.
