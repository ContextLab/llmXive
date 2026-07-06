# Quickstart: Assessing Uncertainty Quantification Techniques

## Prerequisites

- Python 3.11+
- Git
- GitHub Actions Runner (or local environment with ≥2 GB RAM)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-737-assessing-uncertainty-quantification-tec
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

## Execution

### Running the Full Pipeline

Execute the main orchestration script. This will:
1.  Download and preprocess datasets (OQMD, AFLOW).
2.  Train GPR, MC Dropout, Deep Ensembles, and Conformal Prediction models.
3.  Calculate Calibration Error and Sharpness.
4.  Perform statistical significance testing.
5.  Output `data/results/metrics_summary.csv`.

```bash
python code/main.py
```

### Running Specific Components

- **Data Download Only**:
  ```bash
  python code/main.py --stage download
  ```
- **Model Training Only** (requires data to be present):
  ```bash
  python code/main.py --stage train
  ```
- **Evaluation Only**:
  ```bash
  python code/main.py --stage evaluate
  ```

## Verification

After running, verify the results:
1.  Check `data/results/metrics_summary.csv` for the presence of all 12 method-dataset combinations.
2.  Ensure no "OOM" (Out of Memory) errors occurred.
3.  Verify that the `p_value` column contains values < 0.05 for significant differences (if any).

## Troubleshooting

- **Memory Error**: If the script crashes with OOM, reduce the `MAX_SAMPLES` constant in `code/config.py` from 10000 to 5000.
- **Dataset Missing**: If Elastic Modulus data is missing, the script will log a warning and skip that property. Check `logs/pipeline.log` for details.
- **Import Errors**: Ensure all dependencies in `requirements.txt` are installed. If `torch` fails, install the CPU version explicitly: `pip install torch --index-url https://download.pytorch.org/whl/cpu`.
