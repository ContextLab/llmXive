# Quick Start Guide: llmXive Sparse World Models

This guide provides a step-by-step procedure to reproduce the results of the
"Latent Spatial Memory for Video World Models" extension on a CPU-only environment.

## Prerequisites

- Python 3.11 or higher
- pip package manager
- Minimum 16GB RAM (32GB recommended for full dataset processing)
- Internet connection (for dataset download)

## Step 1: Environment Setup

1. **Clone and Navigate**:
 ```bash
 cd projects/PROJ-843-llmxive-follow-up-extending-latent-spati
 ```

2. **Create Virtual Environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # Linux/macOS
 # or
 venv\Scripts\activate # Windows
 ```

3. **Install Dependencies**:
 ```bash
 pip install -r requirements.txt
 ```
 *Note: This installs `opencv-python`, `torch-cpu`, `datasets`, `scikit-image`, and other required libraries.*

## Step 2: Data Preparation (User Story 1)

1. **Download RealEstate10K**:
 ```bash
 python code/data/download.py
 ```
 This script fetches the dataset from Hugging Face and validates the URL.
 Output: `data/raw/realestate10k/`

2. **Stratify Dataset**:
 ```bash
 python code/data/stratify.py
 ```
 This calculates motion and texture metrics, stratifying sequences into 4 subsets
 (Static-High, Static-Low, Fast-High, Fast-Low).
 *Enforcement: Aborts if any stratum has < 50 sequences.*
 Output: `data/stratified/`

3. **Extract Sparse Features**:
 ```bash
 python code/data/extract_features.py
 ```
 Extracts SIFT/ORB descriptors and coordinates. Handles memory limits by
 switching to sequential processing if RAM > 6GB.
 Output: `data/features/` (`.npy` files)

## Step 3: Geometry & Warping (User Story 2)

1. **Run Epipolar Solver**:
 ```bash
 python code/geometry/solver.py
 ```
 Computes Fundamental Matrices and 3D points. Flags "Unsolvable" sequences
 and logs them to `data/results/unsolvable_sequences.json`.
 Output: Intermediate 3D point files.

2. **Perform Latent Warping**:
 ```bash
 python code/geometry/warp.py
 ```
 Applies CPU-based RBF interpolation to fill occlusions.
 Output: Warped frame data.

3. **Aggregate Warped Frames**:
 ```bash
 python code/geometry/aggregate_warps.py
 ```
 Compiles all warped frames into a single artifact.
 Output: `data/results/sparse_warped_frames.npy`

## Step 4: Evaluation & Metrics (User Story 3)

1. **Download Dense Baseline**:
 ```bash
 # This script strictly downloads the pre-computed baseline.
 # If unavailable, it aborts.
 python code/eval/download_baseline.py
 ```
 Output: `data/raw/dense_baseline_frames.npy`

2. **Compute Metrics**:
 ```bash
 python code/eval/metrics.py
 ```
 Calculates WorldScore, Sparse-Consistency Score, and FID.
 Output: `data/results/metrics_raw.json`

3. **Statistical Analysis (ANOVA)**:
 ```bash
 python code/eval/anova.py
 ```
 Performs Two-Way ANOVA on metrics vs. Scene Dynamics and Texture Level.
 Output: `data/results/anova_results.json`

4. **Sensitivity Analysis**:
 ```bash
 python code/eval/sensitivity.py
 ```
 Sweeps RANSAC thresholds to report stability.
 Output: `data/results/sensitivity_results.json`

## Step 5: Final Report Generation

1. **Orchestrate & Aggregate**:
 ```bash
 python code/main.py
 ```
 This script:
 - Consumes outputs from all previous steps.
 - Parses memory profiler logs.
 - Aggregates metrics, ANOVA, and sensitivity results.
 - Writes the final `data/results/metrics.json`.

2. **Generate Verification Report**:
 ```bash
 python code/eval/report.py
 ```
 Reads `data/results/metrics.json`, compares inference time reduction against
 the 40% threshold, and generates the final hypothesis verification document.
 Output: `data/results/hypothesis_verification.md`

## Verification

To verify the end-to-end reproducibility:

1. Check that `data/results/hypothesis_verification.md` exists.
2. Open the file and confirm the "Inference Time Reduction" section shows `Pass` or `Fail`.
3. Ensure `data/results/metrics.json` contains valid numeric values for WorldScore and FID.

## Troubleshooting

- **Out of Memory (OOM)**: The scripts automatically detect high RAM usage and switch to sequential processing. If issues persist, reduce the `MEMORY_LIMIT_GB` in `code/config.py`.
- **Dataset Download Failures**: Ensure internet connectivity and that the Hugging Face dataset `realestate10k` is accessible.
- **Unsolvable Sequences**: If many sequences are flagged as "Unsolvable", check the `data/results/unsolvable_sequences.json` for low-texture sequences.