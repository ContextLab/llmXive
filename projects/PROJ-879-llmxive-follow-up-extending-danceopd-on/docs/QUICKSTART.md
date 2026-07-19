# Quickstart Guide

## Prerequisites

- Python 3.11+
- pip
- At least 7GB available RAM
- (Optional) GPU for teacher inference

## Step-by-Step Guide

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup directory structure
python code/setup_data_dirs.py
```

### 2. Configure Project

Edit `code/utils/config.py` to set:
- `TEACHER_WEIGHTS_PATH`: Path to teacher model weights
- `SEED`: Random seed for reproducibility
- `DATA_PATH`: Base path for data directories
- Hyperparameters (max_depth range, sample sizes, etc.)

### 3. Verify Weights

```bash
python code/utils/check_weights.py
```
This verifies that required weight files exist and have correct checksums.

### 4. Generate Teacher Ground Truth (User Story 1)

```bash
python code/00_data_generation.py
```

**What happens**:
1. Streams samples from ImageNet-1K and LAION-400M
2. Runs teacher model inference (GPU or verified fallback)
3. Extracts features and creates `teacher_routing_dataset.parquet`

**Expected outputs**:
- `data/raw/imageNet_samples.parquet`
- `data/raw/laion_samples.parquet`
- `data/processed/teacher_routing_dataset.parquet`

**Note**: If GPU is unavailable, ensure a verified `data/raw/teacher_ground_truth.parquet` exists.

### 5. Train Decision Trees (User Story 2)

```bash
python code/01_train_trees.py
```

**What happens**:
1. Loads the teacher routing dataset
2. Splits into train/test sets
3. Trains decision trees with `max_depth` from 2 to 20
4. Evaluates routing consistency (accuracy)
5. Saves models and results

**Expected outputs**:
- `models/trained_trees/` (individual `.pkl` files)
- `data/results/tree_accuracy.csv`

### 6. Evaluate Fidelity (User Story 3)

```bash
python code/02_evaluate_fidelity.py
```

**What happens**:
1. Loads trained trees and dataset
2. Generates images using tree-predicted routing
3. Generates images using teacher routing (baseline)
4. Computes FID and CLIP scores
5. Performs statistical tests (bootstrap, t-test)
6. Generates summary report

**Expected outputs**:
- `data/results/fidelity_metrics.csv`
- `data/results/statistical_tests.json`
- `data/results/fidelity_summary.md`
- `data/results/` (generated images with prefixes `tree_depth{D}_sample_{idx}.png` and `teacher_baseline_sample_{idx}.png`)

**Note**: This step has a 6-hour timeout. Partial results are saved if the limit is reached.

### 7. Version Artifacts

```bash
python code/03_versioning.py
```

**What happens**:
- Calculates SHA256 checksums for all artifacts
- Updates `state/` directory with version metadata

### 8. Run Tests

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/
```

## Troubleshooting

### "No real data source available"
- Ensure Hugging Face datasets are accessible
- Check network connectivity
- Verify dataset IDs in `_data_streaming.py`

### "GPU unavailable and no fallback"
- Provide a verified `data/raw/teacher_ground_truth.parquet`
- Or run with a GPU-enabled environment

### "Statistical power insufficient"
- The pipeline will save partial results
- Consider increasing sample size if resources allow

### "Timeout reached"
- Partial results are saved to `data/results/partial_results.json`
- Review the status and consider adjusting parameters

## Expected Runtime

- **Data Generation**: 1-3 hours (depends on network and sample size)
- **Tree Training**: 10-30 minutes
- **Fidelity Evaluation**: 2-4 hours (depends on dataset size)
- **Total**: ~4-8 hours (within 6-hour limit with optimizations)

## Expected Resource Usage

- **RAM**: ≤7GB peak
- **Disk**: ~10-20GB (depending on dataset size)
- **CPU**: Multi-core usage during training and evaluation

## Next Steps

After completing the quickstart:
1. Review `data/results/fidelity_summary.md` for findings
2. Analyze `data/results/tree_accuracy.csv` for optimal tree depth
3. Explore `docs/PROJECT_OVERVIEW.md` for research context
4. Consider extending with additional user stories or optimizations