# Quickstart: Assessing the Impact of Network Centrality on Age‑Related Cognitive Decline

## Prerequisites

- Python 3.10+
- Git
- (Optional) ADNI Account credentials for real data.

## 1. Setup Environment

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-299-assessing-the-impact-of-network-centrali

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Configuration

### Option A: Real Data (ADNI)
Set environment variables for ADNI authentication:
```bash
export ADNI_USER="your_username"
export ADNI_PASS="your_password"
export ADNI_PARTICIPANT_LIST="list_of_ids.txt" # One ID per line
```

### Option B: Synthetic Data (CI/Testing)
No credentials needed. The pipeline will auto-generate a mock dataset.
```bash
export USE_SYNTHETIC_DATA=true
```

## 3. Run the Pipeline

Execute the main script:
```bash
python code/main.py
```

**Output**:
- `data/processed/`: Preprocessed images (deleted after analysis in CI).
- `data/analysis/centrality_metrics.csv`: Centrality values.
- `data/analysis/regression_results.json`: Statistical outputs.
- `outputs/report.pdf`: Final PDF report.
- `logs/pipeline.log`: Execution logs.

## 4. Verify Results

Check the generated report:
```bash
ls -lh outputs/report.pdf
# Should be < 5MB and contain figures/tables.
```

Inspect regression results:
```bash
cat data/analysis/regression_results.json | jq '.[] | select(.q_value <= 0.05)'
```

## 5. Troubleshooting

- **Memory Error**: Ensure you are not running with `USE_SYNTHETIC_DATA=false` on a small runner. The synthetic data is optimized for low RAM.
- **Missing ADNI Credentials**: If `USE_SYNTHETIC_DATA` is not set and credentials are missing, the script will abort. Set `USE_SYNTHETIC_DATA=true` for testing.
- **Motion Exclusion**: Check `logs/pipeline.log` for "Excluded due to motion" messages.
