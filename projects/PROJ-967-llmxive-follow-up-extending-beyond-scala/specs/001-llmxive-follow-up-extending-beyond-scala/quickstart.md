# Quickstart: llmXive Follow-up: Teacher Entanglement vs. Scalar Distillation Loss

## Prerequisites

- Python 3.11+
- `git`
- Access to the `z_reward_eval.parquet` file (placed in `data/raw/`).

## Installation

1. **Clone and Setup**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-967-llmxive-follow-up-extending-beyond-scala
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Data Preparation

**CRITICAL**: The Z-Reward dataset must be manually downloaded and placed in `data/raw/`.
- **Expected File**: `data/raw/z_reward_eval.parquet`
- **Note**: If this file is missing, the pipeline will exit with a "Data Not Found" error. **Do not fabricate data.**

## Running the Pipeline

1. **Ingestion & Feature Engineering**:
   ```bash
   python code/ingestion.py
   python code/features.py
   ```
   - Outputs: `data/processed/features.json`, `data/processed/batch_stats.json`.

2. **Model Training & Evaluation**:
   ```bash
   python code/modeling.py
   ```
   - Outputs: `results/model.pkl`, `results/results.json`.

3. **Run Tests**:
   ```bash
   pytest tests/ -v
   ```

## Expected Outputs

- `results/results.json`: Contains `r2_score`, `mae`, `p_value_permutation`, `null_baseline_mae`, `p_value_baseline`.
- `data/processed/features.json`: JSON array of per-sample features.
- `data/processed/batch_stats.json`: Covariance matrix and dominant eigenvalue.

## Troubleshooting

- **Error: "Data Not Found"**: Ensure `data/raw/z_reward_eval.parquet` exists.
- **Error: "Missing Human Annotations"**: The script logs excluded samples. This is expected behavior (FR-006).
- **Memory Error**: If the dataset is too large, modify `code/ingestion.py` to use `chunksize` parameter in `pd.read_parquet`.
