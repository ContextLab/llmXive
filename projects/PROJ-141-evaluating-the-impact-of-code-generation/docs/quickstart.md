# Quick Start Guide

This guide walks you through setting up and running a single experiment session.

## Step 1: Environment Setup

```bash
# Clone and navigate to project
git clone <repository-url>
cd PROJ-141-evaluating-the-impact-of-code-generation

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configure Environment

Set required environment variables:

```bash
# Required for data protection (Constitution VII)
export CODEX_ENCRYPTION_KEY=$(openssl rand -hex 32)

# Dataset paths (download datasets first if needed)
export HUMAN_EVAL_PATH="./data/humaneval"
export CODEFORCES_PATH="./data/codeforces"
```

## Step 3: Download Datasets

```bash
# Download HumanEval dataset
python code/data/download_humaneval.py

# Download Codeforces dataset
python code/data/download_codeforces.py
```

## Step 4: Verify Problem Loading

Ensure ≥95% load rate as per FR-001:

```bash
python code/experiment/problem_loader.py --verify
```

## Step 5: Start Experiment Server

```bash
python code/experiment/app.py
```

The server will start on `.

## Step 6: Run Experiment Session

1. Open browser and navigate to `
2. Complete the informed consent form (T005)
3. Complete problems under LLM-assisted condition
4. Switch to baseline condition (T020)
5. Complete problems under baseline condition
6. Submit experiment log

## Step 7: Run Quality Assessment

```bash
# Compute all quality metrics
python code/quality/metric_aggregator.py

# Individual metrics (optional)
python code/quality/pass_rate.py
python code/quality/complexity.py
python code/quality/coverage.py
python code/quality/static_analysis.py
```

## Step 8: Run Statistical Analysis

```bash
# Load paired participant data
python code/analysis/data_loader.py

# Run statistical tests
python code/analysis/statistical_tests.py

# Apply multiple-comparison correction
python code/analysis/correction.py

# Export results with trace IDs
python code/analysis/export.py
```

## Step 9: Verify Outputs

Check that outputs were created:

```bash
# Verify data files
ls -la data/

# Verify checksums (Constitution Principle III)
python data/checksums.py

# View analysis results
cat data/analysis_results.csv
```

## Troubleshooting

### Problem Loading Failed

If problem load rate <95%:
```bash
python code/experiment/problem_loader.py --debug
```

### Model Inference Errors

If LLM model fails to load:
```bash
# Check model size (must be ≤1GB for CPU)
python code/models/model_selector.py --verify

# Enable fallback mode
export MODEL_FALLBACK_ENABLED=true
```

### Database Errors

```bash
# Recreate database schema
python code/data/db_schema.py --init
```

## Next Steps

- Read [docs/api.md](api.md) for detailed API documentation
- Run tests: `pytest tests/`
- Check [tasks.md](../tasks.md) for remaining tasks

## Compliance Checklist

Before data collection:
- [ ] T053a: Anonymization implemented
- [ ] T053b: Secure deletion workflow ready
- [ ] T004: Environment configuration complete
- [ ] T005: Consent flow verified
- [ ] T006: Logging infrastructure tested
