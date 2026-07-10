# Quickstart: Investigating the Validity of the Equipartition Theorem in Driven Granular Systems

## Prerequisites

- Python 3.11+
- Git
- Access to GitHub Actions (for CI) or a local environment with ≤7 GB RAM.

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-177-investigating-the-validity-of-the-equipa
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

## Data Preparation

Since no verified source for real granular data exists, you must generate synthetic data for testing.

1. **Generate synthetic data**:
   ```bash
   python code/data/synthetic.py --frames 100000 --output data/raw/synthetic_granular.csv
   ```
   *Note: This script creates a CSV with positions, orientations, and metadata matching the `ParticleFrame` schema. It includes a friction coefficient to generate realistic deviations from equipartition.*

2. **(Optional) Use real data**:
   If you obtain a verified CSV/Parquet file, place it in `data/raw/` and ensure it has columns: `particle_id`, `timestamp`, `x`, `y`, `z`, `theta`, `material_type`, `driving_frequency`.

## Running the Pipeline

1. **Execute the full analysis**:
   ```bash
   python code/main.py --input data/raw/synthetic_granular.csv --output data/results/analysis_results.json
   ```
   *Note: The pipeline processes data in chunks (100k frames) to ensure memory safety.*

2. **Run unit tests**:
   ```bash
   pytest tests/unit/
   ```

3. **Run integration tests**:
   ```bash
   pytest tests/integration/
   ```

## Expected Outputs

- `data/results/analysis_results.json`: Contains `EnergyBin` and `StatisticalResult` objects.
- `data/results/sensitivity_summary.csv`: Table of significant counts for $\alpha \in \{0.01, 0.05, 0.10\}$.
- Console output: Summary of paired t-test p-values, KS test results, and regression coefficients.

## Troubleshooting

- **OOM Error**: The pipeline should automatically chunk data. If OOM occurs, reduce the `--frames` argument in the synthetic generator.
- **Missing Mass**: Check if `material_type` is present in the input CSV. If not, the pipeline will fail as per FR-006.
- **0Hz Frequency**: The pipeline will automatically exclude 0Hz bins from the ratio test.