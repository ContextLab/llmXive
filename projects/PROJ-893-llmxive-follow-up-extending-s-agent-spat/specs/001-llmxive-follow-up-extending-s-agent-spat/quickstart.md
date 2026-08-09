# Quickstart: llmXive follow-up: extending "S-Agent: Spatial Tool-Use Elicits Reasoning for Spatial Intelligence"

## Prerequisites

- Python 3.11+
- `git`
- Hugging Face CLI (optional, for dataset download)

## Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repo-url>
   cd projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

### Step 1: Download and Preprocess Data
This step downloads the verified datasets and extracts geometric constraints.
```bash
python code/data/download.py --sample-size 1000
python code/data/extract_geometry.py --input data/raw --output data/derived/constraints.jsonl
```
*Note: This will skip scenes with missing geometry and log them.*

### Step 2: Run the Symbolic Solver
Execute the CSP solver on the extracted constraints.
```bash
python code/solver/run_solver.py --input data/derived/constraints.jsonl --output data/derived/predictions.jsonl
```
*This runs on CPU. It will respect the 60s timeout per scene.*

### Step 3: Benchmark and Analyze
Compare results and generate the failure analysis report.
```bash
python code/benchmark/metrics.py --predictions data/derived/predictions.jsonl --baseline data/raw/merged.csv --output data/derived/benchmark_results.csv
python code/benchmark/analyze_failures.py --results data/derived/benchmark_results.csv --output data/derived/failure_report.json
```

### Step 4: View Results
- **Metrics**: `data/derived/benchmark_results.csv` (contains Exact Match, F1, Latency).
- **Failure Analysis**: `data/derived/failure_report.json` (categorizes "Geometric Ambiguity" vs "Semantic Gap").
- **Summary**: Check the console output of `analyze_failures.py` for the summary counts.

## Testing

Run the unit tests to verify the CSP logic and metrics calculation:
```bash
pytest tests/unit/
```

Run the integration test to verify the full pipeline (may take a few minutes):
```bash
pytest tests/integration/test_pipeline.py
```
