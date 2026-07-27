# Quickstart Guide: Evaluating the Impact of Code Generation Models on Code Vulnerability Density

This guide provides instructions to run the full pipeline, reproduce results, and generate the final report for the `PROJ-497` project.

## Prerequisites

- **Python**: 3.11 or higher
- **System Tools**: `bandit` (Python package), `git`
- **Hardware**: Minimum 7GB RAM (CPU-only mode), ~14GB disk space for datasets and artifacts
- **Internet**: Required for downloading datasets from Hugging Face

## 1. Environment Setup

### Clone and Install Dependencies

```bash
# Ensure you are in the project root
pip install -r requirements.txt
```

The `requirements.txt` includes all necessary dependencies:
- `transformers`, `datasets`: For model loading and dataset management
- `bandit`: For static security analysis
- `scikit-learn`, `statsmodels`, `pandas`: For statistical analysis
- `matplotlib`, `seaborn`: For visualization
- `pyyaml`, `pingouin`: For configuration and statistical tests

### Verify Installation

```bash
python -c "import transformers, datasets, bandit, statsmodels, pandas, matplotlib; print('All dependencies installed successfully.')"
```

## 2. Data Download

The pipeline automatically downloads the HumanEval and MBPP datasets if they are not present.

```bash
python code/main.py --action download
```

**Output**:
- Datasets saved to `data/human/human_eval/` and `data/human/mbpp/`
- SHA-256 checksums verified and stored in `state/artifact_hashes.yaml`

*Note: This step requires an active internet connection.*

## 3. Code Generation

Generate code samples using the specified models (StarCoder and CodeGen) on the HumanEval and MBPP benchmarks.

```bash
python code/main.py --action generate --models StarCoder CodeGen --benchmarks HumanEval MBPP
```

**Parameters**:
- `--models`: Comma-separated list of models to run (default: `StarCoder,CodeGen`)
- `--benchmarks`: Comma-separated list of benchmarks (default: `HumanEval,MBPP`)
- `--seed`: Random seed for reproducibility (default: `42`)

**Process**:
- The script iterates through all tasks in the selected benchmarks.
- For each task, it attempts to generate up to 200 samples until ≥64 valid samples are obtained.
- Valid samples are saved to `data/generated/{model}/{benchmark}/{task_id}/samples/`.

**Output**:
- Generated code files in `data/generated/`
- Generation logs in `logs/generation.log`

## 4. Vulnerability Analysis

Run static analysis using Bandit on all generated and human-written code.

```bash
python code/main.py --action analyze
```

**Process**:
- Scans all `.py` files in `data/generated/` and `data/human/`.
- Uses the configuration defined in `code/config/bandit_config.yaml`.
- Handles syntax errors by skipping files and logging warnings.

**Output**:
- Raw Bandit reports: `data/processed/bandit_raw_reports.json`
- Structured vulnerability reports: `data/processed/vulnerability_reports.json`
- Per-sample statistics: `data/processed/raw_vulnerability_counts.csv`
- Aggregated dataset: `data/processed/aggregated_analysis_dataset.csv`

## 5. Statistical Analysis

Perform comparative statistical analysis (ZINB regression or permutation test fallback).

```bash
python code/main.py --action statistics
```

**Process**:
- Fits a Zero-Inflated Negative Binomial (ZINB) regression model.
- If ZINB fails to converge, falls back to a permutation test.
- Performs stratified analysis by CWE ID with Benjamini-Hochberg correction.
- Calculates False Positive Rates (FPR) using the validator.
- Generates cross-benchmark and cross-model comparisons.

**Output**:
- Statistical results logged to `logs/statistics.log`
- FPR metrics: `data/processed/fpr_metrics.json`
- Final aggregated dataset with effect sizes: `data/processed/aggregated_analysis_dataset.csv`

## 6. Visualization and Reporting

Generate visualizations and the final summary report.

```bash
python code/main.py --action report
```

**Process**:
- Generates boxplots comparing LLM vs. Human vulnerability counts.
- Generates bar charts for top 5 vulnerability types.
- Compiles all statistics, effect sizes, and FPR metrics into a Markdown report.

**Output**:
- Visualizations: `results/` (PNG/SVG files)
- Summary report: `results/summary.md`

## 7. Reproducibility Check

To verify reproducibility, run the pipeline twice with the same seed and compare outputs.

```bash
# Run 1
python code/main.py --seed 42 --action all

# Run 2
python code/main.py --seed 42 --action all

# Compare derived floating-point outputs (must have absolute difference ≤1e-6)
python code/state_utils.py --verify-reproducibility
```

## 8. Testing

Run the full test suite to ensure all components are functioning correctly.

```bash
pytest tests/ -v
```

**Test Categories**:
- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`
- Contract tests: `tests/contract/`

## Troubleshooting

### Memory Errors
If you encounter `MemoryError` during model loading:
- Ensure you are running in CPU-only mode (default).
- Close other memory-intensive applications.
- The pipeline is designed to fit within 7GB RAM limits.

### Dataset Download Failures
If Hugging Face downloads fail:
- Check your internet connection.
- Ensure you have sufficient disk space (~14GB).
- Retry the download command.

### Bandit Analysis Errors
If Bandit fails to parse certain files:
- The script automatically skips files with syntax errors.
- Check `logs/analysis.log` for specific error messages.

## Full Pipeline Execution

To run the entire pipeline from scratch:

```bash
python code/main.py --action all --seed 42
```

This command executes:
1. Download
2. Generate
3. Analyze
4. Statistics
5. Report

**Estimated Runtime**: ~2-4 hours (depending on hardware and network speed)
**Estimated Disk Usage**: ~15GB after completion

## Support

For issues or questions, please refer to the project documentation in `docs/` or check the `README.md` for additional context.