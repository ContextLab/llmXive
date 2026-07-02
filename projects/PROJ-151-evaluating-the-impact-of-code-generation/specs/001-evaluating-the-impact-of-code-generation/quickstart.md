# Quickstart: Evaluating the Impact of Code Generation Models on Code Review Efficiency

## Prerequisites

- Python 3.11+
- `pip`
- Access to HuggingFace (for dataset download)
- GitHub Actions Runner (for CI execution)

## Installation

1. Clone the repository and navigate to the project directory.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `requirements.txt` pins `torch` (CPU), `transformers`, `datasets`, `radon`, `pylint`, `statsmodels`.*

## Running the Pipeline

The pipeline is orchestrated via `code/main.py`.

### Step 1: Ingest Data
```bash
python code/data/ingest.py
```
- Downloads `prs-v2-sample` from HuggingFace.
- Filters for Java/Python, ≤30 LOC.
- Outputs `data/processed/filtered_prs.parquet`.

### Step 2: Generate Code
```bash
python code/generation/generate.py
```
- Loads StarCoder-1B (CPU).
- Generates code for each problem statement.
- Logs provenance to `data/generated_provenance.csv`.
- **Fallback**: If OOM, switches to CodeGen-350M.

### Step 3: Compute Metrics
```bash
python code/metrics/compute.py
```
- Computes complexity, maintainability, etc.
- Outputs `data/processed/metrics.csv`.

### Step 4: Analysis & Reporting
```bash
python code/main.py --analysis
```
- Fits mixed-effects models.
- Performs sensitivity analysis (LOC 15/30/50).
- Applies multiple-comparison correction.
- Generates summary report with p-values, R², and validation results.

## Validation Study (Manual)

For the human survey component (FR-011/FR-012):
1. Select ≥50 generated snippets.
2. Host a simple HTML/JS tool for reviewers to rate difficulty and time.
3. Export results to `data/validation/survey_results.csv`.
4. Run `python code/analysis/validation.py` to compute MAE and Cohen's Kappa.

## Troubleshooting

- **OOM Error**: If StarCoder fails, the script automatically falls back to CodeGen-350M. Reduce sample size if needed.
- **Missing Columns**: Ensure `filtered_prs.parquet` contains `code_snippet` and `comment_count`.
- **CUDA Error**: Ensure `torch` is installed in CPU-only mode (check `requirements.txt`).

## Output Artifacts

- `data/processed/filtered_prs.parquet`
- `data/generated/code_snippets.csv`
- `data/processed/metrics.csv`
- `data/generated_provenance.csv`
- `data/validation/survey_results.csv`
- `reports/summary_report.md`
