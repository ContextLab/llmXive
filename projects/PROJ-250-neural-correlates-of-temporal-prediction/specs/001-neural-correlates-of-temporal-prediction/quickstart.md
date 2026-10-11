# Quickstart: Neural Correlates of Temporal Prediction Errors in Auditory Scene Analysis

## Prerequisites

- Python 3.x (recent versions)
- Git
- GitHub Actions Runner or Linux environment with $\ge 7$ GB RAM.

## Installation

1. **Clone and Setup**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-250-neural-correlates-of-temporal-prediction
   python -m venv venv
   source venv/bin/activate
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

The pipeline is executed in sequence via the `code/` directory.

### 1. Data Acquisition
```bash
python code/download.py
```
- Downloads an OpenNeuro dataset.
- Verifies checksums and metadata.
- **Halt Condition**: Stops if the "complex" condition is missing from the dataset.

### 2. Preprocessing
```bash
python code/preprocess.py
```
- Applies a low-frequency bandpass filter (up to 40 Hz).
- Performs ICA artifact rejection.
- Re-references to average mastoids.
- Subtracts baseline (pre-stimulus mean over a standard temporal window preceding stimulus onset).
- Segments data into epochs (pre-stimulus to post-stimulus window).

### 3. Analysis
```bash
python code/analysis.py
```
- Computes MMN amplitude/latency.
- Validates SNR above a standard threshold using SEM denominator.
- Generates canonical MMN topography template from 'simple' condition.
- Performs topographic consistency check (simple vs. template).
- Performs topographic validity check (complex vs. template).
- Performs paired t-tests with FDR correction.
- Calculates Cohen's $d$ and topographic correlations.

### 4. Visualization
```bash
python code/visualize.py
```
- Generates ERP waveforms, scalp maps, and significance plots in `results/figures/`.

## Validation

Run the contract tests to ensure data integrity and statistical validity:
```bash
pytest tests/
```
This verifies:
- `results/metrics.csv` matches `contracts/output.schema.yaml`.
- `results/stats.json` matches `contracts/stats.schema.yaml`.
- Signal validity logic (SNR above a standard threshold using SEM) is correctly applied.
- FDR-corrected p-values are used for significance flags.
- Topographic consistency and validity checks are properly distinguished.
