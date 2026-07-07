# Usage Instructions for the LLM Cognitive Load Study

This guide provides detailed steps for running the pipeline, troubleshooting common issues, and understanding the data flow.

## Quick Start

1. **Ensure Dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

2. **Set Environment Variables**:
 The pipeline requires a GitHub token to fetch repository data.
 ```bash
 export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxx"
 ```

3. **Run the Full Pipeline**:
 Execute the scripts in order:
 ```bash
 # Step 1: Ingest Data
 python code/generate_master_dataset.py

 # Step 2: Run Analysis
 python code/analyze.py

 # Step 3: Generate Report
 python code/report.py
 ```

## Detailed Step-by-Step

### Step 1: Data Ingestion (`code/generate_master_dataset.py`)

This script:
- Loads a list of repositories from `data/raw/repo_list.json` (or generates a default list if missing).
- Fetches PRs, commits, and config files via the GitHub API.
- Calculates LLM adoption flags and cognitive load proxies.
- Outputs `data/derived/master_dataset.csv`.

**Configuration**:
- To limit the number of repositories processed, edit `code/generate_master_dataset.py` and modify the `LIMIT_REPOS` variable.
- To skip specific repositories, add them to the `SKIP_REPOS` list in the script.

**Output Verification**:
Check that `data/derived/master_dataset.csv` contains:
- `repo_name`: Name of the repository.
- `llm_adoption_flag`: 1 or 0.
- `iteration_count`: Integer > 0.
- `diff_complexity_score`: Float between 0 and 1.

### Step 2: Statistical Analysis (`code/analyze.py`)

This script:
- Loads `data/derived/master_dataset.csv`.
- Performs cleaning and VIF checks.
- Runs GLMM (Mixed-Effects Models) and ZINB (Zero-Inflated Negative Binomial) models.
- Applies Bonferroni correction for multiple comparisons.
- Runs sensitivity analysis (sweeping iteration thresholds).
- Runs stratified analysis (splitting by AI Noise).
- Outputs JSON results.

**Configuration**:
- Model parameters (e.g., random effects structure) can be adjusted in the `run_glmm` and `run_zinb_model` functions within `code/analyze.py`.
- The `diff_complexity_score` threshold for "High AI Noise" is set to `0.3` by default (configurable in `code/utils/metrics.py`).

**Output Verification**:
Check `data/derived/analysis_results.json` for:
- `coefficients`: Model coefficients.
- `p_values`: Raw and adjusted p-values.
- `vif_flags`: List of variables with VIF > 5.0.

### Step 3: Report Generation (`code/report.py`)

This script:
- Loads analysis results.
- Generates Forest Plots, Sensitivity Plots, and Stratified Plots.
- Writes the text report with sections on Theoretical Grounding and Data Gaps.
- Outputs `docs/output/final_report.pdf`.

**Configuration**:
- Plot styles can be modified in `code/report.py` (e.g., `sns.set_style("whitegrid")`).
- The report text template is in the `generate_report_text` function.

**Output Verification**:
Open `docs/output/final_report.pdf` and verify:
- Presence of the Forest Plot.
- "Signal Separation" subsection discussing AI Noise.
- "Data Gap" section mentioning NASA-TLX unavailability.

## Troubleshooting

### GitHub API Rate Limiting

If you encounter `403 Forbidden` or rate limit errors:
- Ensure your `GITHUB_TOKEN` is valid and has `public_repo` scope.
- Increase the `RETRY_DELAY` in `code/utils/github_client.py`.
- The client implements exponential backoff; wait for the retry logic to complete.

### Missing Dependencies

If `statsmodels` or `scipy` fails to import:
```bash
pip install --upgrade statsmodels scipy
```

### Data Validation Errors

If `data/derived/master_dataset.csv` is empty or missing columns:
- Check the logs from `generate_master_dataset.py` for API errors.
- Ensure the input repository list contains valid `owner/repo` strings.

## Running Tests

Run the test suite to verify functionality:
```bash
pytest tests/ -v
```

## Customization

To add new metrics or modify existing ones:
1. Edit `code/utils/metrics.py` to add calculation functions.
2. Update `code/ingest.py` to call the new functions.
3. Update `code/analyze.py` to include new variables in the models.
4. Update `code/report.py` to visualize new results.

## Support

For issues or questions, refer to the project's `research.md` or open an issue in the repository.
