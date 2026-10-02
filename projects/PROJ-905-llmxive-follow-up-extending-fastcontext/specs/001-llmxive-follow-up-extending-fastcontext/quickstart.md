# Quickstart: FastContext-Lite

## Prerequisites
- Python 3.11+
- Git
- Access to a machine with 7GB+ RAM (GitHub Actions or local).

## Installation

1. **Clone and Setup**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-905-llmxive-follow-up-extending-fastcontext
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: This installs `torch==2.2.0+cpu` explicitly to ensure reproducibility on CPU-only runners. `ruff` is installed as a dev dependency only.*

## Running the Pipeline

### Step 1: Data Preparation (Ground Truth & Scoring)
Run the static analysis and ground truth extraction.
```bash
python code/static_analysis.py --input-swe-bench --output-processed
```
*This generates `data/processed/regularity_scores.csv` and `data/processed/ground_truth_annotations.csv`.*

### Step 2: Stratification
The script automatically splits the data into "Regular" and "Irregular" sets based on the median score (using stable sort).

### Step 3: Execution (FastContext-Lite)
Run the deterministic engine on the "Regular" set.
```bash
python code/fastcontext_lite.py --split Regular --output results
```

### Step 4: Baseline Execution (FastContext-Original)
Run the original baseline (CPU or quantized GPU if enabled).
```bash
python code/baseline_runner.py --split Regular --mode cpu --output results
```

### Step 5: Analysis
Generate statistical reports.
```bash
python code/analysis.py --input results/metrics.csv --output results/statistical_analysis.json
```

## Verification
To verify the installation:
```bash
pytest tests/unit/test_scoring.py -v
```
This should pass without errors, confirming the scoring logic and dependencies are correctly installed.

## Troubleshooting
- **CUDA Error**: If you see CUDA errors, ensure `torch==2.2.0+cpu` is installed. The `requirements.txt` should explicitly pin this.
- **Memory Error**: If processing large repos, ensure `streaming=True` is used in the dataset loader.
- **Missing Ground Truth**: Verify that the SWE-bench dataset version matches the one used for annotation extraction.