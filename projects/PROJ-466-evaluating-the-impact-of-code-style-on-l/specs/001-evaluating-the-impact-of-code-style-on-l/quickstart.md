# Quickstart: Evaluating the Impact of Code Style on LLM Code Generation Diversity

## Prerequisites

- Python 3.11+
- GB RAM available
- Git

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-466-evaluating-the-impact-of-code-style-on-l
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins specific versions of `transformers`, `torch`, and `scikit-learn` to ensure CPU compatibility.*

## Configuration

Edit `code/config/generation.yaml` to set:
- `batch_size`: Start with 50 (will auto-reduce if OOM).
- `max_tasks`: Number of tasks to process (e.g., 50 for testing, 164 for full run).
- `seed`: 42 (fixed).
- `samples_per_task`: **20** (increased from 5 for statistical robustness).

Edit `code/config/analysis.yaml` to set:
- `alpha`: 0.05 (default significance threshold).
- `sweep_thresholds`: [0.01, 0.05, 0.1].

## Running the Pipeline

### 1. Download Data
```bash
python code/generation/loader.py
```
This downloads the HumanEval subset to `data/raw/`.

### 2. Generate & Filter
```bash
python code/main.py --mode generate
```
This performs:
- Generation of **multiple samples** for all styles.
- Saves `samples_all.csv` (unfiltered).
- Executes unit tests.
- Saves `samples_valid.csv` (filtered).
- **Halt Condition**: If pass rate < 1% for any style, the script exits with a "Model Incapability" error.

### 3. Compute Metrics
```bash
python code/main.py --mode metrics
```
Computes AST distance and n-gram entropy for both `samples_all` (producing `metrics_all.csv`) and `samples_valid` (producing `metrics_valid.csv`).

### 4. Statistical Analysis
```bash
python code/main.py --mode stats
```
Runs Kruskal-Wallis H-test, Dunn's post-hoc, and sensitivity analysis. Generates `stats_results.json`.

### 5. Generate Report
```bash
python code/main.py --mode report
```
Generates `artifacts/report.pdf` with plots and statistics.

## Verification

Run the test suite to ensure environment integrity:
```bash
pytest tests/ -v
```

## Troubleshooting

- **OOM Error**: The system automatically reduces batch size. If it reduces to 1 and still fails, increase RAM or reduce `max_tasks`.
- **401 Error on Dataset**: Ensure you are logged into Hugging Face (`huggingface-cli login`) if the dataset requires it, though `openai/human-eval` is public. The `datasets` library handles this automatically.
- **Timeout**: If a single task takes >5 minutes, it is skipped and logged.
- **Model Incapability**: If the log shows "Model Incapability", the pass rate was < 1%. No diversity analysis can be performed for that style.
