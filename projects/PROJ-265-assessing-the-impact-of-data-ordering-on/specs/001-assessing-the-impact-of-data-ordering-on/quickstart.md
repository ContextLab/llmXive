# Quickstart: Assessing the Impact of Data Ordering on Bootstrapping Results

## Prerequisites

- Python 3.11+
- Git
- Access to a GitHub Actions runner (or local machine with sufficient RAM)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-265-assessing-the-impact-of-data-ordering-on
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Simulation

### 1. Synthetic Data Only (Recommended for CI)
Run the full synthetic simulation (User Stories 1 & 2):
```bash
python code/main.py --mode synthetic
```
- Generates AR data for $\phi \in [0.0, 0.9]$.
- Runs [deferred] trials per $\phi$.
- Outputs `results/coverage_metrics.csv`.

### 2. Full Pipeline (Synthetic + Real)
Attempt to run synthetic and real-world analysis (User Story 3):
```bash
python code/main.py --mode full
```
- **Note**: If the UCI dataset is not found locally or via a verified loader, the real-world step will be skipped, and a warning will be logged.

### 3. Generate Plots
```bash
python code/plots.py --input results/coverage_metrics.csv --output results/figures/
```

## Verification

1. **Check Output**:
   Ensure `results/coverage_metrics.csv` exists and contains rows for all $\phi$ levels.
2. **Check Coverage**:
   Verify that coverage for $\phi=0.0$ is $\approx 0.95$ and decreases as $\phi$ increases.
3. **Check Significance**:
   Verify that McNemar's test p-values are $< 0.05$ for $\phi > 0.3$.

## Troubleshooting

- **Missing UCI Data**: If the script fails to load the UCI dataset, check the `data/raw/` directory. If the file is missing, the script will skip the real-world step.
- **Memory Error**: Ensure you have at least 4GB of free RAM. The default simulation is lightweight, but large datasets can cause issues.
- **Import Error**: Ensure all dependencies in `requirements.txt` are installed.