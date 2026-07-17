# Quickstart: llmXive follow-up: extending "Lens: Rethinking Training Efficiency for Foundational Text-to-Image Mo"

## Prerequisites

- Python 3.11+
- `pip`
- At least 15 GB of free disk space (for raw data and processed artifacts)
- A GitHub Actions runner (or local machine) with CPU access.

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/llmxive-follow-up.git
   cd llmxive-follow-up
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `requirements.txt` pins `transformers`, `spacy`, `xgboost`, `scikit-learn`, `pandas`, `pyarrow`, `ruff`, `black`.*

4. **Download spaCy model**:
   ```bash
   python -m spacy download en_core_web_sm
   ```

5. **Configure Linting (Optional but recommended)**:
   The project uses `pyproject.toml` for Black and Ruff configuration.
   ```bash
   # Format code
   black code/
   # Lint code
   ruff check code/
   ```

## Running the Pipeline

**Note**: All commands below assume you are running from the **repository root** (the directory containing `code/`, `data/`, etc.).

### Step 1: Download Data
The script downloads the verified Pick-a-Pic dataset to `data/raw`.
```bash
python code/data/loader.py
```
*Output*: `data/raw/pick-a-pic.parquet` (or streaming cache).
*Error Handling*: If the dataset lacks `preference_score`, the script raises a `ValueError` and exits. No synthetic data is generated.

### Step 2: Extract Features
Computes linguistic features from raw text.
```bash
python code/data/features.py
```
*Output*: `data/processed/features.csv`

### Step 3: Compute Deviation
Calculates the target variable (using raw difference).
```bash
python code/data/preprocess.py
```
*Output*: `data/processed/deviation.csv`
*Error Handling*: If the target has zero variance, the script raises `ValueError("Target not learnable")`.

### Step 4: Train Model & Run Sensitivity
Trains XGBoost and runs the stability loop (5 seeds).
```bash
python code/models/train.py
```
*Output*: `results/stability_metrics.json`, `results/model.pkl`

## Verification

Run the test suite to ensure the pipeline is healthy:
```bash
pytest code/tests/ -v
```

## Troubleshooting

- **"Dataset missing required 'preference_score' column"**: The verified dataset does not contain human ratings. The pipeline has halted to prevent fabrication. Check the dataset schema in `data/raw`.
- **"Memory limit exceeded"**: Ensure `streaming=True` is used in `loader.py`. If running locally, reduce the sample size in the config.
- **"CUDA error"**: The code is designed for CPU. If you see CUDA errors, ensure `device="cpu"` is set in `transformers` and `xgboost`.
- **"Zero Variance in Target"**: The human ratings and CLIP scores are identical for the sample. Check data quality.