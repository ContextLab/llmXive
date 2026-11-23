# Evaluating the Impact of Code Generation on Code Review Turnaround Time

## Project Overview

This project investigates whether AI-assisted code generation impacts the turnaround time of code reviews in open-source repositories. By analyzing pull request data from top Python and JavaScript repositories, we evaluate the hypothesis that AI-generated code may lead to faster or slower review cycles.

## Research Questions

1. Does AI-assisted code generation significantly affect PR turnaround time?
2. What are the distribution characteristics of turnaround times for AI vs. non-AI PRs?
3. How do repository size and author activity influence these results?

## Project Structure

```
projects/PROJ-312-evaluating-the-impact-of-code-generation/
├── code/ # Python modules for data processing and analysis
│ ├── fetch_data.py # GitHub API data acquisition
│ ├── analyze.py # Statistical analysis and hypothesis testing
│ ├── visualize.py # Data visualization (boxplots)
│ ├── report.py # Final report generation
│ ├── utils.py # Utility functions (validation, backoff, logging)
│ ├── validate_spot_check.py # Spot-check validation logic
│ └──... (other modules)
├── data/
│ ├── raw/ # Raw data from GitHub API
│ │ ├── repos.json # Repository metadata
│ │ └── pr_data.json # Raw PR data with commit messages
│ ├── processed/ # Processed and cleaned data
│ │ ├── pr_turnaround.csv # Main analysis dataset
│ │ ├── pr_turnaround_cleaned.csv # Outlier-excluded dataset
│ │ ├── repo_metadata.json # Repository statistics
│ │ ├── statistical_results.json # Statistical test results
│ │ └── excluded_repos.txt # List of filtered repositories
│ └── spot_check/ # Manual validation data
│ ├── sample_list.csv # PRs selected for manual review
│ ├── annotations.csv # Human annotations (manual upload)
│ └── validation_report.csv # Classification accuracy metrics
├── artifacts/ # Final deliverables
│ ├── boxplot.png # High-resolution visualization
│ └── final_report.md # Comprehensive research report
├── contracts/ # JSON Schema definitions
│ ├── pull_request.schema.yaml
│ ├── repo_metadata.schema.yaml
│ └── statistical_result.schema.yaml
├── tests/ # Test suite
│ ├── unit/ # Unit tests
│ └── contract/ # Schema contract tests
├── state/ # Pipeline state tracking
└── requirements.txt # Python dependencies
```

## Installation

1. **Prerequisites**: Python 3.11+

2. **Install Dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

 Required packages:
 - `requests`: HTTP requests to GitHub API
 - `pandas`: Data manipulation and analysis
 - `scipy`: Statistical tests (Mann-Whitney U)
 - `matplotlib`: Visualization (boxplots)
 - `pyyaml`: YAML parsing
 - `tqdm`: Progress bars
 - `statsmodels`: Advanced statistical analysis

3. **GitHub API Token**: Set the `GITHUB_TOKEN` environment variable with a valid GitHub Personal Access Token (PAT) that has `public_repo` scope.

## Usage

### Quick Start

Run the entire pipeline:
```bash
python code/pipeline.py
```

Or run individual stages:

1. **Data Acquisition**:
 ```bash
 python code/fetch_data.py
 ```
 This fetches top Python/JS repos, their PRs, and commit messages. Outputs:
 - `data/raw/repos.json`
 - `data/raw/pr_data.json`
 - `data/processed/pr_turnaround.csv`

2. **Spot Check Validation** (Manual Step Required):
 ```bash
 python code/validate_spot_check.py --generate-sample
 ```
 - Review `data/spot_check/sample_list.csv`
 - Manually annotate `data/spot_check/annotations.csv` (see template)
 - Resume validation:
 ```bash
 python code/validate_spot_check.py --validate
 ```

3. **Statistical Analysis**:
 ```bash
 python code/analyze.py
 ```
 Outputs:
 - `data/processed/statistical_results.json`
 - `data/processed/distribution_stats.json`

4. **Visualization**:
 ```bash
 python code/visualize.py
 ```
 Outputs:
 - `artifacts/boxplot.png` (300 DPI)

5. **Report Generation**:
 ```bash
 python code/report.py
 ```
 Outputs:
 - `artifacts/final_report.md`

### Configuration

- **API Rate Limits**: The pipeline automatically handles rate limiting with exponential backoff. Logs are written to `logs/pipeline.log`.
- **Data Quality Threshold**: The pipeline halts if data quality < 95% (T018c).
- **Spot Check Threshold**: If false-negative rate > 10%, a limitation statement is added to the report (T035).

## Methodology

### Data Collection
- Top 10 Python and JavaScript repositories by star count (>10k stars)
- Full PR history with complete commit lists (pagination handled)
- Classification based on commit keywords ("copilot", "ai-generated") and labels

### Statistical Analysis
- **Primary Test**: Stratified Mann-Whitney U test (stratified by PR size quartiles and author activity tertiles)
- **Outlier Handling**: IQR method (1.5×IQR) for visualization only; primary test uses full dataset
- **Sensitivity Analysis**: Monte Carlo simulation adjusting for false-negative rates

### Validation
- Stratified random sampling for manual spot-check (5% of non-AI PRs)
- False-negative rate calculation to assess classification accuracy

## Output Files

| File | Description |
|------|-------------|
| `data/processed/pr_turnaround.csv` | Main analysis dataset with turnaround times |
| `data/processed/statistical_results.json` | U-statistic, p-value, effect size |
| `artifacts/boxplot.png` | Visualization of turnaround time distributions |
| `artifacts/final_report.md` | Comprehensive research report |
| `data/spot_check/validation_report.csv` | Classification accuracy metrics |

## Limitations

- Classification relies on commit messages and labels; false negatives may exist
- Sample size constraints may limit statistical power
- GitHub API rate limits may affect data completeness
- Results are specific to Python/JavaScript repositories with >10k stars

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Run tests: `pytest tests/`
4. Submit a pull request

## References

- GitHub API Documentation: https://docs.github.com/en/rest
- Mann-Whitney U Test: https://en.wikipedia.org/wiki/Mann%E2%80%93Whitney_U_test
- Fisher's Method for combining p-values: https://en.wikipedia.org/wiki/Fisher%27s_method