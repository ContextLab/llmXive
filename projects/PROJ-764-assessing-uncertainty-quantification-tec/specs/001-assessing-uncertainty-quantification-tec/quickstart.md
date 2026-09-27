# Quickstart: Assessing Uncertainty Quantification Techniques for Machine‑Learning Predicted Material Properties

## Prerequisites

- Python 3.11+
- Git
- 8 GB RAM (recommended for smooth operation within 5h budget)

## Installation

1. **Clone and Setup Environment**
   ```bash
   git clone <repository-url>
   cd projects/PROJ-764-assessing-uncertainty-quantification-tec
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r code/requirements.txt
   ```

2. **Verify Data Access**
   Ensure you have internet access to download the OQMD dataset from Hugging Face. The script will automatically download the data if `data/raw/` is empty.

## Running the Pipeline

### Full Pipeline (5-hour limit enforced)
```bash
python code/main.py
```
This command:
1. Downloads and validates data.
2. Trains Baseline, Deep Ensemble, MC Dropout, and Sparse GP models.
3. Performs inference and generates uncertainty intervals.
4. Computes calibration metrics and screening results (Bootstrap CI).
5. Stops automatically if runtime exceeds 5 hours.

### Individual Components

**Download & Preprocess Only**
```bash
python code/data/download.py
python code/data/preprocess.py
```

**Train Specific Model**
```bash
# Deep Ensemble
python code/models/deep_ensemble.py --seed <random_seed>

# Sparse GP
python code/models/sparse_gp.py --seed
```

**Evaluate Results**
```bash
python code/eval/calibration.py
python code/eval/screening.py
```

## Output Artifacts

After successful completion, the following files will be available:

- `results/uq_predictions.csv`: Predictions with uncertainty bounds.
- `results/calibration_report.csv`: ECE, Interval Scores, Sharpness.
- `results/reliability_diagrams/`: PNG plots for each method.
- `results/robustness_report.json`: Stability metrics across seeds.
- `data/validation_report.json`: Data exclusion summary.

## Troubleshooting

- **Timeout Error**: If the pipeline fails with a timeout, reduce the dataset size in `code/data/preprocess.py` (e.g., sample a subset of rows).
- **OQMD Download Failed**: Check internet connection. The script retries a limited number of times with exponential backoff.
- **GP Convergence Failed**: The Sparse GP may fail if the inducing points are poorly initialized. The script falls back to standard GP or logs a warning (see `results/logs/`).