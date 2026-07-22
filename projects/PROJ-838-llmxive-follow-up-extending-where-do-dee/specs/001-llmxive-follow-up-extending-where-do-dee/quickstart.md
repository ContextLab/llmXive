# Quickstart: 001-gene-regulation

## Prerequisites

- Python 3.11+
- Git
- Hugging Face account (if dataset requires authentication)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd specs/001-llmxive-follow-up-extending-where-do-dee
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify environment**:
   ```bash
   python -c "import pandas, networkx, datasets; print('All imports successful')"
   ```

## Running the Pipeline

The pipeline is orchestrated via `code/pipeline.py`.

### 1. Download Data
```bash
python code/downloader.py --dataset NJU-LINK/TELBench --output data/raw/tebench_raw.json
```
*Note: This step may require setting `HF_TOKEN` if the dataset is gated.*

### 2. Run Full Analysis
```bash
python code/pipeline.py --config code/config.py
```
This executes:
- Parsing and graph construction.
- Metric calculation.
- Train/Test split.
- Threshold optimization and prediction.
- Evaluation report generation.

### 3. Inspect Results
- **Metrics**: `data/processed/metrics.csv`
- **Evaluation Report**: `data/processed/evaluation_results.json`
- **Graphs**: `data/processed/graphs/`

## Testing

Run the unit tests to verify correctness:
```bash
pytest tests/unit/ -v
```

Run integration tests:
```bash
pytest tests/integration/ -v
```

## Configuration

Edit `code/config.py` to adjust:
- `cutoff_depth`: Fraction of spans to use (default 0.30).
- `seed`: Random seed for reproducibility.
- `paths`: Input/output directories.

## Troubleshooting

- **Dataset Access Error**: Ensure `HF_TOKEN` is set if the dataset is gated. Check the `Verified datasets` block for the correct source.
- **Memory Error**: The pipeline uses streaming. If issues persist, reduce the dataset size or increase RAM.
- **Zero-Edge Graphs**: The system handles these by returning 0.0 for metrics. No action needed.
- **Performance**: If the pipeline exceeds 30 minutes for 100 trajectories, check the `data/processed/metrics.csv` for unstable graphs and ensure streaming is enabled.