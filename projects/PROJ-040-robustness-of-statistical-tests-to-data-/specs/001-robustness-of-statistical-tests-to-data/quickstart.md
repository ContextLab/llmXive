# Quickstart: Robustness of Statistical Tests to Data Contamination

## Prerequisites

- Python 3.11+
- pip

## Installation

1. **Clone the repository** (if not already done).
2. **Navigate to the project directory**:
   ```bash
   cd projects/PROJ-040-robustness-of-statistical-tests-to-data-/
   ```
3. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Simulation

The simulation is executed in sequential steps.

### Step 0: Validate Citations (Blocking Gate)
Ensures all dataset URLs are verified before proceeding (Constitution Principle II).
```bash
python code/validation/validate_citations.py
```
*If this step fails, do not proceed. Fix the citation or update the verified datasets block.*

### Step 1: Download Datasets
Fetches the verified UCI datasets to `data/raw/`.
```bash
python code/data/download_datasets.py
```

### Step 2: Generate Checksums
Generates SHA256 hashes for raw data and updates `state/` manifest (Constitution Principle V).
```bash
python code/validation/checksum_artifacts.py
```

### Step 3: Generate Contaminated Data
Creates synthetic datasets with Gaussian and adversarial noise.
```bash
python code/data/generate_contamination.py
```
*Note: This script will generate files for a range of contamination rates and thresholds.*

### Step 4: Run Monte Carlo Simulation
Executes the simulation for all datasets and methods.
```bash
python code/data/run_simulation.py
```
*Output: `data/results/simulation_results.csv`*

### Step 5: Generate Checksums (Final)
Generates hashes for processed data and results, updating `state/` manifest.
```bash
python code/validation/checksum_artifacts.py
```

### Step 6: Generate Visualizations
Creates plots comparing error inflation and power loss.
```bash
python code/viz/plot_results.py
```
*Output: Plots saved in `data/results/figures/`*

## Verification

To verify the setup:
1. Run `python -m pytest tests/` to ensure unit tests pass.
2. Run the simulation on a single dataset with 10 iterations (set `--iterations 10` in `run_simulation.py`) to check for runtime errors.

## Troubleshooting

- **Memory Error**: If you encounter `MemoryError`, reduce the `--iterations` flag or ensure no other heavy processes are running.
- **Missing Dataset**: If `download_datasets.py` fails, verify your internet connection and the availability of the verified HuggingFace URLs.
- **Citation Validation Failed**: If `validate_citations.py` fails, check the `research.md` for unverified URLs or mismatched titles.