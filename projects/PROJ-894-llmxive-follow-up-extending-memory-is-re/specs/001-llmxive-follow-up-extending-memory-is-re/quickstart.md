# Quickstart: llmXive follow-up: extending "Memory is Reconstructed, Not Retrieved: Graph Memory for LLM Agents"

## Prerequisites

- Python 3.11+
- Git
- Sufficient RAM (for CPU quantized inference)
- Access to HuggingFace Hub (free account required for some datasets, though LoCoMo is public)
- `spacy` model downloaded (e.g., `python -m spacy download en_core_web_sm`)

## Installation

1. **Clone the Repository**:
 ```bash
 git clone
 cd llmxive-follow-up
 ```

2. **Create Virtual Environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install Dependencies**:
 ```bash
 pip install -r requirements.txt
 ```
 *Note: `requirements.txt` includes `llama-cpp-python` with CPU-only wheels.*

4. **Download Model (Optional)**:
 - If using a specific quantized model, download it via `huggingface-cli` or `llama.cpp` scripts.
 - Example: `llama-cpp-python` will auto-download if configured in `config.py`.

## Running the Pipeline

### 1. Data Preparation
Download and generate graphs:
```bash
python code/data_loader.py --download --generate-graphs --seed 42
```
- This fetches LoCoMo and generates synthetic noisy graphs in `data/processed/graphs/`.

### 2. Execute Strategies
Run the full, lazy, and greedy strategies on a subset (A set of tasks will be established for testing.):
```bash
python code/runner.py --strategy full --subset 10
python code/runner.py --strategy lazy --subset 10 --threshold 0.7
python code/runner.py --strategy greedy --subset 10 --top-k 5
```
- **Timeout**: Each task has a time limit.
- **Output**: Results saved to `data/processed/results/`.

### 3. Statistical Analysis
Run the analysis script:
```bash
python code/analysis.py --results data/processed/results/
```
- This generates `data/processed/analysis/stats.json` with p-values, correlations, and inflection points.

### 4. Full Benchmark (Optional)
To run on the full LoCoMo subset (may take several hours):
```bash
python code/runner.py --strategy full
python code/runner.py --strategy lazy
python code/runner.py --strategy greedy
python code/analysis.py --results data/processed/results/
```

### 5. Versioning & Hashing
Run the versioning script to update the state file:
```bash
python code/utils/hash_artifacts.py
```

## Troubleshooting

- **Memory Error**: If OOM occurs, reduce the subset size or use a smaller quantized model (e.g., a parameter-efficient scale).
- **Timeout**: If tasks exceed 30 minutes, check `data/logs/timeout.log` for details. The system will skip the task and continue.
- **Graph Errors**: If graphs are disconnected, check `data/logs/graph_errors.log`. The system flags these as "unresolved" but continues.

## Expected Outputs

- `data/processed/results/full_results.csv`: Baseline metrics.
- `data/processed/results/lazy_results.csv`: Lazy strategy metrics.
- `data/processed/results/greedy_results.csv`: Greedy strategy metrics.
- `data/processed/analysis/stats.json`: Statistical report.