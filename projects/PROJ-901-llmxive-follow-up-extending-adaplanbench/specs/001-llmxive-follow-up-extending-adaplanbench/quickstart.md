# Quickstart: llmXive follow-up: extending "AdaPlanBench: Evaluating Adaptive Planning in Large Language Model Age"

## Prerequisites

- Python 3.11+
- Access to a GitHub Actions runner (or local machine with sufficient RAM and CPU cores).
- HuggingFace CLI (if downloading models).

## Installation

1. **Clone the repository** and navigate to the project directory.
   ```bash
   cd projects/PROJ-901-llmxive-follow-up-extending-adaplanbench
   ```

2. **Create a virtual environment** and install dependencies.
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Verify Dataset Availability**.
   - Check if the AdaPlanBench dataset is accessible.
   - *Note*: As per the research plan, if the dataset is not found, the script will halt.
   ```bash
   python code/dataset/loader.py --verify-only
   ```

## Running the Pipeline

### 1. Data Preparation
Filter the dataset to include only tasks with ≥5 constraints and generate distribution summary.
```bash
python code/dataset/loader.py --filter-min-constraints 5 --output data/processed/filtered_tasks.csv
```
*Output*: `filtered_tasks.csv` and `distribution_summary.json`.

### 2. Power Analysis
Run the power analysis to confirm sample size sufficiency.
```bash
python code/analysis/power.py --input data/processed/filtered_tasks.csv
```
*Output*: A report indicating if the current sample size is sufficient for the target effect size ($f^ \ge 0.15$).

### 3. Agent Execution
Run both the Monolithic and Dual-Track agents.
```bash
python code/main.py --mode full --model phi-3-mini --output data/processed/execution_logs.csv
```
*Note*: This script includes resource monitoring. If RAM usage exceeds a predefined threshold, it will log a warning and attempt to reduce batch size.

### 4. Statistical Analysis
Fit the GLMM and generate results.
```bash
python code/analysis/glmm.py --input data/processed/execution_logs.csv --output data/processed/results.json
```

### 5. Human Validation (Optional)
Run the annotation script (requires manual review). The sample size is dynamically calculated based on desired precision.
```bash
python code/dataset/annotator.py --input data/processed/execution_logs.csv --target-kappa-precision 0.10
```

## Troubleshooting

- **OOM Error**: If you encounter "Out of Memory", ensure no other heavy processes are running. Try reducing the `--batch-size` in `main.py` or switching to a smaller model (e.g., `SmolLM-135M`).
- **Dataset Not Found**: If the loader fails to find AdaPlanBench (ID: `adaplanbench/adaplanbench`), check the `code/config.py` for the correct source URL. If no verified source exists, the project cannot proceed.
- **GLMM Convergence**: If the model fails to converge, check `data/processed/results.json` for the `convergence_status` flag. You may need to increase the `max_iter` parameter in `glmm.py`.
- **Static Constraints**: If the dataset lacks progressive constraints, the script will halt with a "Data Incompatibility" error.