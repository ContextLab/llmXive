# Evaluating the Impact of Code Generation on Code Review Quality Using LLMs

## Project Overview

This research project investigates the impact of AI-generated code (specifically from GitHub Copilot) on code review quality metrics. We analyze pull requests from major open-source repositories to determine whether LLM-assisted code receives different review treatment compared to human-written code.

## Research Questions

1. Do LLM-generated pull requests receive different comment densities than human-written PRs?
2. Is there a difference in time-to-merge between LLM and human code?
3. How does code complexity affect review metrics across both groups?
4. Can we detect LLM-generated code with high confidence using secondary detectors?

## Methodology

### Data Collection
- Fetches PRs from prioritized repositories: `psf/requests`, `microsoft/vscode`, `numpy/numpy`
- Classifies PRs as `llm` or `human` based on commit signatures and secondary detectors
- Extracts review metrics: comment count, time-to-merge, review cycles
- Computes cyclomatic complexity scores for all PRs

### Statistical Analysis
- **Primary**: Independent two-sample t-tests comparing LLM vs human groups
- **Sensitivity**: Mann-Whitney U tests for robustness verification
- **Controls**: Complexity scores used to control for confounding variables
- **Validation**: Manual audit with error rate threshold of 5%

### Key Assumptions
- T-tests are primary analysis method (FR-004)
- No multiple-comparison correction applied
- Human expert judgment is ground truth for audit (SC-004)
- Memory usage fallback if >6GB during complexity calculation

## Project Structure

```
.
├── code/
│ ├── analysis/ # Statistical tests, visualizations, reports
│ ├── audit/ # Manual validation logic
│ ├── data/ # Data fetching, classification, metrics extraction
│ └── utils/ # Configuration, logging, seeds, checksums
├── data/
│ ├── raw/ # Raw GitHub API responses
│ ├── processed/ # Cleaned datasets and analysis results
│ └── audit/ # Manual validation results
├── tests/
│ ├── unit/ # Unit tests for individual functions
│ └── integration/ # End-to-end pipeline tests
├── reports/
│ └── figures/ # Generated visualizations and final report PDF
├── docs/ # Documentation
└── requirements.txt # Python dependencies
```

## Installation

1. Clone the repository
2. Create a virtual environment (Python 3.11 recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Configuration

Edit `code/utils/config.py` to modify:
- Repository list for data collection
- API rate limiting settings
- Statistical thresholds (alpha level)
- Audit sample size parameters

## Execution Pipeline

Run the complete pipeline in order:

```bash
# 1. Fetch raw PR data from GitHub
python code/data/fetch_github.py

# 2. Classify PRs as LLM or human
python code/data/classify_prs.py

# 3. Save labeled dataset
python code/data/save_labeled_dataset.py

# 4. Compute complexity scores
python code/analysis/save_complexity_scores.py

# 5. Extract review metrics
python code/data/extract_metrics.py

# 6. Run statistical tests
python code/analysis/statistical_tests.py

# 7. Generate results report
python code/analysis/generate_results_report.py

# 8. Run manual validation audit
python code/audit/manual_validation.py

# 9. Generate visualizations
python code/analysis/visualizations.py

# 10. Generate final report
python code/analysis/generate_final_report.py
```

Or run the complete pipeline:
```bash
bash scripts/run_pipeline.sh # if available
```

## Output Artifacts

### Data Files
- `data/raw/prs_<repo>_<batch>.json` - Raw GitHub API responses
- `data/processed/prs_labeled.csv` - Classified PRs with confidence scores
- `data/processed/complexity_scores.csv` - Cyclomatic complexity per PR
- `data/processed/prs_metrics.csv` - Review metrics for all PRs
- `data/processed/results.json` - Statistical test results
- `data/audit/error_rate.json` - Manual validation error rate
- `data/processed/gate_status.json` - Audit gate status (pass/block)

### Reports
- `reports/figures/boxplots.pdf` - Side-by-side boxplots of review metrics
- `reports/figures/histograms.pdf` - Distribution histograms
- `reports/figures/correlations.pdf` - Complexity vs metrics correlations
- `reports/final_report.pdf` - Complete research summary

## Testing

Run all tests:
```bash
pytest tests/ -v
```

Run specific test suites:
```bash
pytest tests/unit/ -v # Unit tests
pytest tests/integration/ -v # Integration tests
```

## Key Results

The pipeline produces:
- T-statistics and p-values for comment density and time-to-merge comparisons
- Effect sizes (Cohen's d) for practical significance
- Correlation coefficients between complexity and review metrics
- Manual audit error rate (must be < 5% to pass gate)

## Limitations

- API rate limits may restrict data volume
- Classification confidence thresholds may miss edge cases
- Complexity metrics are approximations
- Manual audit sample size is statistically derived but limited

## Contributing

1. Create a feature branch
2. Make changes following the existing code style (black, ruff)
3. Add tests for new functionality
4. Submit a pull request

## License

This research project is open source. See LICENSE file for details.

## Contact

For questions about this research, please refer to the project maintainers.