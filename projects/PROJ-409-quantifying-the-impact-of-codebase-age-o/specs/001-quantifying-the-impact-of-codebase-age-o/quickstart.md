# Quick Start Guide: Quantifying the Impact of Codebase Age on LLM Code Understanding

This guide walks you through the complete execution of the research pipeline, from data extraction to final report generation.

## Prerequisites

Ensure you have the following installed:
- Python 3.11 or higher
- Git command-line tool
- At least 8GB of available RAM
- A Unix-like environment (Linux/macOS) or WSL on Windows

## Step 1: Project Setup

### 1.1 Verify Project Structure

Ensure the following directories exist:
```bash
code/
code/extraction/
code/inference/
code/analysis/
code/utils/
data/raw/
data/extracted/
data/aggregated/
data/results/
data/models/
tests/unit/
tests/integration/
```

If any are missing, run:
```bash
python code/setup_project_structure.py
```

### 1.2 Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages include:
- `huggingface_hub`, `transformers`, `torch`, `bitsandbytes` (for LLM inference)
- `gitpython` (for git history analysis)
- `pandas`, `scipy`, `networkx` (for data analysis)
- `tokenizers` (for token counting)

### 1.3 Configure Linting (Optional)

```bash
python code/setup_linting.py
```

## Step 2: Data Extraction (User Story 1)

Extract function-level Python snippets from target repositories and calculate their median commit age.

### 2.1 Prepare Repository List

Create a comma-separated list of GitHub repository URLs. Example:
```

```

### 2.2 Run Extraction

```bash
python code/extraction/run_extraction.py \
 --repos "" \
 --output data/extracted/snippets.csv
```

**Parameters:**
- `--repos`: Comma-separated list of repository URLs
- `--output`: Path for the output CSV file (default: `data/extracted/snippets.csv`)
- `--min-snippets`: Minimum number of snippets per repo (default: 50)
- `--timeout`: Per-repo timeout in seconds (default: 600)

**Output:**
A CSV file at `data/extracted/snippets.csv` with columns:
- `snippet_id`: Unique identifier
- `repo_url`: Source repository URL
- `file_path`: Path within the repository
- `median_commit_age`: Median age of commits affecting this file (in days)
- `snippet_content`: The extracted function code
- `token_count`: Number of tokens
- `complexity`: Cyclomatic complexity
- `token_length`: Token length of the snippet

### 2.3 Verify Extraction Output

```bash
python code/extraction/verify_extraction.py --input data/extracted/snippets.csv
```

This script checks that:
- All required columns exist
- At least 800 snippets were extracted (per FR-001)
- No null values in `median_commit_age` or `snippet_content`

## Step 3: Inference (User Story 2)

Run a quantized CodeLLM on the extracted snippets to calculate perplexity and functional correctness rates.

### 3.1 Download Model Weights (if not cached)

```bash
python code/inference/model_downloader.py --model "Salesforce/codegen-350M-mono" --output data/models/
```

The model will be cached in `data/models/` for subsequent runs.

### 3.2 Run Inference Pipeline

```bash
python code/inference/run_inference.py \
 --input data/extracted/snippets.csv \
 --output data/aggregated/file_metrics.csv \
 --timeout 300 \
 --global-timeout 3600
```

**Parameters:**
- `--input`: Path to the extracted snippets CSV
- `--output`: Path for the aggregated metrics CSV
- `--timeout`: Per-snippet timeout in seconds (default: 300)
- `--global-timeout`: Total runtime limit in seconds (default: 3600)
- `--model`: Model name to use (default: `Salesforce/codegen-350M-mono`)
- `--quantization`: Quantization level (`8-bit` or `4-bit`, default: `8-bit`)

**Output:**
1. A snippet-level results file (intermediate, not saved by default)
2. An aggregated file-level metrics CSV at `data/aggregated/file_metrics.csv` with columns:
 - `file_path`: Path within the repository
 - `mean_perplexity`: Average perplexity across snippets in the file
 - `mean_correctness`: Average functional correctness rate
 - `mean_complexity`: Average cyclomatic complexity
 - `mean_length`: Average token length
 - `median_age`: Median commit age for the file
 - `snippet_count`: Number of snippets aggregated

### 3.3 Verify Inference Output

```bash
python code/inference/verify_inference_output.py --input data/aggregated/file_metrics.csv
```

This script validates:
- Required columns exist
- `perplexity` values are > 1.0 or NaN
- `functional_correctness_rate` values are in [0.0, 1.0] or NaN
- Data completeness rate is ≥ 95% (per SC-004)

## Step 4: Analysis (User Story 3)

Perform statistical correlation analysis and generate the final report.

### 4.1 Run Correlation Analysis

```bash
python code/analysis/correlation.py \
 --input data/aggregated/file_metrics.csv \
 --output data/results/correlation_results.csv
```

**Parameters:**
- `--input`: Path to the aggregated file metrics CSV
- `--output`: Path for the correlation results CSV
- `--covariates`: Comma-separated list of covariates to control for (default: `complexity,token_length`)

**Output:**
A CSV file at `data/results/correlation_results.csv` containing:
- `spearman_correlation_age_perplexity`: Correlation coefficient
- `p_value_age_perplexity`: P-value for the correlation
- `spearman_correlation_age_correctness`: Correlation coefficient
- `p_value_age_correctness`: P-value for the correlation
- `significance_age_perplexity`: Boolean (True if p < 0.05)
- `significance_age_correctness`: Boolean (True if p < 0.05)

### 4.2 Generate Final Report

```bash
python code/analysis/report_generator.py \
 --input data/results/correlation_results.csv \
 --output data/results/final_report.md
```

**Output:**
A Markdown report at `data/results/final_report.md` containing:
- Summary of the research question
- Methodology overview
- Correlation coefficients and p-values
- Statistical significance interpretation
- "No significant correlation" statement if p > 0.05
- Hash of the results file (for integrity verification)

### 4.3 Verify Final Report

```bash
python code/analysis/verify_report.py --input data/results/final_report.md
```

This script validates:
- All required JSON keys exist in the report metadata
- Numeric values are properly formatted
- Significance logic is correctly applied
- Interpretation matches the p-value threshold

## Step 5: Reproducibility and Integrity

### 5.1 Hash Verification

The final results CSV is hashed using SHA-256. Verify integrity:

```bash
python code/utils/hasher.py \
 --file data/results/correlation_results.csv \
 --verify
```

### 5.2 Reference Validation

Ensure all citations in the report point to valid files:

```bash
python code/utils/reference_validator.py \
 --dir specs/001-quantify-age-impact/
```

## Troubleshooting

### Common Issues

**Issue:** "Repository not found" or "Git history inaccessible"
- **Solution:** Ensure the repository URL is public and the Git server is reachable.

**Issue:** "Out of memory" during inference
- **Solution:** Reduce the `--timeout` per snippet or use a smaller model. Ensure you have sufficient RAM.

**Issue:** "NaN values in metrics"
- **Solution:** This is expected for snippets that timeout or fail syntax validation. The pipeline handles these gracefully by recording NaN.

**Issue:** "Incomplete dataset (less than 800 snippets)"
- **Solution:** Increase the number of repositories or adjust `--min-snippets` per repo.

### Logging

Set the `LOG_LEVEL` environment variable to adjust verbosity:
```bash
export LOG_LEVEL=DEBUG
python code/extraction/run_extraction.py...
```

Logs are written to `data/logs/` and the console.

## Next Steps

- Review the final report in `data/results/final_report.md`
- Compare results across different repositories
- Extend the analysis with additional covariates
- Submit findings to the research team

## Support

For issues or questions, refer to the project's `specs/001-quantify-age-impact/` design documents or open an issue in the repository.