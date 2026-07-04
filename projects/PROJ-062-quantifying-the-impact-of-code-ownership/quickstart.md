# Quickstart Guide

## Prerequisites
- Python 3.11+
- Git
- GitHub Token (export `GITHUB_TOKEN`)

## Steps
1. **Initialize**:
 ```bash
 python -m venv venv
 source venv/bin/activate
 pip install -r requirements.txt
 ```

2. **Run Pipeline**:
 ```bash
 export CUTOFF_DATE="2023-01-01"
 export REPO_LIST="psf/requests,pydantic/pydantic,psycopg/psycopg"
 python code/main.py
 ```

3. **Verify Outputs**:
 - Check `data/results/final_report.json` for correlation stats.
 - Check `data/results/sensitivity_pvalue.csv` for robustness.
 - Check `figures/` for scatter plots.

## Troubleshooting
- **Rate Limits**: Ensure `GITHUB_TOKEN` is set.
- **Git Errors**: Ensure `git` is in PATH.
- **Memory**: If OOM, reduce `REPO_LIST` size.
