# Quickstart: Evaluating the Impact of Data Scaling on Robustness of Statistical Tests

## Prerequisites

- Python 3.11+
- Git
- (Optional) Virtual environment manager (`venv` or `conda`)

## Installation

1. **Clone the Repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-541-evaluating-the-impact-of-data-scaling-on
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Simulation

### 1. Run the Full Pipeline
Execute the main orchestration script to run simulations, scaling, testing, and aggregation.
```bash
python code/main.py --mode simulation
```
*This will generate synthetic data, apply scaling, run tests, and save results to `results/`.*

### 2. Run Real-World Validation
Download verified datasets and run the pipeline on them.
```bash
python code/main.py --mode real_world
```
*Note: This requires internet access to download datasets from the verified URLs.*

### 3. Run Specific Tests
You can run a subset of configurations for debugging:
```bash
python code/main.py --mode simulation --config-id "test-config-1" --iterations 100
```

## Generating Reports

### 1. Visualizations
Generate the error rate plots and comparison charts.
```bash
python code/main.py --mode visualize
```
*Outputs are saved to `results/figures/`.*

### 2. Mixed-Effects Analysis
Run the statistical model to test scaling method impact.
```bash
python code/main.py --mode analyze
```

## Verification

### Check Data Integrity
Verify checksums of downloaded datasets.
```bash
python code/main.py --mode verify-checksums
```

### Run Unit Tests
Ensure the simulation engine and scaling functions work correctly.
```bash
pytest tests/unit/
```

## Troubleshooting

- **Runtime Error**: If the process exceeds 6 hours, check the `results/partial_results.csv` for partial data.
- **Missing Data**: If a dataset fails to load, check `results/real_world_results.csv` for the `skipped_reason`.
- **Zero Variance**: The system automatically skips iterations with zero variance and logs a warning.
