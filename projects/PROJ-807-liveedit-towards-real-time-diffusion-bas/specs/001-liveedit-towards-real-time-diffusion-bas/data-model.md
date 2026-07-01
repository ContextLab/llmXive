# Data Model: LiveEdit

## Overview

This document defines the data structures for the LiveEdit validation pipeline, including input video/mask definitions, intermediate processing states, and final benchmark outputs. The model is designed to be lightweight to fit within the available RAM constraint.

## Input Data Model

### Video Frame Stream
The input is not a single monolithic object but a **stream of frames** processed in chunks.

*   **Representation**: `numpy.ndarray` (H, W, 3) - uint8, RGB.
*   **Chunking**: Frames are grouped into fixed-duration temporal chunks.
*   **Memory Footprint**: 30 frames * 720p * 3 bytes ≈ 46 MB per chunk.

### Mask Definition
A binary mask corresponding to the video frames.

*   **Representation**: `numpy.ndarray` (H, W, 1) - uint8 (0 or 255).
*   **Alignment**: Must match the resolution and frame count of the input video.
*   **Missing Handling**: If a mask is missing for a frame, the system defaults to a "no-op" (zero mask) or fails gracefully.

### Static Calibration Video
A video with identical frames (or a static scene) used to measure the pipeline's inherent noise floor.

*   **Representation**: `numpy.ndarray` (H, W, 3) - uint8, RGB.
*   **Usage**: Passed through the pipeline to calculate `noise_floor_std`.

## Output Data Model

### Benchmark Result
A JSON object capturing the performance and quality metrics, including relative comparisons.

*   **Schema**: `contracts/benchmark_result.schema.yaml`
*   **Fields**:
    *   `run_id`: Unique identifier for the run.
    *   `input_video`: Path to input.
    *   `total_frames`: Integer.
    *   `total_time_seconds`: Float.
    *   `fps`: Float (calculated for Distilled model).
    *   `baseline_fps`: Float (calculated for Baseline model).
    *   `relative_speedup`: Float (Baseline FPS / Distilled FPS).
    *   `background_psnr`: Float (Distilled Output vs Baseline Output).
    *   `baseline_psnr`: Float (Baseline Output vs Baseline Output - expected to be high).
    *   `background_ssim`: Float (Distilled vs Baseline).
    *   `noise_floor_std`: Float (Standard deviation of frame differences in static video).
    *   `flicker_score`: Float (Output variance / noise_floor_std).
    *   `chunk_boundary_score`: Float (Boundary difference vs global variance).
    *   `status`: "PASS" | "FAIL".
    *   `error_message`: String (if status is FAIL).

### Output Video Manifest
A manifest file listing the generated artifacts.

*   **Schema**: `contracts/output_manifest.schema.yaml`
*   **Fields**:
    *   `output_video_path`: Path to the generated edited video.
    *   `input_video_path`: Path to the original.
    *   `frame_count`: Integer.
    *   `resolution`: "720p" | "1080p" | etc.
    *   `processing_chunks`: Integer (number of chunks processed).

## Contracts

### Benchmark Result Schema

```yaml
$schema: http://json-schema.org/draft-07/schema#
type: object
properties:
  run_id:
    type: string
    description: "Unique identifier for the benchmark run"
  input_video:
    type: string
    description: "Path to the input video file"
  total_frames:
    type: integer
    description: "Total number of frames processed"
  total_time_seconds:
    type: number
    description: "Total execution time in seconds"
  fps:
    type: number
    description: "Frames per second achieved by the Distilled model"
  baseline_fps:
    type: number
    description: "Frames per second achieved by the Baseline model"
  relative_speedup:
    type: number
    description: "Ratio of Baseline FPS to Distilled FPS (target: >= 1.0)"
  background_psnr:
    type: number
    description: "PSNR between Distilled Output Background and Baseline Output Background"
  baseline_psnr:
    type: number
    description: "PSNR between Baseline Output Background and Baseline Output Background (reference)"
  background_ssim:
    type: number
    description: "SSIM between Distilled Output Background and Baseline Output Background"
  noise_floor_std:
    type: number
    description: "Standard deviation of frame differences in the static calibration video"
  flicker_score:
    type: number
    description: "Ratio of Output background variance to noise_floor_std (target: < 3.0)"
  chunk_boundary_score:
    type: number
    description: "Difference at chunk seams normalized by global variance"
  status:
    type: string
    enum:
      - PASS
      - FAIL
    description: "Overall validation status"
  error_message:
    type: string
    description: "Error details if status is FAIL"
required:
  - run_id
  - input_video
  - total_frames
  - total_time_seconds
  - fps
  - baseline_fps
  - relative_speedup
  - background_psnr
  - baseline_psnr
  - background_ssim
  - noise_floor_std
  - flicker_score
  - chunk_boundary_score
  - status
```

### Output Manifest Schema

```yaml
$schema: http://json-schema.org/draft-07/schema#
type: object
properties:
  output_video_path:
    type: string
    description: "Path to the generated edited video"
  input_video_path:
    type: string
    description: "Path to the original input video"
  frame_count:
    type: integer
    description: "Number of frames in the output video"
  resolution:
    type: string
    description: "Resolution of the video (e.g., 720p)"
  processing_chunks:
    type: integer
    description: "Number of chunks processed"
required:
  - output_video_path
  - input_video_path
  - frame_count
  - resolution
  - processing_chunks
```
