# Processing Details: Implementation Specifics

This document provides technical details on the implementation of the processing
pipeline, focusing on the specific algorithms, error handling, and validation
logic used.

## 1. Salience Map Generation (DeepGaze II & GBVS)

### 1.1 DeepGaze II Implementation
- **Library**: `ultralytics` (for model loading) and `torch` (for inference).
- **Device Enforcement**: The model is explicitly loaded with `device='cpu'` in
 `code/ingestion/salience_gen.py` to ensure compatibility with CPU-only runners.
- **Memory Monitoring**:
 - Uses `psutil` to track RSS memory in real-time.
 - If memory exceeds 6.5GB, a warning is logged; if it exceeds 7GB, the process
 is terminated (T014).
- **Batch Processing**:
 - Images are processed in batches to manage memory.
 - If a batch exceeds 15 minutes, a `batch_timeout_count` is incremented (T014).
 - Cumulative time is tracked across all batches.

### 1.2 GBVS Fallback Logic
- **Trigger**: Activated only when DeepGaze II raises an exception (e.g., OOM or
 model initialization failure) for a specific image.
- **Algorithm**: Graph-Based Visual Saliency (GBVS) is implemented via `code/ingestion/fallback_heuristic.py`.
- **Validation Metrics**:
 1. **Dimensions**: Output map must match input image resolution.
 2. **Variance**: Map must have non-zero variance (not a uniform gray).
 3. **Mean Value**: Mean salience must be > 0.01.
- **Failure Handling**: If validation fails, the image ID is appended to
 `data/interim/excluded_images.csv` with reason "GBVS_Validation_Fail".

### 1.3 Provenance Tracking
- Every generated map is tagged in `data/processed/salience_maps/metadata.json`
 with the `method` field: either "DeepGaze" or "GBVS" (T016).
- **Success Metric**: Only "DeepGaze" maps count towards the SC-001 success rate.
 GBVS maps are reported separately (T013b).

## 2. Eye-Tracking and Segmentation

### 2.1 YOLOv8 Segmentation
- **Model**: YOLOv8n (nano) for speed and low memory footprint.
- **Class Selection**: Only the `face` class (COCO ID 14) is retained.
- **Weapons Exclusion**:
 - The code explicitly checks for the existence of `specs/.../SCR-002-Exclusion-of-Weapons.md`.
 - If present, it logs "FR-008 (Weapons) skipped per SCR-002" and writes
 `data/interim/weapons_exclusion_flag.json` (T020d).
- **Mask Generation**: Semantic masks are generated as binary arrays and saved
 to `data/interim/face_masks/`.

### 2.2 Fixation Metric Calculation
- **Input**: Raw `eyetracking.tsv` files from `data/raw/[subject_id]/`.
- **ROI Filtering**: Fixations are filtered to those falling within the "Face"
 polygon mask.
- **Metrics**:
 - **First-Fixation Probability**: Proportion of trials where the first fixation
 landed on the face.
 - **Dwell Time**: Total duration of fixations on the face.
 - **Latency**: Time from stimulus onset to first face fixation.

## 3. Statistical Modeling and Validation

### 3.1 Linear Mixed Models (LMM)
- **Library**: `statsmodels` (mixed linear models).
- **Formulas**:
 - **Model A**: `dwell_time ~ salience + (1 | subject_id)`
 - **Model B**: `dwell_time ~ salience + (1 + salience | subject_id)`
- **Exclusion Constraint**: The code asserts that `luminance`, `contrast`, and
 `edge_density` are **not** present in the input dataframe before fitting
 (T032), enforcing SCR-001.
- **Convergence**:
 - If `model.converged` is False, the code logs a warning and retries with
 increased `maxiter` (T046).

### 3.2 Variance Inflation Factor (VIF)
- **Purpose**: Diagnostic only. To prove that salience is not collinear with
 low-level features.
- **Features**: Luminance (mean intensity), Contrast (std dev), Edge Density (Canny).
- **Threshold**: VIF > 5 triggers a hard halt (T030).
- **Implementation**: `code/analysis/vif_calc.py` calculates VIF using the
 `variance_inflation_factor` from `statsmodels.stats.outliers_influence`.

### 3.3 Power Analysis
- **Method**: Simulation-based using `simr`.
- **Effect Size**: Assumes d=0.5 if no pilot data is available (T029a).
- **Sensitivity Sweep**: `code/analysis/lmm_power.py` sweeps effect sizes from
 small to large to determine minimum N required (T045).

## 4. Error Handling and Gates

### 4.1 Data Integrity Gates
- **Synthetic Data Guard**: `code/ingestion/fallback_guard.py` scans for
 `try/except` blocks that return synthetic data. If found, raises `DATA_MISSING_001`.
- **Real Source Verification**: `code/ingestion/verify_real_source.py` validates
 the OpenNeuro checksum before processing (T043).

### 4.2 Processing Gates
- **Power Gate**: `data/interim/power_gate_flag.json` halts T032 if power < 0.8.
- **VIF Gate**: `data/interim/vif_gate_flag.json` halts T032 if VIF > 5.
- **Fallback Threshold**: `data/interim/invalid_fallback_flag.json` halts if
 GBVS fallback > 10% (T018c).
- **Compute Budget**: `data/interim/compute_budget_exceeded.json` halts if
 cumulative time + batch timeouts > 6 hours (T042).

## 5. Output Schema

The final output `data/processed/results.json` follows the schema defined in
`code/contracts/output.schema.yaml`:

```yaml
fields:
 - fixed_effect_estimate: float
 - p_value: float
 - confidence_interval: [float, float]
 - sensitivity_sweep: list
 - disclaimer: string (must contain "correlational only" if p < 0.05)
```

Validation is performed by `code/utils/final_validator.py` (T049).
