# Quickstart: Evaluating the Impact of Code Generation Models on Code Security

## Prerequisites

- Python 3.11+
- Git
- Sufficient free disk space (for models and data)
- (Optional) Docker (for isolated scanner environments, though CLI tools are preferred)

## Installation

1. **Clone and Setup Environment**
   ```bash
   git clone <repo-url>
   cd projects/PROJ-152-evaluating-the-impact-of-code-generation
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Verify Dependencies**
   Ensure `bandit`, `semgrep`, and `codeql` are installed globally or accessible via PATH.
   ```bash
   bandit --version
   semgrep --version
   codeql --version
   ```

## Running the Pipeline

### Step 1: Download Data & Models
```bash
python code/download.py
# This downloads prompts to data/prompts/ and model weights to ~/.cache/huggingface/
# Note: Handcrafted prompts are generated and checksummed here.
```

### Step 2: Generate Code
```bash
python code/generate.py
# Generates code for all prompts across 3 models.
# Output: data/generated/snippets.csv
# Note: 120s timeout per generation.
```

### Step 3: Run Static Analysis
```bash
python code/analyze.py
# Runs Bandit, Semgrep, CodeQL on generated code.
# Output: data/findings/raw_findings.csv
# Note: 300s timeout per scan.
```

### Step 4: Compute Metrics & Statistics
```bash
python code/metrics.py
python code/stats.py
# Output: data/results/model_summary.csv, data/results/statistical_results.csv
# Note: Includes FPR correction from calibration step.
```

### Step 5: Generate Visualizations
```bash
python code/viz.py
# Output: data/results/boxplot.png, data/results/heatmap.png
```

### Step 6: View Results
- **Summary Table**: `data/results/model_summary.csv`
- **Statistical Tests**: `data/results/statistical_results.csv`
- **Plots**: `data/results/boxplot.png`, `data/results/heatmap.png`
- **Run Summary**: `data/results/run_summary.csv` (SC-005)

## Testing

Run the integration test suite on a subset of prompts.:
```bash
pytest tests/integration/test_pipeline_subset.py -v
```

## Troubleshooting

- **OOM Errors**: Ensure models are loaded sequentially. Check `config.py` for `batch_size=1`. Reduce prompt count if necessary.
- **Scanner Failures**: Logs are written to `data/logs/scanner_errors.log`.
- **Timeouts**: Adjust `MAX_GENERATION_TIME` or `MAX_SCAN_TIME` in `config.py` if necessary (default values are 120s and 300s respectively).
