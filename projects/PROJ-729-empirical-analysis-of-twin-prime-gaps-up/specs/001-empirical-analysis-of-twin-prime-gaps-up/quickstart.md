# Quickstart: Empirical Analysis of Twin Prime Gaps up to 10⁹

## Prerequisites

- Python 3.11+
- `pip`
- Access to a terminal (Linux/macOS/WSL)

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `primesieve` may require a C++ compiler if a wheel is not available for your platform, but pre-built wheels exist for Ubuntu 22.04.*

## Running the Pipeline

The pipeline consists of five steps: Generation, Validation, Analysis, Hashing, and Reporting.

### Step 1: Generate Data
Generate the twin prime dataset up to a large upper bound.:
```bash
python code/generate_primes.py
```
*Output*: `data/raw/twin_primes.csv`

### Step 2: Validate Schema
Ensure the generated data matches the required schema:
```bash
python code/validate_schema.py
```
*Output*: Exit code 0 if valid, 1 if invalid. **This is a blocking gate.**

### Step 3: Run Analysis
Perform the statistical tests and generate plots:
```bash
python code/analyze_gaps.py
python code/analyze_local.py
```
*Output*: `data/results/stats.json`, `data/figures/qq_plot.png`, `data/figures/local_deviation.png`

### Step 4: Hash Artifacts
Compute hashes and update project state:
```bash
python code/hash_artifacts.py
```
*Output*: Updates `state/projects/PROJ-729-...yaml` with artifact hashes.

### Step 5: Verify Citations & Generate Report
Verify citations and compile the final report:
```bash
python code/verify_citations.py
python code/report.py
```
*Output*: `paper/analysis_report.md`

## Verification

To verify the installation and data integrity:
```bash
pytest tests/
```
This runs unit tests for the gap calculation and integration tests for the full pipeline.

## Expected Output

- **Runtime**: ~15-20 seconds (generation) + 1-2 minutes (Bootstrap analysis) + < 1 second (hashing/reporting).
- **Memory Peak**: < 300 MB.
- **Key Result**: A JSON file containing the Bootstrap KS p-value and a list of two-sample KS p-values for the power-of-two windows.
