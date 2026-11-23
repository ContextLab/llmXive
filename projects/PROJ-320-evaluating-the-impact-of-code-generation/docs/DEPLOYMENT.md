# Deployment Guide

## Prerequisites

- Python 3.11 or higher
- GitHub Personal Access Token with `public_repo` scope
- Minimum 8GB RAM for full dataset processing [UNRESOLVED-CLAIM: c_57380dce — status=not_enough_info]
- Approximately 20GB disk space for raw and processed data [UNRESOLVED-CLAIM: c_f0807c39 — status=not_enough_info]

## Environment Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd llm-code-review-impact
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate # Linux/Mac
# or
venv\Scripts\activate # Windows
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create `.env` file in project root:

```bash
GITHUB_TOKEN=your_personal_access_token
PYTHONHASHSEED=42
```

## Configuration

Edit `code/utils/config.py` to customize:

```python
REPOSITORY_LIST = [
 "psf/requests",
 "microsoft/vscode",
 "numpy/numpy",
 # Add more repositories as needed
]

API_RATE_LIMIT = 5000 # GitHub API limit
MAX_RETRIES = 5
BACKOFF_FACTOR = 2

ALPHA_LEVEL = 0.05
MIN_AUDIT_SAMPLE = 30
AUDIT_PROPORTION = 0.10

CONFIDENCE_THRESHOLD = 0.6
ERROR_RATE_THRESHOLD = 0.05
```

## Running the Pipeline

### Option 1: Individual Scripts

Run each stage sequentially:

```bash
# Stage 1: Fetch data
python code/data/fetch_github.py

# Stage 2: Classify PRs
python code/data/classify_prs.py

# Stage 3: Save labeled dataset
python code/data/save_labeled_dataset.py

# Stage 4: Compute complexity
python code/analysis/save_complexity_scores.py

# Stage 5: Extract metrics
python code/data/extract_metrics.py

# Stage 6: Run statistical tests
python code/analysis/statistical_tests.py

# Stage 7: Generate results report
python code/analysis/generate_results_report.py

# Stage 8: Run audit
python code/audit/manual_validation.py

# Stage 9: Generate visualizations
python code/analysis/visualizations.py

# Stage 10: Generate final report
python code/analysis/generate_final_report.py
```

### Option 2: Full Pipeline Script

If available, run the complete pipeline:

```bash
bash scripts/run_pipeline.sh
```

### Option 3: Docker (Recommended for Production)

```bash
# Build image
docker build -t llm-code-review-impact.

# Run pipeline
docker run -v $(pwd)/data:/app/data \
 -v $(pwd)/reports:/app/reports \
 -e GITHUB_TOKEN=$GITHUB_TOKEN \
 llm-code-review-impact
```

## Output Verification

After pipeline completion, verify these artifacts exist:

```bash
# Data files
ls -lh data/raw/*.json
ls -lh data/processed/prs_labeled.csv
ls -lh data/processed/complexity_scores.csv
ls -lh data/processed/prs_metrics.csv
ls -lh data/processed/results.json
ls -lh data/audit/error_rate.json
ls -lh data/processed/gate_status.json

# Reports
ls -lh reports/figures/boxplots.pdf
ls -lh reports/figures/histograms.pdf
ls -lh reports/figures/correlations.pdf
ls -lh reports/final_report.pdf
```

## Troubleshooting

### GitHub API Rate Limiting

If you encounter rate limit errors:

```bash
# Check your token status
curl -H "Authorization: token $GITHUB_TOKEN" \

```

Solutions:
- Use a token with higher rate limits (authenticated requests: 5000/hour [UNRESOLVED-CLAIM: c_ef96ab0b — status=not_enough_info])
- Wait for rate limit reset
- Reduce the number of repositories or PRs to fetch

### Memory Issues

If processing fails due to memory:

```bash
# Monitor memory usage
htop # or Task Manager on Windows

# Reduce batch size in config
# Edit code/utils/config.py
MAX_PRS_PER_REPO = 100 # Reduce from 200
```

The pipeline has built-in fallback for complexity calculation if memory > 6GB.

### Audit Gate Blocked

If `gate_status.json` shows "blocked":

1. Check `data/audit/error_rate.json` for the actual error rate
2. Review manual validation results in `data/audit/manual_validation_results.json`
3. Adjust classification thresholds in `code/data/classify_prs.py`
4. Re-run classification with adjusted parameters

## CI/CD Integration

### GitHub Actions

Add `.github/workflows/pipeline.yml`:

```yaml
name: Research Pipeline

on:
 push:
 branches: [main]
 schedule:
 - cron: '0 0 * * 1' # Weekly

jobs:
 run-pipeline:
 runs-on: ubuntu-latest
 steps:
 - uses: actions/checkout@v3
 - name: Set up Python
 uses: actions/setup-python@v4
 with:
 python-version: '3.11'
 - name: Install dependencies
 run: |
 pip install -r requirements.txt
 - name: Run pipeline
 env:
 GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
 run: |
 bash scripts/run_pipeline.sh
 - name: Upload artifacts
 uses: actions/upload-artifact@v3
 with:
 name: research-results
 path: |
 data/processed/
 reports/
```

## Monitoring

### Log Files

Check logs for issues:

```bash
# Data fetching logs
tail -f logs/data_fetch.log

# Classification logs
tail -f logs/classification.log

# Analysis logs
tail -f logs/analysis.log
```

### Performance Metrics

Track pipeline execution time:

```bash
time python scripts/run_pipeline.sh
```

## Security Considerations

- Never commit `GITHUB_TOKEN` to version control
- Use `.gitignore` to exclude sensitive files
- Rotate tokens regularly
- Ensure no PII is logged or stored

## Scaling

For larger datasets:

1. Increase `MAX_PRS_PER_REPO` in config
2. Use distributed processing (future enhancement)
3. Consider cloud-based execution with more RAM
4. Implement streaming for complexity calculation

## Support

For issues or questions:
- Check existing issues in the repository
- Review documentation in `docs/`
- Contact project maintainers