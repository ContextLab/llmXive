# Quickstart: Quantifying the Effects of Data Noise on Dynamical Systems Reconstruction

## Prerequisites

- Python 3.11+
- Git
- 7GB RAM (minimum)
- 2 CPU cores

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd <project-root>
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

To execute the full analysis (Lorenz and Rössler systems, all SNR levels, both noise types, N=50 realizations):

```bash
python code/main.py --systems lorenz rossler --noise gaussian quantization --snr 0 5 10 15 20 25 30 --realizations 50
```

### Arguments

- `--systems`: List of systems to simulate (`lorenz`, `rossler`).
- `--noise`: List of noise types to apply (`gaussian`, `quantization`).
- `--snr`: List of SNR levels in dB.
- `--bits`: (Optional) Quantization bits for quantization noise (default: 8).
- `--seed`: (Optional) Random seed for reproducibility (default: 42).
- `--realizations`: Number of independent trajectory realizations per condition (default: 50).

## Output

Results are saved to the `results/` directory:

- `lookup_table.csv`: The primary output containing mean error rates and confidence intervals across SNR levels.
- `plots/error_vs_snr.png`: Visualization of metric degradation with confidence bands.
- `data/processed/`: Intermediate data files (noisy trajectories, metric results).

### Viewing Results

```bash
# View the lookup table
cat results/lookup_table.csv

# View the plots (requires a GUI or image viewer)
xdg-open results/plots/error_vs_snr.png
```

## Verification

To verify the pipeline against known ground truth (Lorenz clean data, N=50 realizations):

```bash
python code/main.py --systems lorenz --noise none --verify --realizations 50
```

This will run the metric computation on clean data, compare the mean against literature values, and print a pass/fail status.