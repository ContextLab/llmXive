# Quickstart: Exploring the Distribution of Smooth Numbers in Short Intervals

## Prerequisites

-   Python 3.11+
-   A POSIX-compliant environment (Linux/macOS/WSL)
-   At least 7 GB of available RAM
-   6 hours of CPU time (estimated)

## Installation

1.  **Clone the repository** (or navigate to the project directory).
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

The pipeline consists of three sequential steps. Run them in order.

### Step 1: Generate Prime Sieve
Generates the list of primes up to a large magnitude. This may take a moderate amount of time.
```bash
python code/sieve.py --limit 1000000000 --output data/primes_1e9.csv
```
*Verification*: Check that the line count of the output file is consistent with the expected scale.

### Step 2: Compute Density Measurements
Runs the enumeration across the parameter grid (fixed $h$ values). This may take several hours.
```bash
python code/smoothness.py \
  --primes data/primes_1e9.csv \
  --output data/density_measurements.csv \
  --grid-file specs/001-exploring-the-distribution-of-smooth-numbers/grid_config.yaml
```
*Note*: The `grid_config.yaml` defines the $x, y$ ranges and the fixed $h$ values (spanning several orders of magnitude) with Multiple random seeds per configuration.

### Step 3: Statistical Analysis & Visualization
Fits the weighted power-law model and generates plots.
```bash
python code/analysis.py \
  --input data/density_measurements.csv \
  --output data/model_fits.json \
  --plot-dir data/figures
```

## Testing

Run the unit tests to verify the logic:
```bash
pytest tests/ -v
```

## Expected Outputs

-   `data/primes_e9.csv`: ~200MB CSV file.
- `data/density_measurements.csv`: CSV with [deferred] rows (includes `u_value`, `rho_theory`, `deviation_ratio`).
-   `data/model_fits.json`: JSON containing regression coefficients and KS test p-values.
-   `data/figures/`: Directory containing PNG plots of the deviation ratio vs. interval length.