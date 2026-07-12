# Data Model: llmXive follow-up: extending "ABot-Earth 0.5: Generative 3D Earth Model"

## Overview
This document defines the data structures, schemas, and storage formats for the project. All data is stored in the `data/` directory, with raw data preserved and processed data versioned. The schemas in `contracts/` are the authoritative definitions for these entities.

## Key Entities

### 1. DegradedScene
Represents a satellite image region with applied synthetic degradation.
- **Source**: `data/processed/degraded_scenes/`
- **Format**: `.npy` (image data), `.json` (metadata)
- **Attributes**:
  - `scene_id`: Unique string identifier.
  - `original_tile_id`: Sentinel-2 tile ID.
  - `degradation_type`: Enum ["low_res", "cloud", "temporal", "mixed"].
  - `nnf`: Normalized Noise Fraction (float, 0.0-1.0).
  - `resolution_m`: Pixel resolution in meters (float).
  - `cloud_opacity`: Opacity of applied cloud mask (float, 0.0-1.0).
  - `seed`: Random seed used for reproducibility.
  - `city`: Source city (e.g., "NYC", "LA") from `city_list.txt`.

### 2. GroundTruthLiDAR
Independent high-fidelity point cloud reference.
- **Source**: `data/raw/lidar/`
- **Format**: `.las` or `.laz` (compressed LAS), converted to `.ply` for processing.
- **Attributes**:
  - `scene_id`: Matches the DegradedScene.
  - `projection`: CRS string (e.g., "EPSG:32610").
  - `point_count`: Integer.
  - `bounds`: Bounding box (min_x, min_y, min_z, max_x, max_y, max_z).
  - `acquisition_date`: Date of LiDAR acquisition (YYYY-MM-DD).
  - `source`: "USGS 3DEP" or "NYC Open Data".

### 3. ReconstructedScene
Output of the 3DGS generation pipeline.
- **Source**: `data/processed/reconstructions/`
- **Format**: `.ply` (Gaussian Splatting format).
- **Attributes**:
  - `scene_id`: Matches input.
  - `method`: Enum ["baseline_3dgs", "inpaint_3dgs"].
  - `num_gaussians`: Integer.
  - `generation_time_sec`: Float.
  - `peak_ram_mb`: Float.

### 4. FidelityMetrics
Quantitative comparison between ReconstructedScene and GroundTruthLiDAR.
- **Source**: `data/results/metrics.csv`
- **Format**: CSV (Comma Separated Values).
- **Attributes**:
  - `scene_id`: String.
  - `method`: Enum ["baseline_3dgs", "inpaint_3dgs"].
  - `chamfer_distance_m`: Float (normalized scale).
  - `ppsnr`: Float (null for temporal mode).
  - `pssim`: Float (null for temporal mode).
  - `nnf`: Float.
  - `degradation_type`: String.
  - `temporal_gap_months`: Integer (months between LiDAR and Image).
  - `is_confounded`: Boolean (true if `temporal_gap_months` > 12).
  - `timestamp`: ISO8601 timestamp.

## Data Flow

1.  **Ingestion**: Raw Sentinel-2 and LiDAR downloaded to `data/raw/`.
2.  **Alignment**: `01_data_curation.py` aligns coordinates, outputs `data/processed/aligned_pairs/`.
3.  **Mask Validation**: `02b_validate_masks.py` validates synthetic masks (FR-006).
4.  **Degradation**: `02_degradation_pipeline.py` creates `data/processed/degraded_scenes/`.
5.  **Generation**: `03_3dgs_cpu_inference.py` creates `data/processed/reconstructions/`.
6.  **Evaluation**: `04_metrics_evaluation.py` appends to `data/results/metrics.csv`.
7.  **Analysis**: `05_threshold_analysis.py` reads `metrics.csv`, outputs plots and statistical reports.

## Storage Constraints

- **Raw Data**: Checksummed, immutable.
- **Processed Data**: Overwritten only if the source or parameters change (versioned by hash).
- **Size Limits**:
  - Single `.ply` file < 500 MB.
  - Total `data/` directory < 10 GB (compressed where possible).
  - Memory usage during processing < 6.5 GB.