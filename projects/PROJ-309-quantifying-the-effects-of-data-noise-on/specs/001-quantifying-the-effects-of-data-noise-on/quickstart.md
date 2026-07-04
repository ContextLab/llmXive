# Quickstart: Quantifying the Effects of Data Noise on Dynamical Systems Reconstruction

## Prerequisites

-   Python 3.11+
-   Git
-   2 CPU cores, 7GB RAM (standard GitHub Actions runner)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-309-quantifying-the-effects-of-data-noise-on
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
    *Note: `requirements.txt` pins exact versions to ensure reproducibility.*

## Running the Pipeline

### 1. Generate Clean Data
```bash
python code/generators.py --system Lorenz --steps 5000 --seed 42 --replicates 10
python code/generators.py --system Rössler --steps 5000 --seed 42 --replicates 10
```
*Output: `data/raw/clean/` (files named `<system_type>_<uuid>.npz`)*

### 2. Inject Noise
```bash
python code/noise.py --input data/raw/clean/ --snr_levels 0 5 10 15 20 25 30 --noise_types Gaussian Quantization
```
*Output: `data/raw/noisy/` (files named `<system_type>_<noise_type>_<snr>_<replicate_id>.npz`)*

### 3. Compute Metrics
```bash
python code/metrics.py --input data/raw/noisy/ --algorithm GP Rosenstein FNN
```
*Output: `data/processed/metrics/`*

### 4. Analyze & Visualize
```bash
python code/analysis.py --input data/processed/metrics/ --threshold 30
python code/visualize.py --input data/results/error_vs_snr.csv --output data/results/plots/
```
*Output: `data/results/error_vs_snr.csv`, `data/results/plots/`*

### 5. Run Tests
```bash
pytest tests/
```
*Validates unit tests, contract schemas, and integration flows.*

## Expected Outputs

-   **Lookup Table**: `data/results/error_vs_snr.csv` containing SNR, noise type, metric, and error rate.
-   **Plots**: Line plots showing error vs. SNR with critical threshold markers.
-   **Logs**: Console output detailing runtime, SNR accuracy, and any warnings (e.g., "Insufficient data").

## Troubleshooting

-   **Runtime Error**: If the pipeline exceeds 2 hours, reduce `--steps` to 5000 in `generators.py` (already default).
-   **SNR Mismatch**: If measured SNR deviates >0.5dB, check `noise.py` for variance calculation errors.
-   **Memory Error**: If OOM occurs, process trajectories in batches (modify `metrics.py`).