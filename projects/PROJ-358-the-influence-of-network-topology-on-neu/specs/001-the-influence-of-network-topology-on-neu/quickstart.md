# Quickstart: The Influence of Network Topology on Neural Synchrony During Cognitive Tasks

## 1. Prerequisites

- Python 3.11+
- `pip` or `conda`
- Access to a GitHub Actions runner (free-tier) or local machine with 7GB+ RAM.

## 2. Installation

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-358-the-influence-of-network-topology-on-neu
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r code/requirements.txt
   ```

## 3. Running the Pipeline

### 3.1 Full Pipeline (End-to-End)
Run the main script to download, preprocess, compute metrics, and analyze:
```bash
python code/main.py --subjects 30 --threshold 0.20
```

**Flags**:
- `--subjects`: Number of subjects to process (default: 30 for CI; 100 for local).
- `--threshold`: Proportional threshold for graph construction (default: 0.20).
- `--dataset`: Dataset source ("openneuro" or "hcp" - note HCP requires auth).

### 3.2 Step-by-Step
1. **Download Data**:
   ```bash
   python code/data/download.py --source openneuro --n 30
   ```
2. **Preprocess**:
   ```bash
   python code/data/preprocess.py --input data/raw/ --output data/processed/
   ```
3. **Compute Metrics**:
   ```bash
   python code/analysis/graph_metrics.py --input data/processed/rest.csv
   python code/analysis/synchrony.py --input data/processed/task.csv
   ```
4. **Statistical Analysis**:
   ```bash
   python code/analysis/stats.py --input data/processed/
   ```

## 4. Output

- `data/processed/subjects.csv`: Subject metadata and exclusion flags.
- `data/processed/graph_metrics.csv`: Resting-state topology metrics.
- `data/processed/synchrony_metrics.csv`: Task-based synchrony metrics (including Delta FC).
- `data/processed/correlation_results.csv`: Final statistical results (r, p, q).
- `data/processed/sensitivity_report.csv`: Results across thresholds {0.10, 0.20, 0.30}.

## 5. Verification

Run the test suite to verify the pipeline:
```bash
pytest tests/ -v
```

**Expected Output**:
- All tests pass.
- `data/processed/correlation_results.csv` contains valid `r`, `p`, `q` values.
- No NaN values in metrics.
- If N < 25, the pipeline halts with a "Power Insufficiency" error.

## 6. Troubleshooting

- **Memory Error**: Ensure `streaming=True` is used in data loading. Process subjects one-by-one.
- **HCP Access Error**: Switch to `--dataset openneuro` as HCP is gated.
- **Disconnected Graph**: The script automatically tries higher thresholds (0.30) if 0.20 fails.
- **Power Insufficiency**: If N < 25, the pipeline will stop. Do not force execution.