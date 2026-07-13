# Data Model: llmXive follow-up: extending "ABot-Earth 0.5: Generative 3D Earth Model"

## Overview
This document defines the data structures, schemas, and storage formats used throughout the `001-generative-3d-earth-fidelity` feature. All data is stored in `projects/PROJ-988-llmxive-follow-up-extending-abot-earth-0/data/`.

## Entities & Relationships

### 1. DegradedScene
Represents a satellite image region with applied synthetic degradation.
*   **Source**: Sentinel-2 tile + Synthetic Mask.
*   **Usage**: Input for 3DGS generation.
*   **Attributes**:
    *   `scene_id`: Unique string (e.g., `S2_T32TQM_20230101_001`).
    *   `tile_id`: Original Sentinel-2 tile ID.
    *   `patch_coords`: Bounding box (min_x, min_y, max_x, max_y) in UTM.
    *   `degradation_type`: Enum (`low_res`, `cloud`, `temporal`, `mixed`).
    *   `nnf`: Normalized Noise Fraction (float, 0.0 to 1.0). **Defined as weighted sum of degradation parameters (cloud_opacity, downscale_factor, blur_sigma), NOT derived from ground truth.**
    *   `seed`: Random seed used for reproducibility.
    *   `urban_density_bin`: String (`low`, `medium`, `high`) used as random effect in LMM.
    *   `image_path`: Relative path to the degraded image file.
    *   `mask_path`: Relative path to the cloud mask file.

### 2. GroundTruthLiDAR
Represents the independent, high-fidelity point cloud.
*   **Source**: OpenTopography.
*   **Usage**: Reference for Chamfer Distance and geometric validation.
*   **Attributes**:
    *   `lidar_id`: Unique identifier.
    *   `scene_id`: Foreign key to `DegradedScene`.
    *   `point_cloud_path`: Relative path to `.las` or `.ply` file.
    *   `alignment_error`: Float (meters), computed during alignment.
    *   `status`: Enum (`valid`, `excluded`, `misaligned`).

### 3. ReconstructedScene
Represents the 3D Gaussian Splatting output.
*   **Source**: 3DGS Pipeline (Baseline or Inpainted).
*   **Usage**: Input for fidelity metrics.
*   **Attributes**:
    *   `reconstruction_id`: Unique string.
    *   `scene_id`: Foreign key to `DegradedScene`.
    *   `method`: Enum (`baseline`, `inpainting`).
    *   `ply_path`: Relative path to the generated `.ply` file.
    *   `render_config`: Object defining the rendering contract for the inpainting interface.
        *   `resolution`: "512x512"
        *   `format`: "PNG"
        *   `intrinsics`: {"f": 1024, "cx": 256, "cy": 256}
        *   `poses`: List of 8 fixed camera poses.
    *   `generation_time_sec`: Float.
    *   `peak_ram_mb`: Float.
    *   `status`: Enum (`success`, `oom`, `timeout`).

### 4. FidelityMetrics
Quantitative comparison between `ReconstructedScene` and `GroundTruthLiDAR`.
*   **Source**: `compute_metrics.py`.
*   **Usage**: Statistical analysis and threshold detection.
*   **Attributes**:
    *   `metric_id`: Unique string.
    *   `reconstruction_id`: Foreign key to `ReconstructedScene`.
    *   `p_psnr`: Float (Projected PSNR).
    *   `p_ssim`: Float (Projected SSIM).
    *   `chamfer_distance`: Float (meters, normalized).
    *   `geometric_divergence_score`: Float (Chamfer Distance between Baseline and Inpainted geometry). **Used to distinguish recovery from hallucination.**
    *   `improvement_delta`: Float (Inpainted - Baseline).
    *   `statistical_significance`: Boolean (result of Wilcoxon/LMM for the aggregate set).
    *   `power_analysis_notes`: String (e.g., "N=48, d=0.4, power=0.82").

## Storage Formats

*   **Images/Masks**: `.png` (lossless) or `.tiff` (georeferenced).
*   **Point Clouds**: `.ply` (standard 3DGS format) or `.las` (LiDAR).
*   **Metadata/Results**: `.csv` (pandas DataFrame compatible) and `.json` (configuration).
*   **Logs**: `.log` (text) and `.csv` (performance metrics).

## Data Flow Diagram

```mermaid
graph TD
    A[Sentinel-2 Raw] -->|Download & Align| B(DegradedScene)
    C[OpenTopography LiDAR] -->|Download & Align| D(GroundTruthLiDAR)
    B -->|Apply Synthetic Degradation| E[Synthetic Degraded Image]
    E -->|3DGS Baseline| F[ReconstructedScene: Baseline]
    F -->|Render Interface (512x512)| G[Rendered Views]
    G -->|Inpainting Module| H[ReconstructedScene: Inpainted]
    F -->|Compute Metrics| I[FidelityMetrics: Baseline]
    H -->|Compute Metrics| J[FidelityMetrics: Inpainted]
    I & J -->|Statistical Analysis (Wilcoxon/LMM)| K[Threshold Analysis & Plots]
    
    subgraph Performance Instrumentation
    L[Logger] -->|Log RAM/Time| M[performance_log.csv]
    F -.->|Track| L
    H -.->|Track| L
    end
```

## Data Versioning
*   All raw data files in `data/raw/` are checksummed (SHA-256).
*   Derived data in `data/processed/` includes the source checksum in its metadata.
*   No in-place modifications allowed.