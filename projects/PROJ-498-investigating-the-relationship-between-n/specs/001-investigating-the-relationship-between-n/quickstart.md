# Quickstart: Investigating the Relationship Between Neural Synchrony and Attention Switching Costs

## Prerequisites

- Python 3.11+
- 7GB+ RAM
- GB+ Disk Space
- Internet access (for dataset download)

## Installation

1. **Clone the repository** (or navigate to the project directory).
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `requirements.txt` pins versions for `mne`, `scipy`, `statsmodels`, etc.*

## Running the Pipeline

The pipeline is executed via `code/main.py`. It performs the following steps sequentially:

1. **Data Validation**: Checks if `ds004173` is available and valid.
2. **Download**: Fetches data (if not present).
3. **Preprocessing**: Filters, ICA, epochs.
4. **Synchrony Calculation**: Computes wPLI/PLV.
5. **Behavioral Analysis**: Computes switching costs.
6. **Statistical Testing**: Permutation tests and Bayesian Hierarchical Model.
7. **Sensitivity Analysis**: Re-runs with shifted windows.
8. **Output**: Generates reports and plots.

### Command

```bash
python code/main.py --dataset ds004173 --output data/results
```

*Note: If `ds004173` is not available or fails schema validation, the script will halt with an error. Refer to `research.md` for dataset constraints.*

### Configuration

Edit `code/config.py` to modify:
- `BANDPASS_LOW`, `BANDPASS_HIGH`: Filter settings.
- `EPOCH_TMIN`, `EPOCH_TMAX`: Epoch window.
- `N_PERMUTATIONS`: Number of permutations (default 1000).
- `RANDOM_SEED`: For reproducibility.

## Verification

To verify the installation and pipeline:

1. **Run Unit Tests**:
   ```bash
   pytest tests/unit/
   ```
   *Tests synthetic signals for correct wPLI calculation.*

2. **Run Integration Test (Single Subject)**:
   ```bash
   python code/main.py --dataset ds004173 --subject sub-01 --quick
   ```
   *Processes only one subject to verify memory usage and pipeline flow.*

## Expected Outputs

- `data/processed/`: Cleaned epochs.
- `data/metrics/`: Synchrony and behavioral CSVs.
- `data/results/`: Correlation JSON, sensitivity report, and plots.
- `data/exclusions.csv`: List of excluded subjects.

## Troubleshooting

- **OOM Error**: Ensure `code/main.py` processes subjects sequentially and deletes raw data after epoching.
- **Dataset Missing**: If the dataset is not found, check `research.md` for verified sources. The pipeline will not fabricate data. It will halt with a clear error message.
- **ICA Failure**: If >50% of data is removed, the subject is excluded and logged.
- **Script Missing**: Ensure `code/update_state_hashes.py` is present. If not, run the setup script to generate it.
