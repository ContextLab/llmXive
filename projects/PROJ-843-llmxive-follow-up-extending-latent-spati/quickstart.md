# Quickstart Guide: llmXive Follow-up Pipeline

This guide walks you through running the full pipeline on a CPU-only environment.

## 2. Data Preparation
The pipeline expects data in `data/raw/`.
If missing, run:
```bash
python code/data/download.py
```

- Python 3.11+
- 16GB+ RAM
- Internet connection (for dataset download)

## Step 1: Setup Environment

```bash
# Navigate to project root
cd projects/PROJ-843-llmxive-follow-up-extending-latent-spati

# Install dependencies
pip install -r code/requirements.txt

# Initialize data directories
python code/data/setup_data.py
```

## Step 2: Download and Stratify Dataset

```bash
# Download RealEstate10K
python code/data/download.py

# Stratify into 4 subsets
python code/data/stratify.py
```

**Expected Output**:
- `data/stratified/` directory with 4 subfolders (Static-High, Static-Low, Fast-High, Fast-Low)
- Each folder contains N≥50 sequences

## Step 3: Extract Sparse Features

```bash
python code/data/extract_features.py
```

**Expected Output**:
- `.npy` files in `data/features/` containing coordinate/descriptor pairs
- Batch processing triggered if RAM > 6GB

## Step 4: Solve Geometry and Warp

```bash
# Compute fundamental matrix and triangulate
python code/geometry/solver.py

# Perform RBF warping
python code/geometry/warp.py

# Aggregate warped frames
python code/geometry/aggregate_warps.py
```

**Expected Output**:
- `data/results/sparse_warped_frames.npy`
- `data/results/unsolvable_sequences.json` (if any)

## Step 5: Evaluate Metrics

```bash
# Download dense baseline
python code/eval/download_dense_baseline.py

# Compute metrics
python code/eval/metrics.py

# Run ANOVA
python code/eval/anova.py

# Run sensitivity analysis
python code/eval/sensitivity.py
```

**Expected Output**:
- `data/results/metrics.json`
- ANOVA p-values for interaction effects
- Sensitivity sweep results

## Step 6: Generate Final Report

```bash
python code/eval/report.py
```

**Expected Output**:
- `data/results/hypothesis_verification.md`
- Pass/Fail verdict for SC-003 (40% inference time reduction)

## Step 7: Run Full Pipeline (Optional)

```bash
python code/main.py
```

This executes all steps in sequence and aggregates results.

## Validation

```bash
python code/validate_quickstart.py
```

This script verifies:
- All required files exist
- Scripts run without errors
- Output artifacts are generated

## Troubleshooting

### Memory Issues
- If you encounter OOM errors, reduce the batch size or increase RAM.
- The pipeline automatically triggers sequential processing if RAM > 6GB.

### Dataset Download Fails
- Check internet connection.
- Verify URL accessibility: `python code/data/download.py --check-only`

### Feature Extraction Errors
- Ensure OpenCV is properly installed.
- Check that input sequences are valid video files.

### RANSAC Fails
- Low texture sequences may be flagged as "Unsolvable".
- Check `data/results/unsolvable_sequences.json` for details.

## Next Steps

- Review `data/results/hypothesis_verification.md` for final results.
- Analyze ANOVA and sensitivity reports in `data/results/`.
- Extend the pipeline with additional user stories as needed.

## Support

For issues, check the project logs in `data/results/` or review the design documents in `specs/`.