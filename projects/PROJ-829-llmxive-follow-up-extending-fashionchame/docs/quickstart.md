# Quickstart Guide: FashionChameleon Text-Driven Adapter Benchmark

This guide explains how to run the full benchmark pipeline for the FashionChameleon project. The benchmark evaluates the fidelity of garment attribute preservation when switching from image-based to text-based reference inputs using the DeepFashion2 dataset. [UNRESOLVED-CLAIM: c_f4e8a734 — status=not_enough_info]

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- At least 16GB RAM (streaming mode reduces this requirement)
- CPU-only execution (no GPU required)

## 1. Environment Setup

### Clone and Navigate
```bash
git clone <repository-url>
cd PROJ-829-llmxive-follow-up-extending-fashionchame
```

### Install Dependencies
```bash
pip install -r code/requirements.txt
```

The `requirements.txt` includes:
- `torch` (CPU version)
- `transformers`
- `opencv-python`
- `scikit-learn`
- `scipy`
- `datasets` (Hugging Face)
- `lpips`
- `pandas`
- `pyyaml`
- `jsonschema`
- `psutil`

### Verify Installation
```bash
python -c "import torch, transformers, cv2, datasets; print('All dependencies installed successfully')"
```

## 2. Directory Structure

The project expects the following directory structure (created by T001):
```
code/
├── src/
│ ├── adapters/
│ ├── data/
│ ├── metrics/
│ ├── pipeline/
│ └── stats/
├── scripts/
├── config/
├── tests/
├── data/
│ ├── raw/
│ └── processed/
└── docs/
```

If directories are missing, run:
```bash
python code/setup_data_dirs.py
python code/setup_test_dirs.py
```

## 3. Configuration

The benchmark uses `code/config/settings.yaml` for all configurable parameters:
- `seed`: Random seed for reproducibility (default: 42)
- `streaming_chunk_size`: Number of samples per streaming batch (default: 100)
- `latency_threshold_ms`: Maximum allowed inference time per frame in ms (default: 50)
- `optical_flow_threshold`: Threshold for motion label classification (default: 0.05)
- `vlm_confidence_threshold`: Minimum VLM confidence for sample inclusion (default: 0.8)

Modify these values as needed before running the benchmark.

## 4. Running the Full Benchmark

The main entry point is the `run_full_benchmark.py` script:

```bash
cd code
python scripts/run_full_benchmark.py
```

### What the Script Does

1. **Data Loading**: Streams the DeepFashion2 dataset using Hugging Face `datasets` library with memory-efficient chunking.
2. **Feasibility Filtering**: Filters samples based on garment feature classes (color, pattern, texture) and motion labels derived from optical flow magnitude.
3. **VLM Verification**: Uses BLIP-Large to verify prompt-image alignment, excluding low-confidence samples.
4. **Stratified Subset Selection**: Creates a balanced benchmark subset ensuring representation across all garment feature classes.
5. **Baseline Execution**: Runs the original image-driven adapter on the subset.
6. **Text-Adapter Execution**: Runs the text-driven adapter on the same subset.
7. **Fidelity Scoring**: Computes LPIPS and SSIM metrics for both baseline and text-adapter outputs.
8. **Latency Measurement**: Measures inference time per frame and checks against the 50ms threshold.
9. **Statistical Analysis**: Performs ANOVA and Bonferroni correction to determine significance of fidelity differences.
10. **Sensitivity Analysis**: Sweeps optical flow thresholds to assess robustness.
11. **Report Generation**: Aggregates all results into structured JSON and CSV reports.

### Expected Outputs

After successful completion, the following files will be generated in `data/processed/`:

- `filtered_subset_manifest.json`: List of samples included in the benchmark after filtering.
- `fidelity_report.json`: Aggregated fidelity scores (LPIPS, SSIM) by garment feature class.
- `latency_report.json`: Inference timing statistics and pass/fail status.
- `sensitivity_analysis.csv`: False positive/negative rates across different optical flow thresholds.
- `manifest.json`: Content hashes for all generated artifacts.

## 5. Individual Component Testing

### Verify Data Loader Streaming
```bash
python code/scripts/verify_loader_streaming.py
```
This script verifies that the DeepFashion2 loader can stream 100+ records without OOM errors.

### Run Unit Tests
```bash
pytest code/tests/unit/ -v
```

### Run Integration Tests
```bash
pytest code/tests/integration/ -v
```

## 6. Expected Runtime

- **Full Benchmark**: ~2-4 hours on CPU (depending on dataset subset size)
- **Memory Usage**: Peak ~6.5GB (triggers batch processing via streaming)
- **Latency Target**: <50ms per frame average

## 7. Troubleshooting

### "Module not found" Errors
Ensure you are running from the `code/` directory or adjust PYTHONPATH:
```bash
export PYTHONPATH=$(pwd)/code:$PYTHONPATH
```

### DeepFashion2 Download Fails
The script requires internet access to fetch the DeepFashion2 dataset from Hugging Face. Verify your network connection and that the dataset ID `DeepFashion2` is accessible.

### OOM Errors
{{claim:c_cbcc0397}} If issues persist, reduce `streaming_chunk_size` in `config/settings.yaml`.

### VLM Model Not Found
The BLIP-Large model is downloaded automatically on first run. This may take several minutes. Ensure sufficient disk space (~2GB for model weights).

## 8. Output Interpretation

### fidelity_report.json
```json
{
 "color": {
 "mean_lpips": 0.12,
 "mean_ssim": 0.85,
 "relative_loss_percent": 5.2
 },
 "pattern": {
 "mean_lpips": 0.18,
 "mean_ssim": 0.79,
 "relative_loss_percent": 12.4
 },
 "texture": {
 "mean_lpips": 0.15,
 "mean_ssim": 0.82,
 "relative_loss_percent": 8.1
 }
}
```

Higher `relative_loss_percent` indicates greater fidelity degradation for that attribute when using text references.

### sensitivity_analysis.csv
Columns: `threshold`, `fp_rate`, `fn_rate`
Use this to identify the optimal optical flow threshold for motion label classification.

## 9. Next Steps

After running the benchmark:
1. Review `fidelity_report.json` to identify which garment attributes degrade most.
2. Check `latency_report.json` to ensure real-time performance requirements are met.
3. Analyze `sensitivity_analysis.csv` to validate the robustness of motion filtering.
4. Run statistical significance tests (included in the benchmark output) to confirm findings.

For detailed API documentation, refer to the docstrings in each module under `code/src/`.