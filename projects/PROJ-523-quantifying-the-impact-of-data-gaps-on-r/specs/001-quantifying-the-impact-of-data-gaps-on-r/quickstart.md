# Quickstart: Quantifying the Impact of Data Gaps on Reconstructed CMB Maps

## Prerequisites

- Python 3.11+
- pip
- 7 GB RAM, 14 GB Disk (Free-tier CI compatible)

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    # or
    venv\Scripts\activate  # Windows
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `camb` and `healpy` may require system-level compilation tools (gcc, libfftw3).*

## Running the Pipeline

### 1. Pilot Run (Required)

Before the full run, execute a pilot to estimate runtime and determine the maximum number of realizations (N) allowed within 6 hours.

```bash
python code/pipeline/run_analysis.py --mode pilot --n_realizations 3
```

This will output:
- `avg_time_per_realization`: Estimated runtime.
- `max_realizations`: Calculated N to fit 6h.
- `recommended_fractions`: Suggested number of gap fractions if N < 50.

### 2. Full Analysis

Run the full analysis with the dynamically determined parameters.

```bash
python code/pipeline/run_analysis.py --mode full
```

### 3. Sensitivity Analysis

Run the sensitivity sweep (FR-007) after the main analysis.

```bash
python code/analysis/bias_analysis.py --mode sensitivity
```

## Verification

1.  **Check Output Files**: Ensure `data/derived/` contains `.fits` maps and `.yaml` results.
2.  **Validate Schemas**: Run contract tests to ensure data matches `contracts/*.schema.yaml`.
    ```bash
    pytest tests/contract/
    ```
3.  **Verify Runtime**: Check `data/metadata/run_log.yaml` to confirm total time < 6h.

## Troubleshooting

- **Memory Error**: If `healpy` fails, reduce `nside` in `code/config.py` (e.g., to 256) or process maps in chunks.
- **Timeout**: If the pilot run suggests N < 30, the system will automatically reduce the number of gap fractions. Check `run_log.yaml` for the final configuration.
- **Convergence Failure**: If an algorithm fails, it is logged and excluded. Ensure at least 30 valid realizations remain.
