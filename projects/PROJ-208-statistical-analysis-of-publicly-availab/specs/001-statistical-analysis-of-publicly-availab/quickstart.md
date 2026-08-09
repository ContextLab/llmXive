# Quickstart: Statistical Analysis of GitHub Issue Resolution Times

## Prerequisites

- Python 3.11+
- Git
- GitHub Actions runner (or local environment for testing)

## Installation

1. **Clone the repository** and navigate to the project directory.
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `requirements.txt` includes `datasets`, `pandas`, `scipy`, `statsmodels`, `scikit-learn`, `matplotlib`, `seaborn`.*

## Data Download & Processing

The pipeline automatically downloads the verified dataset from HuggingFace.

```bash
# Run the full pipeline
python code/main.py
```

This script performs:
1. **Data Ingestion**: Downloads `akhousker/github-issues`.
2. **Cleaning**: Filters invalid timestamps, computes resolution times.
3. **Analysis**: Runs distribution fitting, hypothesis testing, and LME.
4. **Reporting**: Generates `data/processed/analysis_results.json` and plots.

## Manual Steps (Optional)

### Load Data Manually
```python
from datasets import load_dataset
ds = load_dataset("akhousker/github-issues", split="train")
print(f"Loaded {len(ds)} records")
```

### Run Specific Analysis
```python
# Distribution Analysis
from code.analysis.distribution import run_distribution_analysis
run_distribution_analysis("data/processed/cleaned_issues.csv")

# Hypothesis Testing
from code.analysis.hypothesis import run_hypothesis_tests
run_hypothesis_tests("data/processed/cleaned_issues.csv")
```

## Output Artifacts

- `data/raw/github_issues_raw.parquet`: Raw downloaded data.
- `data/processed/cleaned_issues.csv`: Cleaned analysis dataset.
- `data/processed/analysis_results.json`: Statistical test results.
- `data/processed/plots/`: ECDF, distribution fits, and model diagnostics.

## Troubleshooting

- **Rate Limits**: Not applicable (uses static HF dataset).
- **Memory Errors**: Dataset is small. If errors occur, check for memory leaks in other processes.
- **Missing Fields**: If `language` is missing, the script will skip language-based analysis and log a warning.
