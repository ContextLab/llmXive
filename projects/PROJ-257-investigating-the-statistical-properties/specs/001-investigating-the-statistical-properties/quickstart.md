# Quickstart: Statistical Properties of Simulated Black Hole Mergers

## Prerequisites

- Python 3.11+
- pip (Python package installer)
- Git (for cloning the repository)

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/your-repo.git
   cd your-repo
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
   *Note: `requirements.txt` pins versions of `pandas`, `numpy`, `scipy`, `matplotlib`, `requests`, `tqdm`, `pyyaml`.*

## Running the Pipeline

The pipeline is executed via the main script. It handles downloading (if URLs are available), generating synthetic data (if downloads fail), and running the full analysis.

```bash
python src/main.py
```

### Command Line Options (Optional)
- `--download-only`: Fetches data but skips analysis.
- `--generate-synth-only`: Skips download and generates only the synthetic catalog.
- `--alpha-sweep`: Explicitly enables the sensitivity analysis (default: True).

## Expected Outputs

After successful execution, the following artifacts will be generated:

1. **Data**:
   - `data/processed/obs_catalog.csv`: Preprocessed observational data.
   - `data/processed/sim_catalog.csv`: Synthetic simulation data.
   - `data/processed/selection_weights.csv`: Inverse probability weights.

2. **Results**:
   - `data/results/ks_results.json`: KS statistics, p-values, and Bonferroni corrections.
   - `data/results/power_analysis.json`: MDES and power limitation flags.
   - `data/results/sensitivity_report.json`: Alpha sweep results and borderline flags.

3. **Visualizations**:
   - `outputs/figures/mass_ratio_kde.png`: KDE plot for mass ratio.
   - `outputs/figures/effective_spin_kde.png`: KDE plot for effective spin.

## Troubleshooting

- **Download Failures**: If Zenodo URLs are unreachable, the pipeline will retry 3 times with exponential backoff. If it fails, it will automatically switch to synthetic data generation mode and log a warning.
- **Memory Errors**: The pipeline is designed for <7 GB RAM. If you encounter OOM errors, reduce the `samples_per_event` parameter in `src/data/preprocess.py`.
- **Missing Dependencies**: Ensure all packages in `requirements.txt` are installed in the active virtual environment.

## Verification

To verify the pipeline ran correctly:
1. Check `data/results/power_analysis.json` for the `power_limitation_flag`.
2. Inspect `outputs/figures/` for the presence of PNG files.
3. Run `pytest tests/` to ensure all unit and integration tests pass.