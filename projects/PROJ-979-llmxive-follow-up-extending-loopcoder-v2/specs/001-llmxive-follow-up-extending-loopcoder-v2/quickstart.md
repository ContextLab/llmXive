# Quickstart: llmXive follow-up: extending "LoopCoder-v2: Only Loop Once for Efficient Test-Time Computation Scali"

## Prerequisites

- Python 3.10+
- Git
- Substantial RAM (CPU-only validation) or GPU (Full analysis)
- Access to HuggingFace Hub (for datasets)
- Docker (optional, for sandboxed execution)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2
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
   *Note: `requirements.txt` includes `torch` (CPU version) and `transformers`. For GPU, ensure the correct `torch` version is installed.*

## Running the Analysis

### Step 1: Download Datasets
The data loader will automatically fetch datasets from HuggingFace.
```bash
python code/src/data_loader.py --download
```
*Note: Ensure you have sufficient free disk space for the datasets.*

### Step 2: Run Entropy & Convergence Analysis
This step extracts entropy and tracks convergence.
- **Validation Mode (CPU)**: Use `--sample-size 50` to run on CodeLlama-1.3b within 6 hours.
- **Full Mode (GPU)**: Omit `--sample-size` to run on the full dataset.

```bash
# Validation Mode
python code/src/entropy.py --output data/processed/entropy_results.csv --sample-size 50
python code/src/inference.py --output data/processed/convergence_results.csv --sample-size 50

# Full Mode (Requires GPU)
python code/src/entropy.py --output data/processed/entropy_results.csv
python code/src/inference.py --output data/processed/convergence_results.csv
```
*Tip: For development, use a small sample size to process only a subset of problems.*

### Step 3: Run Correlation & Router Simulation
```bash
python code/src/analysis.py --entropy data/processed/entropy_results.csv \
                            --convergence data/processed/convergence_results.csv \
                            --output data/processed/router_simulation.csv
```

### Step 4: Verify Results
Check the generated report:
```bash
cat data/processed/router_simulation.csv
```
Ensure that `p_value` is reported and `flops_saved` is non-negative.

## Testing

Run the test suite to verify contract compliance:
```bash
pytest code/tests/ -v
```

## Troubleshooting

- **Memory Error**: If you encounter OOM on CPU, reduce the `--sample-size` or switch to `CodeLlama-0.5b` (set `--model-id codellama/CodeLlama-0.5b-Instruct-hf`).
- **Model Not Found**: If the CodeLlama checkpoint is missing, check the HuggingFace Hub manually. The code will raise a clear error if the model cannot be loaded.
- **Slow Inference**: CPU inference is slow. Use the `--sample-size` flag to limit the number of problems.
- **Execution Timeout**: If code execution hangs, ensure `docker` is running or increase the timeout in `code/src/entropy.py`.