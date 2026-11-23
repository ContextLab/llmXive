# Quick Start Guide

## Prerequisites

- Python 3.11+
- 7GB+ available RAM
- CPU-only environment (no CUDA required)
- Internet connection for dataset download

## Installation

```bash
# Clone repository
git clone <repo-url>
cd llmXive-active-learner

# Create virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Validation

### 1. Environment Check
```bash
python code/env_validator.py
```
Should report:
- Python version >= 3.11
- No CUDA available (CPU-only mode)
- All dependencies installed
- Memory limit check passed

### 2. Data Download
```bash
python code/data_loader.py --download
```
Downloads nfcorpus and scifact from BEIR.

### 3. Run Minimal Experiment
```bash
python code/run_pipeline.py --seeds 1 --threshold 0.95
```
Runs one seed with baseline and clustering-aided variants.

## Full Pipeline Execution

```bash
# Run full experiment with 5 seeds and threshold sweep
python code/run_pipeline.py --seeds 5 --sweep

# Generate statistical report
python code/generate_statistical_report.py

# Analyze threshold sensitivity
python code/analyze_threshold_sweep.py
```

## Output Artifacts

After successful execution:

- `data/results/statistical_report.md`: Main results with p-values
- `data/results/threshold_sweep.json`: Threshold sensitivity analysis
- `logs/comparisons.log`: All pairwise comparison logs
- `logs/resources.log`: Runtime and memory usage stats

## Troubleshooting

### Memory Error
If you encounter memory errors:
1. Reduce the number of seeds: `--seeds 2`
2. Use a smaller threshold value (increases clustering)
3. Ensure no other memory-intensive processes are running

### Dataset Download Fails
1. Check internet connection
2. Verify BEIR library is up to date: `pip install --upgrade beir`
3. Check disk space in `data/` directory

### CUDA Detected
This project is CPU-only. If CUDA is detected:
```bash
# Uninstall GPU versions
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

## Next Steps

1. Read `docs/DESIGN.md` for architectural overview
2. Review `docs/ARCHITECTURE.md` for component details
3. Examine `specs/001-llmxive-prp-redundancy/` for requirements
4. Run unit tests: `pytest tests/`
