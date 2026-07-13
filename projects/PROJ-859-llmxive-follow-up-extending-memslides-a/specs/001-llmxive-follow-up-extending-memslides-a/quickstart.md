# Quickstart: Trace Compressibility Analysis

## Prerequisites
- Python 3.11+
- pip / venv

## Installation

1. **Clone and Setup**:
   ```bash
   cd projects/PROJ-859-llmxive-follow-up-extending-memslides-a
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r code/requirements.txt
   ```

2. **Verify Dependencies**:
   ```bash
   python -c "import sklearn; import pandas; print('Dependencies OK')"
   ```

## Running the Pipeline

### Step 1: Generate Synthetic Data
Generate the synthetic dataset of multi-turn revision sessions.
```bash
python code/main.py --task generate --output data/raw/traces.jsonl --seed 42
```
*Output*: `data/raw/traces.jsonl` containing [deferred] sessions. Includes `exact_tool_sequence` and `raw_arg_variance`.

### Step 2: Extract Structural Metrics
Compute entropy, repetition, and variance for each trace.
```bash
python code/main.py --task extract --input data/raw/traces.jsonl --output data/processed/metrics.csv
```
*Output*: `data/processed/metrics.csv`.

### Step 3: Per-Trace Rule Induction & Compressibility
Induce rules for each trace and calculate compressibility scores.
```bash
python code/main.py --task induce --input data/processed/metrics.csv --output data/processed/compressibility_analysis.jsonl
```
*Output*: `data/processed/compressibility_analysis.jsonl` containing per-trace compressibility scores.

### Step 4: Benchmark Agents (Global)
Run baseline and compressed agents (using global rule set) on held-out test set.
```bash
python code/main.py --task benchmark --model data/processed/global_model.pkl --output data/processed/benchmark_results.json
```
*Output*: `data/processed/benchmark_results.json`.

### Step 5: Statistical Analysis
Correlate metrics with Fidelity Loss and Compressibility Score.
```bash
python code/main.py --task analyze --input data/processed/compressibility_analysis.jsonl --output data/processed/statistical_analysis.json
```
*Output*: `data/processed/statistical_analysis.json`.

## Validation

Run contract tests to ensure data integrity. Contracts are located at `projects/PROJ-859-llmxive-follow-up-extending-memslides-a/contracts/`.
```bash
pytest tests/contract/
```

## Reproducibility
To reproduce the exact results:
1. Ensure `code/config.py` has the same `RANDOM_SEED` (default 42).
2. Run the full pipeline in order.
3. Verify checksums in `state/projects/PROJ-859-llmxive-follow-up-extending-memslides-a.yaml`.