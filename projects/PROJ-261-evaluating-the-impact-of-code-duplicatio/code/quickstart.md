# Quickstart Guide: Evaluating the Impact of Code Duplication on LLM Code Understanding

This guide provides step-by-step instructions to run the complete pipeline for evaluating how code duplication affects LLM code understanding.

## Prerequisites

- Python 3.11+
- 16GB+ RAM recommended
- Internet connection for dataset download
- (Optional) GPU with 16GB+ VRAM for faster model inference

## Setup

1. **Clone and navigate to project:**
 ```bash
 cd projects/PROJ-261-evaluating-the-impact-of-code-duplication
 ```

2. **Create virtual environment and install dependencies:**
 ```bash
 python -m venv.venv
 source.venv/bin/activate # On Windows:.venv\Scripts\activate
 pip install -r requirements.txt
 ```

3. **Install pre-commit hooks:**
 ```bash
 pre-commit install
 ```

## Execution Pipeline

Run the following commands in order to execute the full analysis pipeline:

```bash
# Step 1: Download and prepare raw data
python code/data_loader.py

# Step 2: Compute clone density metrics
python code/ast_cloner.py

# Step 3: Compute model perplexity scores
python code/model_metrics.py

# Step 4: Evaluate bug detection accuracy
python code/bug_detection.py

# Step 5: Perform correlation analysis
python code/correlation_analysis.py

# Step 6: Validate segment count threshold (SC-003)
python code/segment_count_validator.py

# Step 7: Generate visualizations
python code/visualization.py

# Step 8: Compute checksums for all artifacts
python code/checksum_manifest.py
```

## Output Artifacts

The pipeline produces the following artifacts:

- `data/raw/github-code-sample.csv` - Raw code corpus (500MB subset)
- `data/processed/clone_metrics.csv` - Clone density per segment
- `data/processed/perplexity_scores.csv` - Model perplexity per segment
- `data/processed/bug_detection_results.csv` - Bug detection accuracy per segment
- `data/analysis/correlation_results.csv` - Spearman correlation results
- `data/analysis/figures/` - Visualization plots (PNG & PDF)
- `data/parse_failures.csv` - Logs of files that failed to parse
- `artifact_hashes.json` - SHA-256 checksums of all output files

## Validation

Run the validation script to ensure all required outputs were generated:

```bash
python code/quickstart_validation.py
```

This script verifies:
- All required CSV files exist
- Files contain expected columns
- Segment count threshold (≥1000) is met
- No NaN/Inf values in critical columns

## Troubleshooting

### Dataset Download Fails
- Check internet connection
- Ensure HuggingFace token is set if required: `export HF_TOKEN=your_token`
- Try reducing sample size in `code/config.py`

### Model Loading Fails
- Ensure `bitsandbytes` is installed correctly
- Check GPU memory if using CUDA
- For CPU-only environments, ensure model quantization is enabled

### Parse Failures
- Check `data/parse_failures.csv` for list of problematic files
- Verify Python syntax in raw data files
- Adjust AST parsing configuration in `code/config.py`

## Parallel Execution

The following steps can be run in parallel:
- `data_loader.py` (once, before others)
- `ast_cloner.py` and `model_metrics.py` (after data download)
- `bug_detection.py` (after clone metrics computed)
- `correlation_analysis.py` (after all metrics computed)
- `visualization.py` (after correlation results)

## Performance Expectations

- Raw data download: ~5-10 minutes (500MB)
- Clone density computation: ~30-60 minutes (CPU)
- Perplexity scoring: ~1-2 hours (CPU) or ~15-30 minutes (GPU)
- Bug detection: ~30-60 minutes (CPU)
- Correlation analysis: ~5 minutes
- Visualization generation: ~2 minutes

Total runtime: ~3-5 hours on standard hardware.