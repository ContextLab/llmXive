# Quickstart: The Impact of Visual Crowding on Facial Emotion Recognition Accuracy

## Prerequisites

- Python 3.11+
- pip (package manager)
- Git
- Sufficient disk space (~ GB for RAVDESS + generated stimuli)

## Installation

1.  **Clone the Repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-357-the-impact-of-visual-crowding-on-facial-/
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

### Step 1: Download Data
Download and cache the RAVDESS dataset.
```bash
python code/utils/download.py --source ravdess
```
*Output*: `data/raw/ravdess.zip` and checksum file.

### Step 2: Generate Stimuli
Generate crowding stimuli with default parameters.
```bash
python code/utils/stimulus_gen.py --flanker-counts 1 3 5 --eccentricities 2 4 6
```
*Output*: `data/interim/stimuli/` directory and `stimulus_manifest.json`.

### Step 3: Compute Clutter Metrics
Compute visual clutter metrics for all generated stimuli.
```bash
python code/utils/clutter_metrics.py --input data/interim/stimuli/
```
*Output*: `data/processed/clutter_metrics.csv`.

### Step 4: Simulate/Collect Human Data
*(Note: Replace with actual data collection script if IRB approved. This command generates synthetic data for testing.)*
```bash
python code/analysis/generate_synthetic_data.py --n-participants <NUM_PARTICIPANTS> --n-trials 1000
```
*Output*: `data/processed/human_judgments.csv`.

### Step 5: Run Analysis
Fit the GLMM and generate the report.
```bash
python code/analysis/glmm_model.py
```
*Output*: `artifacts/regression_results.yaml`, `reports/analysis_report.md`.

## Testing

Run the unit tests to verify the pipeline:
```bash
pytest tests/unit/ -v
```

Run integration tests:
```bash
pytest tests/integration/ -v
```

## Troubleshooting

- **Convergence Failure**: If the GLMM fails to converge, the script will automatically fall back to a fixed-effects model and log a warning. Check `artifacts/model_config.yaml` for details.
- **Memory Error**: If you encounter memory errors, reduce the number of stimuli or participants in the configuration file (`code/config.py`).
- **Missing RAVDESS**: Ensure the verified URL is accessible. If not, check your network or use a local copy placed in `data/raw/`.
