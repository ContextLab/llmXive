# Quick Start Guide: Extending TriSplat for CPU-Only Edge Robotics

This guide walks you through setting up and running the CPU-optimized geometry-only 3D reconstruction pipeline.

## Step 1: Environment Setup

### Prerequisites Check
- [ ] Python 3.11 or higher installed
- [ ] At least 6 GB free RAM available
- [ ] At least 14 GB free disk space
- [ ] No GPU required (CPU-only environment)

### Install Dependencies

```bash
# Navigate to project root
cd projects/PROJ-938-llmxive-follow-up-extending-trisplat-sim

# Install required packages
pip install -r code/requirements.txt
```

### (Optional) Setup Development Tools

```bash
pip install ruff black
```

## Step 2: Verify Installation

Run a quick test to ensure all dependencies are correctly installed:

```bash
python -c "import torch; import numpy; import trimesh; print('All imports successful!')"
```

## Step 3: Run a Single Scene (MVP Test)

Before running the full batch, test the pipeline on a single scene:

```bash
python code/cli.py --views 3 --timeout 1800 --seed 42
```

**Expected Output:**
- Data streaming from RealEstate10K
- Progress bar showing scene processing
- Generated mesh file (`.obj` or `.ply`) in the output directory
- Metrics logged to console

**Validation:**
- [ ] Pipeline completes within 30 minutes
- [ ] Valid mesh file is generated
- [ ] No CUDA errors (CPU-only mode)
- [ ] Memory usage stays under 6 GB

## Step 4: Run Full Batch Experiment

Once the single scene test passes, run the full batch experiment:

```bash
# Run with default settings (N=20 scenes, 6-hour timeout)
python code/cli.py --update-state
```

Or run directly with custom parameters:

```bash
python code/experiments/run_batch.py --n-scenes 20 --timeout 21600
```

**What happens:**
1. The pipeline processes 20 scenes across 2, 3, 4, and 5 view configurations
2. Metrics (Chamfer Distance, PSNR) are collected for each scene
3. Statistical analysis identifies the sparsity threshold
4. Benchmark comparison against baseline TriSplat is performed

**Expected Duration:**
- N=20 scenes: ~1-4 hours (depending on hardware)
- N=50 scenes (stretch goal): ~3-6 hours if runtime permits

## Step 5: Generate Reports

After batch completion, generate the final analysis reports:

### 5.1 Generate Benchmark CSV

```bash
python code/experiments/generate_benchmark_csv.py
```

**Output:** `data/processed/benchmark_tradeoff.csv`

### 5.2 Generate Trade-off Plot

```bash
python code/experiments/generate_tradeoff_plot.py
```

**Output:** `data/processed/benchmark_tradeoff_plot.png`

### 5.3 Generate Final Report

```bash
python code/experiments/generate_final_report.py
```

**Output:** `data/processed/final_report.json` and `data/processed/threshold_result.json`

## Step 6: Verify Results

Check the generated artifacts:

```bash
# View the benchmark CSV
head data/processed/benchmark_tradeoff.csv

# View the threshold result
cat data/processed/threshold_result.json

# View the final report
cat data/processed/final_report.json | python -m json.tool
```

**Expected Results:**
- `threshold_result.json` contains the identified sparsity threshold (view count where error exceeds 15%)
- `benchmark_tradeoff_plot.png` shows latency vs. Chamfer Distance curve
- `final_report.json` contains comprehensive statistics and comparative metrics

## Step 7: Run Tests (Optional)

Verify the implementation with the test suite:

```bash
# Run unit tests
python -m pytest tests/unit/ -v

# Run integration tests
python -m pytest tests/integration/ -v

# Run memory usage test specifically
python -m pytest tests/integration/test_memory_limits.py -v
```

## Common Issues and Solutions

### Issue: "Monocular input not supported"
**Solution:** Ensure you specify at least 2 views: `--views 2`

### Issue: "CUDA error"
**Solution:** The pipeline is designed for CPU-only. Ensure no GPU-related environment variables are set.

### Issue: "Dataset download failed"
**Solution:** Check your internet connection. The dataset is streamed from Hugging Face.

### Issue: "Convergence failed"
**Solution:** This is expected for low-texture scenes. A placeholder mesh will be generated with the error flag "LOW_TEXTURE_CONVERGENCE_FAILED" or "TIMEOUT_CONVERGENCE_FAILED".

### Issue: "Memory limit exceeded"
**Solution:** The pipeline uses streaming to minimize memory usage. If you still exceed 6 GB, reduce the number of concurrent scenes or increase system RAM.

## Advanced Usage

### Updating State File
After execution, update the project state with checksums:

```bash
python code/cli.py --update-state
```

This computes SHA-256 hashes of all processed data and updates `state/projects/PROJ-938-llmxive-follow-up-extending-trisplat-sim.yaml`.

### Running with Custom View Counts
Test specific view configurations:

```bash
# Test with 2 views
python code/cli.py --views 2 --timeout 1800

# Test with 5 views
python code/cli.py --views 5 --timeout 1800
```

### Enabling Verbose Logging
Add `--verbose` flag (if implemented) or check the log files in the output directory.

## Next Steps

After completing the quick start:

1. Review the `README.md` for detailed architecture and API documentation
2. Examine the generated reports to understand the sparsity threshold
3. Analyze the trade-off plot to see the latency vs. fidelity relationship
4. Consider extending the pipeline with additional scenes or configurations

## Support

For additional help:
- Refer to the full `README.md`
- Check the test files for usage examples
- Review the error handling documentation in `README.md`

**Happy reconstructing!** 🚀