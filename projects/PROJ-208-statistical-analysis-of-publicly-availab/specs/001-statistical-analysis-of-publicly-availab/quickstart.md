# Quickstart: Statistical Analysis of GitHub Issue Resolution Times

## Prerequisites

- Python 3.11+
- GitHub Personal Access Token (PAT) with `public_repo` scope
- 14 GB available disk space (for GitHub Actions runner)
- 7 GB available RAM (for GitHub Actions runner)

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-208-statistical-analysis-of-publicly-availab

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Set environment variables:

```bash
export GITHUB_TOKEN="your-pat-token-here"
export GITHUB_REPOS="owner/repo1,owner/repo2,..."  # Comma‑separated list of ≥100 repos
```

## Running the Pipeline

### Step 1: Data Collection

```bash
python -m code.collect.github_collector
```

This collects closed issues from the specified repositories and writes to `data/raw/issues.json`.

### Step 2: Preprocessing

```bash
python -m code.collect.preprocess
```

This computes resolution times, filters invalid issues, and writes to `data/processed/issues_clean.csv`.

### Step 3: Distribution Analysis

```bash
python -m code.analysis.distribution_fitting
```

This generates ECDF plots and fits log‑normal/Weibull distributions.

### Step 4: Hypothesis Testing

```bash
python -m code.analysis.hypothesis_testing
```

This runs Kruskal‑Wallis tests with Holm‑Bonferroni correction.

### Step 5: Mixed‑Effects Modeling

```bash
python -m code.analysis.mixed_effects_model
```

This fits the mixed‑effects model with leave‑one‑repository‑out cross‑validation.

### Step 6: Diagnostics

```bash
python -m code.diagnostics.collinearity
python -m code.diagnostics.sensitivity_analysis
```

These generate collinearity and sensitivity reports.

## Running Tests

```bash
# Contract tests
pytest tests/contract/

# Integration tests
pytest tests/integration/

# Unit tests
pytest tests/unit/
```

## Expected Outputs

| Output | Location | Description |
|--------|----------|-------------|
| Raw issues | `data/raw/issues.json` | Raw GitHub API responses |
| Clean dataset | `data/processed/issues_clean.csv` | Preprocessed analysis‑ready data |
| Distribution metrics | `data/processed/distribution_metrics.json` | KS statistics, AIC values |
| Test results | `data/processed/test_results.json` | Hypothesis test outcomes |
| Model results | `data/processed/model_results.json` | Mixed‑effects model coefficients |
| Collinearity report | `data/processed/collinearity_report.json` | VIF values per predictor |
| Sensitivity report | `data/processed/sensitivity_report.json` | Bootstrap‑based stability metrics for each cutoff |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| API rate limit exceeded | Script automatically waits ≥60 s before retry (FR‑003) |
| Insufficient memory | Reduce repository sample size or increase CI runner resources |
| MixedEffects model fails | Fall back to `statsmodels` MixedLM if `pymer4` unavailable |
| No issues collected | Verify `GITHUB_REPOS` format and token permissions |