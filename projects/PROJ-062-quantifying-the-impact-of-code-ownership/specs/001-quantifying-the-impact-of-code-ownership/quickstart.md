# Quickstart: Quantifying the Impact of Code Ownership on Software Quality

## Prerequisites

- **Python**: 3.11+
- **Git**: Installed and in PATH.
- **System**: Linux environment (GitHub Actions runner compatible).
- **Disk**: ≥14 GB free space.
- **RAM**: ≥7 GB available.

## Installation

1. **Clone the Project**
 ```bash
 git clone
 cd PROJ-062-quantifying-the-impact-of-code-ownership
 ```

2. **Create Virtual Environment**
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install Dependencies**
 ```bash
 pip install -r code/requirements.txt
 ```
 *Note: `requirements.txt` pins versions for reproducibility (Constitution Principle I).*

## Execution

Run the full pipeline:

```bash
python code/main.py
```

### Pipeline Steps
1. **Data Collection**: Clones target repositories (shallow depth 1000).
2. **Metric Calculation**: Computes Gini, Bug Density, Churn, Complexity.
3. **Statistical Analysis**: Performs Spearman correlation, VIF, Quadratic regression.
4. **Visualization**: Generates scatter plots.
5. **Output**: Writes results to `data/results/`.

## Verification

1. **Check Output Files**:
 - `data/results/correlation_summary.json`: Contains correlation stats.
 - `data/results/sensitivity_analysis.json`: Contains sweep results.
 - `data/results/plots/*.png`: Visualizations.

2. **Validate Contracts**:
 ```bash
 python -m pytest tests/contract/
 ```
 *Ensures output JSON matches `contracts/output.schema.yaml`.*

3. **Reproducibility Check**:
 - Re-run `python code/main.py`.
 - Verify checksums in `state/projects/PROJ-062-quantifying-the-impact-of-code-ownership.yaml` match.

## Troubleshooting

- **API Rate Limit**: If `403` errors occur, the script implements exponential backoff (FR-006). Wait 60s between retries.
- **Memory Error**: If RAM exceeds 7 GB, ensure no other processes are running. The script processes repositories sequentially.
- **Clone Failure**: Repositories with <1000 commits are skipped. Check `logs/data_collection.log` for skipped repos.
