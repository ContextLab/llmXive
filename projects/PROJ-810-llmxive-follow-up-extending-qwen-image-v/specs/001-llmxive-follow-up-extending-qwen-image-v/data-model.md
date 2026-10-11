# Data Model: llmXive follow-up: extending "Qwen-Image-VAE-2.0 Technical Report"

## Overview
Defines all persistent artifacts exchanged between pipeline stages. All files reside under `data/` and are validated against the JSON‑Schema contracts in `contracts/`.

## Entity Definitions

### 1. RawImageCrop
- **Description**: Cropped region extracted from a source document using ground‑truth bounding boxes.  
- **Fields**:
  - `image_id` (string): Identifier of the source document.  
  - `crop_id` (string): Unique identifier for the crop.  
  - `modality` (string, enum: `"text"`, `"image"`): Ground‑truth label.  
  - `bbox` (array of 4 numbers): `[x1, y1, x2, y2]`.  
  - `pixels` (object): Reference to a NumPy file (`format: "numpy"`; includes `shape` array).  

### 2. LatentVector
- **Description**: High‑dimensional encoding produced by the Qwen‑Image‑VAE‑2.0 encoder.  
- **Fields**:
  - `latent_id` (string): Unique identifier.  
  - `crop_id` (string): Links back to `RawImageCrop`.  
  - `vector` (array of numbers): Float32 latent representation.  
  - `modality` (string, enum: `"text"`, `"image"`).  
  - `encoder_version` (string): Model version tag.  

### 3. Centroid
- **Description**: Mean vector of a modality‑specific cluster.  
- **Fields**:
  - `centroid_id` (string, enum: `"text_centroid"`, `"image_centroid"`).  
  - `vector` (array of numbers).  
  - `n_samples` (integer): Number of vectors aggregated.  

### 4. EditedImage
- **Description**: Image generated after vector arithmetic and decoding.  
- **Fields**:
  - `image_id` (string).  
  - `source_crop_id` (string).  
  - `pixels` (object, same structure as in `RawImageCrop`).  
  - `operation` (string, enum: `"text_swap"`).  
  - `baseline_reconstruction_id` (string).  

### 5. MetricResult
- **Description**: Single metric computation for a given test.  
- **Fields**:
  - `metric_name` (string).  
  - `value` (number).  
  - `p_value` (number, nullable).  
  - `is_significant` (boolean).  
  - `metadata` (object, optional).  

## Data Flow
1. **Ingestion** → `RawImageCrop` (streamed from HF).  
2. **Encoding** → `LatentVector`.  
3. **Clustering** → `Centroid`.  
4. **Editing** → `EditedImage`.  
5. **Evaluation** → `MetricResult`.  

All intermediate files are stored as compressed NumPy (`.npz`) or JSON (`.json`) under `data/interim/` and `data/results/`.

---
