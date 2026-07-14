# Quickstart Guide for llmXive Follow-up

## Prerequisites
- Python 3.11+
- Install dependencies: `pip install -r requirements.txt`

## Running the Pipeline

The pipeline is orchestrated via `code/main.py`. It supports running specific phases or the full suite.

### Full Execution (End-to-End)

This command runs all phases in order: Data Preparation -> Feature Extraction -> Geometry -> Evaluation -> Aggregation.

```bash
python code/main.py
```

### Specific Phase Execution

You can run individual phases for debugging or incremental development:

```bash
# 1. Prepare and stratify data
python code/main.py --phase data_prepare

# 2. Extract SIFT/ORB features
python code/main.py --phase extract_features

# 3. Compute Geometry (Solver, Warp, Aggregate)
python code/main.py --phase compute_geometry

# 4. Evaluate Metrics (WorldScore, FID, etc.)
python code/main.py --phase evaluate
```

## Deliverables

Upon successful completion, the following artifacts will be generated:

- `data/stratified/`: Stratified video sequences
- `data/features/`: Sparse feature descriptors (.npy)
- `data/results/sparse_warped_frames.npy`: Aggregated warped frames (US2)
- `data/raw/dense_baseline_frames.npy`: Dense baseline for comparison (US3)
- `data/results/metrics.json`: Final aggregated metrics and memory usage (T020)
- `data/results/hypothesis_verification.md`: Final report (T021)

## Validation

To validate the quickstart process:

```bash
python code/validate_quickstart.py
```