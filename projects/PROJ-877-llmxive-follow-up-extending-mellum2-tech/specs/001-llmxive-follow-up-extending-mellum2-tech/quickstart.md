# Quickstart: llmXive follow-up: extending "Mellum2 Technical Report"

## 1. Prerequisites

- **OS**: Linux (Ubuntu 22.04 or similar).
- **Python**: 3.11+.
- **Dependencies**:
  - `codeql` CLI (for static analysis).
  - `tree-sitter` (for parsing).
  - `git`, `make`.
- **Hardware**: CPU-only (2+ cores, 7+ GB RAM). No GPU required.

## 2. Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install CodeQL (if not present)
# Follow instructions at: https://codeql.github.com/docs/codeql-cli/getting-started-with-the-codeql-cli/
```

## 3. Running the Pipeline

The pipeline is executed via `code/main.py`. It handles downloading, analysis, inference, and reporting.

```bash
# Run the full pipeline
python code/main.py --sample-size 500 --languages python,java

# Options:
#   --sample-size: Number of repos to sample (default: 500)
#   --languages: Comma-separated list of languages (default: python,java)
#   --model: HuggingFace model ID (default: TinyLlama/TinyLlama-1.1B-Chat-v1.0)
#   --skip-inference: Skip LLM step (for static analysis testing only)
```

## 4. Output

Upon successful completion, the following artifacts are generated in `data/results/`:

- `correlation_report.json`: Correlation coefficients, p-values, and FDR corrections (based on Repository Aggregates).
- `threshold_report.json`: Identified thresholds, slopes, and sensitivity analysis.
- `plots/`:
  - `correlation_scatter.png`: Scatter plot with regression lines (x=Repo Mean Complexity, y=Repo Mean Loss).
  - `threshold_sensitivity.png`: Sensitivity analysis plot.
- `pipeline_log.txt`: Detailed execution log including skipped files and errors.

## 5. Troubleshooting

- **OOM Error**: Reduce `--sample-size` or ensure `codeql` file limits are enforced.
- **CodeQL Failure**: Ensure `codeql` is in PATH and has sufficient memory.
- **Dataset Download Timeout**: Check network connectivity; the script retries automatically.
- **Model Not Found**: Ensure `TinyLlama-1.1B` is accessible via HuggingFace.