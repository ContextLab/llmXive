# Quickstart: llmXive follow-up: extending "Where Do Deep-Research Agents Go Wrong? Span-Level Error Localization"

## Prerequisites
- Python 3.11+
- pip
- Access to HuggingFace (for dataset download)

## Installation

1.  **Clone and Setup**:
    ```bash
    cd projects/PROJ-838-llmxive-follow-up-extending-where-do-dee
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    python -m spacy download en_core_web_sm
    ```

3.  **Verify Environment**:
    Ensure you have access to the TELBench dataset URL. No GPU drivers are required.

## Running the Pipeline

### 1. Download Data
Fetch the raw TELBench dataset and verify checksums.
```bash
python code/downloader.py --fetch
```
*Output*: `data/raw/telbench_trajectories.json`

### 2. Build Graphs & Calculate Metrics
Process trajectories, construct DAGs, and compute topological features.
```bash
python code/main.py --mode process --cutoff-depth 0.30
```
*Output*: `data/processed/metrics/trajectory_metrics.csv`

### 3. Evaluate & Generate Report
Apply the optimal F1-based threshold and generate the confusion matrix.
```bash
python code/main.py --mode evaluate --strategy f1-max
```
*Output*: `data/results/evaluation_report.json`

### 4. Sensitivity Analysis (Optional)
Run the threshold sweep to check robustness.
```bash
python code/main.py --mode sensitivity --thresholds 0.01 0.05 0.1 --percentiles 10 20 30
```

### 5. Versioning & Hashing
Manually trigger hashing of all artifacts (or run after each phase).
```bash
python code/hasher.py
```
*Output*: Updates `state/projects/PROJ-838-llmxive-follow-up-extending-where-do-dee.yaml` with SHA-256 hashes.

## Testing

Run the unit and integration test suite:
```bash
pytest tests/
```

## Troubleshooting
- **Memory Error**: If processing the full dataset fails, add `--sample-size 100` to the `process` command to test on a subset first.
- **Missing Fields**: If `graph_builder.py` logs a warning about missing fields, check `data/raw/telbench_trajectories.json` for schema drift against the expected TELBench format.
- **No Edges**: If a trajectory has zero edges, the connectivity metric is set to `0.0` by default. This is expected behavior for sparse reasoning paths.
- **spaCy Model Missing**: Ensure `en_core_web_sm` is installed via `python -m spacy download en_core_web_sm`.