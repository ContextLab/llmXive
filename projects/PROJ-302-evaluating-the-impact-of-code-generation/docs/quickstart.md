# Quickstart Guide: Evaluating the Impact of Code Generation on Code Review Time

This guide provides step-by-step instructions to set up, run, and validate the `llmXive` research pipeline for evaluating how LLM-generated code affects code review times.

## Prerequisites

- Python 3.9+
- Git
- A GitHub Personal Access Token (with `public_repo` scope)
- Sufficient disk space (~15GB for intermediate data)
- (Optional) GPU for faster code generation (self-hosted runner required)

## 1. Clone and Setup

```bash
git clone <repository-url>
cd llmXive-evaluating-llm-code-generation-impact
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

> **Note**: If you plan to use the GPU escape hatch for code generation, ensure you have access to a self-hosted GitHub Actions runner with GPU capabilities.

### Configure Environment

Create a `.env` file in the project root with your GitHub token:

```bash
GITHUB_TOKEN=your_github_personal_access_token
```

## 2. Project Structure

```
.
├── code/ # Source code modules
│ ├── data_acquisition/ # GitHub scraping, code generation
│ ├── feature_extraction/# Complexity, timestamps, style metrics
│ ├── analysis/ # Matching, statistical tests, sensitivity
│ ├── utils/ # Config, models, validators
│ └── main.py # Pipeline orchestrator
├── data/ # Generated datasets and reports
│ ├── raw/ # Raw GitHub API responses
│ └── processed/ # Cleaned and enriched data
├── reports/ # Final PDF and HTML reports
├── docs/ # Documentation (this file)
└── tests/ # Unit, integration, and contract tests
```

## 3. Running the Pipeline

The pipeline is orchestrated via `code/main.py`. It executes the following stages:

1. **Data Acquisition**: Fetches PR metadata and code from GitHub.
2. **Feature Extraction**: Computes complexity, style, and timestamp metrics.
3. **Code Generation**: Generates synthetic LLM code (context-based and prompt-based).
4. **Matching & Analysis**: Performs propensity score matching and statistical testing.
5. **Sensitivity Analysis**: Validates results across complexity/size strata.
6. **Report Generation**: Produces a PDF report with visualizations.

### Execute Full Pipeline

```bash
python code/main.py
```

The script will:
- Create necessary directories (`data/`, `reports/`, `logs/`).
- Fetch data from GitHub (respects rate limits).
- Generate synthetic code (CPU first; triggers GPU workflow if timeout > 60s).
- Run matching and statistical tests.
- Enforce gates (matching balance, sensitivity consistency, PII).
- Generate `reports/analysis_report.pdf`.

### Expected Outputs

After successful completion, you will find:

- `data/processed/merged_features.parquet`
- `data/processed/matching_results.parquet`
- `data/processed/sensitivity_summary.json`
- `data/processed/runtime_report.json`
- `reports/analysis_report.pdf`
- `reports/visualizations/` (box plots, CDF curves)

## 4. Validation

Run the quickstart validator to ensure all components are functioning:

```bash
python code/quickstart_validator.py
```

This script checks:
- Directory structure integrity.
- Existence of required output files.
- Validity of JSON reports (SMD < 0.1, sensitivity consistency >= 80%).
- PII scan results (should be clean).

Exit code `0` indicates success.

## 5. Troubleshooting

### Rate Limiting
If you encounter GitHub API rate limits, ensure your `GITHUB_TOKEN` is valid and has the correct scopes. The pipeline includes exponential backoff (T013).

### Code Generation Timeout
If CPU generation exceeds 60s, the pipeline will dispatch a GitHub Actions workflow to a GPU runner (T014b-GEN). Ensure your repository has the `.github/workflows/gpu-generation.yml` file and a self-hosted GPU runner is available.

### Matching Failure
If covariate balance (SMD) > 0.1 after retries, the pipeline halts and generates `data/processed/matching_failure_report.json`. Review the report and consider adjusting covariates.

### Sensitivity Inconsistency
If p < 0.05 in < 80% of subsets, the pipeline exits with code 1. Check `data/processed/sensitivity_summary.json` for details.

## 6. Extending the Pipeline

- **Add New Repos**: Modify `code/data_acquisition/github_scraper.py` to include additional repositories.
- **Custom Covariates**: Edit `data/processed/covariate_config.json` to change matching variables.
- **New Visualizations**: Extend `code/analysis/visualization.py` to add custom plots.

## 7. Citation

If you use this pipeline in your research, please cite the project repository.

---
*Last updated: 2023-10-27*
