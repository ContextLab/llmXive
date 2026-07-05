# Quickstart: The Use of Climate-Smart Agricultural Practices in Rural Areas to Improve Food Security and Livelihoods

## Prerequisites
- Python 3.11+
- Git
- Access to a terminal (Linux/Mac/WSL)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-020-the-use-of-climate-smart-agricultural-pr
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

The pipeline is executed via the `main.py` script located in `code/`.

### Step 1: Data Download & Preprocessing
This step downloads (or mocks) data, merges, and samples it.
```bash
python code/main.py --step download_clean
```
*Output*: `data/processed/features_final.csv`

### Step 2: Statistical Modeling
Fits the Mixed-Effects model and runs diagnostics.
```bash
python code/main.py --step model_fit
```
*Output*: `results/model_output.json`, `results/diagnostics.log`

### Step 3: Robustness & Visualization
Runs bootstrap, leave-one-out, and generates plots.
```bash
python code/main.py --step robustness_viz
```
*Output*: `results/figures/*.png`, `results/robustness_report.json`

### Full Run
To run the entire pipeline end-to-end:
```bash
python code/main.py --full
```

## Verification
- Check `results/diagnostics.log` for VIF warnings.
- Verify `results/figures/` contains at least 4 plot types (scatter, coefficient, map, distribution).
- Ensure `results/model_output.json` contains Bonferroni-corrected p-values.

## Troubleshooting
- **Memory Error**: Ensure `data/processed/` is cleaned and the sampling step ran successfully. The script should auto-limit to ~15k rows.
- **Data Missing**: If LSMS data is unavailable, the script will generate synthetic data and log a warning. Check `logs/pipeline.log`.
- **Timeout**: If the job exceeds 6 hours, the script will log the state and retry with a reduced batch size.
