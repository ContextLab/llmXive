# Quickstart: Evaluating the Effectiveness of LLM-Driven Code Simplification on Performance

## Prerequisites

- Python 3.11+
- 7 GB+ RAM
- Internet access (for dataset download)
- Git

## Installation

1. **Clone the repository** (if applicable) or navigate to the project root.
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` pins `torch` (CPU version), `transformers`, `datasets`, `scikit-learn`.*

## Running the Pipeline

The entire experiment is orchestrated via `code/main.py`.

### Step 1: Download and Validate Data
```bash
python code/data/download.py
python code/data/validate.py
```
*Output*: `data/raw/` and `data/processed/filtered.parquet`.

### Step 2: Simplify Code
```bash
python code/models/simplify.py
```
*Output*: `data/processed/simplified_pairs.parquet`.

### Step 3: Run Benchmarks
```bash
python code/benchmark/runner.py
```
*Output*: `data/results/benchmark_runs.parquet`.

### Step 4: Statistical Analysis
```bash
python code/benchmark/stats.py
```
*Output*: `data/results/statistical_summary.csv`.

## Verification

To verify the setup, run the pilot validation (functions):
```bash
python code/main.py --pilot
```
*Expected*: Logs showing ≥10 valid pairs per stratum.

## Troubleshooting

- **OOM Error**: Reduce `batch_size` in `simplify.py` or switch to `TinyLlama-1.1B`.
- **Timeout**: Increase `TIMEOUT_SECONDS` in `utils/sandbox.py` (not recommended for CI).
- **ImportError**: Ensure all dependencies are installed in the virtual environment.
