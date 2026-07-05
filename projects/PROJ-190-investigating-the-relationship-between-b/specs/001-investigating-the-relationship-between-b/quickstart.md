# Quickstart: Brain Network Efficiency and Fluid Intelligence

## Prerequisites

- Python 3.11+
- HCP Data Access (credentials for `https://db.humanconnectome.org/` or a local copy of the 1200-subject release).
- Schaefer Atlas files (downloaded from the Yeo Lab GitHub).
- **CI Note**: For automated CI runs, a `--mock-data` flag is available to generate synthetic data matching the HCP schema.

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-190-investigating-the-relationship-between-b
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Download Data** (Manual step for HCP):
   - Log in to the HCP database.
   - Download the `1200_Subjects` release.
   - Place the data in `data/raw/`.
   - *Note: For CI, a pre-downloaded subset or mock data is used.*

## Running the Pipeline

The pipeline is orchestrated via `code/main.py`.

### Full Run (or Sampled)
```bash
python code/main.py --config config/default.yaml
```

### Mock Run (CI Testing)
```bash
python code/main.py --config config/default.yaml --mock-data
```

### Steps Executed:
1. **Download/Load**: Loads fMRI and behavioral data (or generates mock data).
2. **Preprocess**: Applies nuisance regression and band-pass filtering. Calculates FD.
3. **Graph Construction**: Parcellates with Schaefer 200/400, computes matrices, thresholds.
4. **Metric Calculation**: Computes global and frontoparietal efficiency (Harmonic Mean for disconnected graphs).
5. **Statistics**: Runs correlations, regression, VIF check, and permutation testing (with a sufficient number of permutations).
6. **Report**: Generates `results/statistical_summary.json` and figures.

### Verification
Check the output log for:
- `Subjects processed: X`
- `Mean FD: Y mm`
- `Global Efficiency (200): Z`
- `FWE Corrected p-value: P`

If the 6-hour limit is approached, the system will automatically sample to ≤200 subjects and log this event.

## Troubleshooting

- **HCP Access Error**: Ensure credentials are set in environment variables or the HCP CLI is configured. Use `--mock-data` for CI testing.
- **Memory Error**: The script uses memory mapping. If issues persist, reduce `--max-subjects` manually.
- **Permutation Timeout**: If 1,000 permutations exceed time, the system will log a warning and reduce subjects (fallback to N=200).