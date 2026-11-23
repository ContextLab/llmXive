# Quick Start Guide

Get up and running with the llm-code-review-impact pipeline in 10 minutes.

## Prerequisites

- Python 3.11+
- GitHub Personal Access Token
- 8GB+ RAM
- 20GB+ disk space

## Installation (2 minutes)

### Step 1: Clone and Setup

```bash
git clone <repository-url>
cd llm-code-review-impact
python -m venv venv
source venv/bin/activate # Linux/Mac
# or
venv\Scripts\activate # Windows
pip install -r requirements.txt
```

### Step 2: Configure GitHub Token

```bash
# Create.env file
echo "GITHUB_TOKEN=your_token_here" >.env

# Or export directly
export GITHUB_TOKEN=your_token_here
```

## Quick Run (5 minutes)

Run a minimal pipeline with limited data:

```bash
# Fetch just 10 PRs from one repo
python code/data/fetch_github.py --limit 10 --repo psf/requests

# Classify and analyze
python code/data/classify_prs.py
python code/analysis/save_complexity_scores.py
python code/data/extract_metrics.py
python code/analysis/statistical_tests.py

# Generate basic visualizations
python code/analysis/visualizations.py
```

## Full Pipeline (10+ minutes)

Run the complete analysis:

```bash
bash scripts/run_pipeline.sh
```

Or run each stage manually:

```bash
# 1. Data collection
python code/data/fetch_github.py

# 2. Classification
python code/data/classify_prs.py

# 3. Save labeled data
python code/data/save_labeled_dataset.py

# 4. Complexity analysis
python code/analysis/save_complexity_scores.py

# 5. Metrics extraction
python code/data/extract_metrics.py

# 6. Statistical tests
python code/analysis/statistical_tests.py

# 7. Results report
python code/analysis/generate_results_report.py

# 8. Audit
python code/audit/manual_validation.py

# 9. Visualizations
python code/analysis/visualizations.py

# 10. Final report
python code/analysis/generate_final_report.py
```

## Verify Results

Check that all outputs were created:

```bash
# List data files
ls -lh data/processed/

# Check for expected files
test -f data/processed/prs_labeled.csv && echo "✓ Labeled PRs"
test -f data/processed/complexity_scores.csv && echo "✓ Complexity scores"
test -f data/processed/prs_metrics.csv && echo "✓ Metrics"
test -f data/processed/results.json && echo "✓ Results"
test -f data/audit/error_rate.json && echo "✓ Audit results"
test -f data/processed/gate_status.json && echo "✓ Gate status"

# List reports
ls -lh reports/figures/
```

## Run Tests

Verify everything works:

```bash
pytest tests/ -v
```

## Common Commands

### Check Configuration

```bash
python -c "from utils.config import get_config_summary; print(get_config_summary())"
```

### View Logs

```bash
tail -f logs/*.log
```

### Clean Up

```bash
# Remove processed data (keep raw)
rm -rf data/processed/*
rm -rf reports/figures/*

# Remove all generated data
rm -rf data/raw/*
rm -rf data/processed/*
rm -rf reports/figures/*
```

## Next Steps

1. **Read the full documentation** in `docs/`
2. **Review the architecture** in `docs/ARCHITECTURE.md`
3. **Understand the methodology** in `docs/README.md`
4. **Contribute** - see `docs/CONTRIBUTING.md`

## Troubleshooting

### "Module not found" errors

```bash
# Ensure you're in the project root
pwd
# Should show: /path/to/llm-code-review-impact

# Activate virtual environment
source venv/bin/activate
```

### GitHub API errors

```bash
# Check your token
curl -H "Authorization: token $GITHUB_TOKEN" \
 https://api.github.com/user

# Verify token has public_repo scope
```

### Memory errors

```bash
# Reduce batch size
# Edit code/utils/config.py
MAX_PRS_PER_REPO = 50 # Reduce from 200
```

## Need Help?

- Check `docs/` for detailed documentation
- Review existing issues in the repository
- Contact project maintainers