# Quickstart: Exploring the Validity of the Weak Equivalence Principle with Publicly Available Planetary Orbital Data

## Prerequisites

- Python 3.11 or higher
- `pip` (Python package installer)
- Access to the internet (for downloading JPL Horizons data and INPOP19a)
- Sufficient disk space (for data and dependencies)

## Installation

1.  **Clone the repository** and navigate to the project directory:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-348-exploring-the-validity-of-the-weak-equiv
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
    *Note: `requirements.txt` includes `rebound`, `astroquery`, `scipy`, `numpy`, `pandas`.*

## Running the Pipeline

The pipeline is designed to run end-to-end. Execute the main entry point:

```bash
python -m src.main
```

### Step-by-Step Execution

1.  **Data Download**:
    The script will automatically download JPL Horizons data for Mercury, Venus, Earth, and Mars (mid-20th century to present) and save them to `data/raw/`.
    *   *Status*: You will see logs like `Downloading JPL data for Mercury...`

2.  **INPOP Download**:
    The script will download INPOP19a data for cross-validation.
    *   *Status*: Logs will indicate `Downloading INPOP19a data...`

3.  **GR Baseline Generation**:
    The `rebound` integrator will compute the GR-predicted trajectories.
    *   *Status*: Logs will indicate `Running IAS15 integrator...` and `Verifying Mercury precession...`.

4.  **Differential Validation**:
    The system will compute the difference between JPL and INPOP ephemerides and check the specified tolerance.
    *   *Status*: `Computing differential residuals...` and `Validating against INPOP19a...`. **Action**: Halts if RMS > 1 km.

5.  **Parameter Estimation**:
    The system will fit PPN parameters and perform the Nordtvedt regression on the differential signal.
    *   *Status*: Logs will show `Fitting PPN parameters...` and `Running OLS regression...`.

6.  **Monte Carlo Simulation**:
    The system will run a sufficient number of iterations to generate the null distribution.
    *   *Status*: `Running Monte Carlo simulation (10000 iterations)...`

7.  **Validation & Output**:
    Results are compared against INPOP19a (if available) and saved to `results/`.

## Output Artifacts

Upon successful completion, the following files will be generated:

- `results/regression_stats.json`: Contains $\gamma, \beta, \eta$ fits and OLS regression results.
- `results/mc_distribution.json`: Contains the null distribution and p-values.
- `data/derived/differential_residuals.csv`: The cleaned dataset used for analysis.
- `logs/pipeline.log`: Detailed execution log.

## Troubleshooting

- **API Rate Limit Errors**: The script includes automatic backoff. If it fails after a maximum number of retries, check your network connection.
- **Missing INPOP Data**: If INPOP19a download fails, the script will log a warning and proceed with JPL-only validation.
- **Memory Errors**: If you encounter `MemoryError`, ensure no other heavy processes are running. The pipeline is optimized for < 7 GB RAM.
- **Convergence Issues**: If the Monte Carlo simulation fails to converge, check `logs/pipeline.log` for the specific error code (e.g., `E-MC-NON-CONVERGE`).
- **Sample Size Error**: If an insufficient number of planets have valid binding energy data, the pipeline will halt with error code `E-SAMPLE-INSUFFICIENT`.

## Verification

To verify the installation and baseline accuracy:

```bash
python -m pytest tests/test_integrator.py -v
```
This test ensures the Mercury precession rate is within the expected tolerance (±0.1 arcseconds/century).
