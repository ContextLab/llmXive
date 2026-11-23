# Quickstart: llmXive follow-up: extending "SpatialClaw: Rethinking Action Interface for Agentic Spatial Reasoning"

## Prerequisites
- Python 3.11+
- `pip`
- Git

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-941-llmxive-follow-up-extending-spatialclaw
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Dependencies include: `shapely`, `numpy`, `scipy`, `pandas`, `pytest`.*

## Running the Experiment

### 1. Generate/Load Data
If the SpatialClaw dataset is not present, the synthetic proxy will be generated automatically:
```bash
python code/data/loader.py --mode generate --output data/raw/synthetic_spatialclaw.jsonl
```

### 2. Run the Restricted Agent (2D)
Execute the 2D restricted agent on a subset of tasks (e.g., 10 occlusion tasks):
```bash
python code/main.py --agent 2d --tasks occlusion --runs 5 --seed 42
```
*This will enforce the 2D constraint, block 3D libraries, and log results.*

### 3. Re-run the 3D Baseline
Execute the 3D baseline on the *same* task instances for paired comparison:
```bash
python code/main.py --agent 3d --tasks occlusion --runs 5 --seed 42
```

### 4. Run Statistical Analysis
Perform the paired comparison and sensitivity analysis:
```bash
python code/stats/tests.py --input results/logs/combined_metrics.csv
python code/stats/sensitivity.py --input results/logs/combined_metrics.csv
```

### 5. Verify Constraints
Check that no 3D libraries were used in the 2D run:
```bash
grep -r "trimesh" results/logs/2d_run_logs/ && echo "FAIL: 3D library detected" || echo "PASS: No 3D libraries detected"
```

## Expected Outputs
- `results/logs/2d_run_logs/`: Detailed logs of the restricted agent.
- `results/analysis/paired_comparison.csv`: Paired success rates and latencies.
- `results/analysis/sensitivity_report.csv`: Threshold sweep results.
- `results/analysis/statistical_test.csv`: P-values and significance flags.

## Troubleshooting
- **Memory Error**: Reduce the batch size in `loader.py` or increase the chunk size for streaming.
- **Import Error**: Ensure `trimesh` and `pytorch3d` are not installed in the virtual environment if strict blocking is required (though the kernel should block them even if installed).
- **Statistical Failure**: Ensure `n >= 5` runs were completed; the Wilcoxon test requires paired data.
