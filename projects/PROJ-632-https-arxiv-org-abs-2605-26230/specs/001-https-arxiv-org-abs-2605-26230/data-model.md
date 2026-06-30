# Data Model: Reproduce & Validate Geometry-Aware Representation Denoising (GARD)

## 1. Overview

This document defines the data structures for input datasets, intermediate processing, and output artifacts for the GARD reproduction pipeline. The model is designed to be lightweight, compatible with CPU-only execution, and strictly validated against the spec's success criteria.

## 2. Input Data Model

### 2.1 Sample Dataset Structure
The input dataset is expected to be a directory structure containing multi-view images. The directory MUST conform to the `gard_input.schema.yaml` contract.

```text
data/da3_sample/
├── view_001.png          # Input degraded RGB image
├── view_002.png
├── ...
├── depth_001.npy         # (Optional) Ground truth depth if available
└── metadata.json         # (Optional) Scene parameters
```

**Schema Constraints**:
- **Image Format**: `.png` or `.jpg`.
- **Resolution**: Must be ≤ 640x480 to fit RAM constraints.
- **Naming Convention**: `view_{id}.ext`.
- **Validation**: The `src/validators.py` script MUST validate the directory against `gard_input.schema.yaml` before inference. If validation fails, the pipeline aborts with a "Scientific Null" error.

### 2.2 Configuration
```yaml
config:
  input_path: "data/da3_sample"
  output_path: "outputs"
  max_memory_gb: 7
  timeout_hours: 6
  force_cpu: true
  enable_blur_baseline: true  # For control group
```

## 3. Output Data Model

### 3.1 Restored Images
- **Format**: PNG (lossless compression preferred for validation).
- **Location**: `outputs/images/restored_{id}.png`.
- **Properties**: Same resolution as input, 3 channels (RGB).

### 3.2 3D Geometry
- **Format**: PLY (Polygon File Format) or OBJ.
- **Location**: `outputs/geometry/scene.ply`.
- **Properties**:
  - Non-empty vertex list.
  - Valid normals (if applicable).
  - Loadable by MeshLab/Open3D.

## 4. Intermediate Data

- **Processed Batches**: Temporary numpy arrays held in RAM.
- **Logs**: `logs/inference.log` containing step-by-step execution and error traces.
- **Baseline Images**: `outputs/baseline/blur_{id}.png` (Gaussian blurred input).

## 5. Data Flow

1.  **Load**: Read images from `data/da3_sample` (validate against schema).
2.  **Preprocess**: Resize (if >640px), normalize, convert to tensor (CPU).
3.  **Baseline**: Generate Gaussian Blur of input.
4.  **Inference**: Pass through GARD model.
5.  **Postprocess**: Denormalize, convert to image/mesh.
6.  **Validate**: Compute LPIPS/NIQE against Input and Baseline.
7.  **Save**: Write to `outputs/`.