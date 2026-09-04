# Quickstart: Neural Correlates of Temporal Prediction Errors in Auditory Scene Analysis

## Prerequisites

- Python 3.11+
- Git
- Access to a GitHub Actions runner (or local environment with 7 GB+ RAM).

## Installation

1.  **Clone the repository** and navigate to the project directory:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-250-neural-correlates-of-temporal-prediction
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
    *Note: `requirements.txt` pins `mne`, `numpy`, `pandas`, `scipy`, `matplotlib`, `seaborn`, `statsmodels`.*

## Running the Pipeline

The pipeline is orchestrated via `code/main.py`.

### Step 1: Download and Verify Data
```bash
python code/download.py
```
- Downloads the dataset (OpenNeuro ds000246 or alternative with complex condition).
- Verifies checksums and condition labels.
- **HALTS** if "complex" condition is missing or derived heuristically.
- Outputs to `data/raw/`.

### Step 2: Preprocess Data
```bash
python code/preprocess.py
```
- Applies bandpass filter (1–40 Hz).
- Runs ICA for artifact rejection.
- Re-references to average mastoids.
- Segments epochs (-200 to 500 ms).
- Outputs to `data/processed/epochs.fif`.

### Step 3: Analyze MMN Metrics
```bash
python code/analysis.py
```
- Computes MMN amplitude and latency for simple/complex conditions.
- Performs **Interaction Test** (ANOVA/LMM) with FDR correction.
- Calculates SNR and signal validity.
- Calculates topographic correlation against canonical template.
- Compares effect size against literature benchmark.
- Outputs `results/metrics.csv` and `results/stats.json`.

### Step 4: Generate Visualizations
```bash
python code/visualize.py
```
- Generates ERP waveforms, scalp topographies, and significance plots.
- Outputs to `results/figures/`.

## Validation

To verify the pipeline integrity:
```bash
pytest tests/
```
- Runs contract tests against `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml`.
- Checks for NaNs in epoch data.
- Verifies that `p_value_fdr` < 0.05 implies `significant` = True.
- Verifies `signal_validity` logic.
- Verifies `practical_significance` logic.

## Troubleshooting

- **"Dataset lacks required 'complex' condition"**: The dataset does not contain the necessary experimental design. The pipeline halts as per FR-008. Check `research.md` for fallback options.
- **"Circular Logic Detected"**: The `condition_label` was derived from `stimulus_type`. The pipeline halts to prevent invalid statistics.
- **Memory Error**: If running locally, reduce the number of subjects or use streaming mode (if implemented).
- **NaNs in Data**: The pipeline halts. Check preprocessing steps for ICA component rejection thresholds.