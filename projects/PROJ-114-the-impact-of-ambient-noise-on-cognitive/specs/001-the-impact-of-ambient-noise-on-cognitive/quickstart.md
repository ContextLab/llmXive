# Quickstart: The Impact of Ambient Noise on Cognitive Flexibility in Remote Workers

## Prerequisites

- Python 3.11+
- `pip` (Python package manager)
- Access to a GitHub Actions runner (for CI) or a local Linux/macOS environment.

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd projects/PROJ-114-the-impact-of-ambient-noise-on-cognitive
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
   *Note: `requirements.txt` pins versions for reproducibility (e.g., `statsmodels==0.14.1`, `pandas==2.2.0`).*

## Running the Pipeline

The pipeline is orchestrated by **Snakemake**.

1. **Download/Prepare Data**:
   If running locally, ensure `data/raw/mturk_scores.csv` is present. The pipeline will automatically generate synthetic noise logs if `data/raw/noise_logs.csv` is missing (for testing purposes).

2. **Execute the Workflow**:
   ```bash
   snakemake --cores 2 --rerun-incomplete
   ```
   This command:
   - Filters participants (FR-001).
   - Aggregates noise logs (FR-002).
   - Normalizes reaction times (FR-003).
   - Fits the LMM (FR-004).
   - Runs sensitivity analysis (FR-006).
   - Generates results in `data/results/`.

3. **View Results**:
   - Model summary: `data/results/model_summary.json`
   - Sensitivity sweep: `data/results/sensitivity_sweep.json`
   - Figures: `data/results/figures/`

## Testing

Run the test suite to verify contract compliance:

```bash
pytest tests/ -v
```

This validates:
- Data filtering logic (FR-001).
- Outlier removal (FR-003).
- Model convergence (SC-005).
- Schema validation against `contracts/`.

## Troubleshooting

- **Convergence Warnings**: If the model fails to converge, check `data/results/convergence_warnings.log`. The pipeline will flag this as a power limitation (SC-005).
- **Memory Errors**: The pipeline is designed for < 7 GB RAM. If errors occur, ensure no other heavy processes are running.
- **Missing Data**: Ensure `mturk_scores.csv` is in `data/raw/`. The pipeline expects this file to exist.
