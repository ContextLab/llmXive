# Quickstart: Transferability of DFT‑D3 Dispersion to Ionic Liquids

## Prerequisites
- **Python 3.11+**
- **Psi4** (CPU-only). Install via conda or the wheel specified in `code/requirements.txt`.

## Installation

1. **Clone the repository**
 ```bash
 git clone <repo-url>
 cd projects/PROJ-735-transferability-of-dft-d3-dispersion-to-
 ```

2. **Environment Activation**
 ```bash
 # Create a virtual environment
 python -m venv venv
 # Activate the environment
 source venv/bin/activate
 # Install dependencies
 pip install -r code/requirements.txt
 ```

## Running the Pipeline

To execute a tiny end-to-end run for verification (producing a small subset of results), use:
```bash
python -m code.main --subset 3
```

To run the full benchmark:
```bash
python -m code.main
```

## Expected Outputs
The pipeline produces the following key artifacts:
- `data/derived/raw_energies.csv`: Interaction energies, D3 contributions, and signed errors.
- `data/derived/scaling_factor.txt`: The fitted scaling factor `s` and its confidence interval.
- `data/derived/correlation_results.csv`: Statistical correlations with bulk properties.
- `docs/benchmark_report.md`: Final summary of raw energy metrics.
- `docs/correlation_report.md`: Detailed report on bulk property associations.
