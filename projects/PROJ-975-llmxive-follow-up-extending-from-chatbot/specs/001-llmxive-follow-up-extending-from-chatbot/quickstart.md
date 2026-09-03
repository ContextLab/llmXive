# Quickstart: llmXive follow-up

## Prerequisites

- Python 3.11+
- `pip` or `venv`
- Access to a standard Linux environment (GitHub Actions compatible)

## Installation

1.  **Clone the repository** (if not already done):
    ```bash
    git clone <repo-url>
    cd projects/PROJ-975-llmxive-follow-up-extending-from-chatbot
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` pins `sentence-transformers`, `scikit-learn`, `pandas`, `numpy`, `pytest`, `jsonschema`.*

4.  **Install pre-commit hooks** (optional but recommended):
    ```bash
    pre-commit install
    ```

## Running the Experiment

### 1. Generate Synthetic Data
Run the data generation script to create the tasks and a set of skills.
```bash
python code/generate_data.py
```
*Output*: `data/raw/tasks.json`, `data/raw/skills.json`.

### 2. Run Baseline Experiments
Execute the agent across a range of library sizes with and without pruning.
```bash
python code/run_baseline.py
```
*Output*: `data/results/experiment_log.csv`, `data/results/experiment_log_baseline.csv`.

### 3. Analyze Results
Run the statistical analysis to find the tipping point and pruning effects.
```bash
python code/analyze.py
```
*Output*: `data/results/tipping_point.json`, `data/results/pruning_analysis.json`.

## Verification

To verify the setup:
```bash
pytest tests/
```
Ensure all unit and contract tests pass.

## Troubleshooting

- **Memory Error**: If you encounter OOM errors, check that `sentence-transformers` is using the CPU version and that the dataset is not being loaded into memory multiple times.
- **Missing Skills**: If the agent fails to find skills, verify the `embedding_vector` generation in `generate_data.py`.
- **Reproducibility**: Ensure `PYTHONHASHSEED` is set if running in parallel, though the scripts use fixed seeds internally.