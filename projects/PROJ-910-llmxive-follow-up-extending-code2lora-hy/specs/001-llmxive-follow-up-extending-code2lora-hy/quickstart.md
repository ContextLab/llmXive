# Quickstart: AST-Based Adapter Generation

This guide provides a step-by-step walkthrough to generate an AST-based LoRA adapter and evaluate it on the RepoPeftBench dataset.

## Prerequisites

- Python 3.9+
- Installed dependencies: `pip install -r requirements.txt`
- Access to a machine with at least 8 GB RAM (GPU optional for evaluation)

## Step 1: Download Real Data

The pipeline requires real data. Do not use synthetic data.

### Download RepoPeftBench (Evaluation Dataset)

```bash
python code/data/download_repopeftbench.py
```

This script fetches the Python subset of RepoPeftBench from HuggingFace and saves it to `data/raw/`.

### Download Sample Repository (Adapter Generation)

```bash
python code/data/download_sample_repo.py
```

This script fetches a small, real Python repository (e.g., `requests` or `flask`) from GitHub and saves it to `data/raw/`.

## Step 2: Generate AST-Based Adapter

Run the adapter generation pipeline on the sample repository:

```bash
python code/main.py generate --repo-path data/raw/sample_repo --output data/adapters/sample_adapter.safetensors
```

**What happens:**
1. The system extracts AST features (cyclomatic complexity, inheritance depth, token histograms, import graph centrality).
2. The hypernetwork (MLP) projects these features into LoRA adapter weights.
3. The adapter is saved as a `.safetensors` file.

**Resource Limits:**
- CPU: Restricted to 2 cores.
- RAM: Aborts if usage exceeds 7 GB.

## Step 3: Evaluate Adapter Performance

Evaluate the generated adapter on RepoPeftBench:

```bash
python code/main.py evaluate --adapter data/adapters/sample_adapter.safetensors --output data/results/ast_scores.csv
```

This computes exact-match scores for each task in the benchmark.

## Step 4: Compare with Neural Baseline

Compare the AST-based adapter against the original Code2LoRA neural baseline:

```bash
# Load baseline adapter and compute scores
python code/evaluation/baseline_loader.py

# Generate comparison report
python code/evaluation/comparison_report.py
```

Output: `data/results/comparison_report.csv` and `data/results/stats.json` (Wilcoxon signed-rank test).

## Step 5: Sensitivity Analysis (Optional)

Determine the minimal feature set required to maintain >80% of baseline accuracy:

```bash
python code/main.py sensitivity --output data/results/sensitivity_summary.csv
```

## Step 6: Verify Resource Constraints

Check that resource limits were respected:

```bash
cat data/results/resource_summary.csv
```

Verify:
- Peak RAM ≤ 7 GB
- Total runtime ≤ 6 hours
- CPU restricted to 2 cores

## Troubleshooting

### Data Missing Error

If you see an error about missing data, ensure you ran the download scripts in Step 1.

```bash
python code/data/download_repopeftbench.py
python code/data/download_sample_repo.py
```

### Memory Limit Exceeded

If the process aborts due to memory usage > 7 GB, try:
- Running on a machine with more RAM.
- Reducing the size of the input repository.

### CUDA Out of Memory

Evaluation may require GPU memory. If you encounter this error, try:
- Running evaluation on CPU (slower but functional).
- Reducing the batch size in `code/evaluation/runner.py`.

## Next Steps

- Review `specs/001-ast-based-adapter-generation/` for detailed design documents.
- Run the full test suite: `pytest tests/`
- Explore sensitivity analysis results in `data/results/sensitivity_summary.csv`.