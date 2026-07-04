# Quickstart: Quantifying the Impact of Data Compression on Gravitational Wave Event Reconstruction

## Prerequisites
- Python 3.11+
- `pip` or `conda`
- Access to a Linux environment (GitHub Actions or local Linux/macOS)
- System-level `openjpeg` libraries (for `glymur` JPEG2000 support)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd <project-dir>
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `LALSuite` may require system-level installation (e.g., `apt install lalsuite` on Debian/Ubuntu). `glymur` requires `openjpeg`.*

## Data Acquisition

Run the data acquisition script to download and validate GWOSC events:
```bash
python code/01_data_acquisition.py --min-events 15 --output-dir data/raw
```
This script:
- Connects to the GWOSC API (O3a/O3b catalogs).
- Downloads ≥15 CBC events.
- Validates metadata completeness.
- Saves checksums to `data/raw/.checksums`.

## Simulation

Generate simulated injections with ground truth.:
```bash
python code/03_simulation.py --count 50 --model o3b --output-dir data/raw
```

## Compression & Analysis

Run the full pipeline (compression, parameter estimation, analysis):
```bash
python code/02_compression_engine.py --input-dir data/raw --output-dir data/processed
python code/04_parameter_estimation.py --input-dir data/processed --output-dir data/derived --iterations sufficient for convergence
python code/05_analysis.py --input-dir data/derived --output-dir data/derived/stats
```

## Verification

Validate the output against the contract schemas:
```bash
pytest tests/contract/
```

## Troubleshooting

- **Memory Error**: If `LALInference` fails due to RAM, reduce the number of MCMC iterations in `code/04_parameter_estimation.py` (minimum 10,000, but [deferred] recommended for convergence).
- **Missing Dependencies**: Ensure `LALSuite` and `openjpeg` are installed system-wide if imports fail.
- **Convergence Failure**: If Gelman-Rubin (R-hat) > 1.1, the event will be excluded from bias analysis. This is expected for some difficult injections.
- **API Rate Limits**: The `gwosc` client handles retries automatically, but large batch downloads may take time.