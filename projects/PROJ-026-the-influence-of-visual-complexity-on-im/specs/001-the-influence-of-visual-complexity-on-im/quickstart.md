# Quickstart: The Influence of Visual Complexity on Implicit Bias

## Prerequisites

- Python 3.11 or higher
- Git
- (Optional) Docker (for isolated execution)

## Installation

1. **Clone the repository** and navigate to the project directory:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-026-the-influence-of-visual-complexity-on-im
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

## Data Preparation

### Option A: Synthetic Data (Recommended for CI)
The project includes a script to generate synthetic IAT data and complexity metrics for testing.
```bash
# Generate data with NO effect (for pipeline validation)
python code/data/load.py --generate-synthetic --seed 42 --n-participants 60 --null-effect

# Generate data with HYPOTHESIZED effect (for detection logic testing only)
python code/data/load.py --generate-synthetic --seed 42 --n-participants 60
```
This will create:
- `data/raw/stimuli/`: 50 synthetic grayscale images (dummy file paths).
- `data/raw/responses/`: Synthetic IAT trial logs.
- `data/processed/complexity_scores.csv`: Computed metrics.
- `data/processed/aggregated_d_scores.csv`: Aggregated D-scores.

### Option B: Real Data
If you have collected real data:
1. Place raw images in `data/raw/stimuli/`.
2. Place raw IAT logs (CSV/JSON) in `data/raw/responses/`.
3. Run the processing pipeline:
   ```bash
   python code/main.py --process-stimuli --aggregate-responses
   ```

## Running the Analysis

Execute the full analysis pipeline (Permutation Test + Sensitivity + Plotting):
```bash
python code/main.py --run-analysis
```

This will:
1. Compute visual complexity metrics (if not already done).
2. Perform PCA dimensionality check.
3. Run Permutation Test (and LOIO sensitivity analysis).
4. Generate publication-quality plots in `data/results/plots/`.
5. Save results to `data/results/`.

## Verification

Run the test suite to ensure correctness:
```bash
pytest code/tests/ -v
```

### Expected Outputs
- `data/results/permutation_results.json`: Main statistical results.
- `data/results/sensitivity_results.json`: Robustness analysis (Threshold + LOIO).
- `data/results/plots/d_score_comparison.png`: Visualization of D-scores.
- `data/results/plots/sensitivity_sweep.png`: Sensitivity analysis plot.

## Troubleshooting

- **Memory Errors**: Ensure the dataset is not too large. The pipeline is designed for a moderate cohort of participants. If using real data, sample if necessary.
- **Image Loading Errors**: The pipeline will skip corrupted images and log them to `logs/stimuli_validation.log`.
- **Statistical Errors**: If `n < 15` in any condition, the sensitivity point is marked invalid. Check the `sensitivity_results.json` for details.
- **PCA Variance**: If PC1 variance < 70%, the pipeline automatically switches to Multivariate Permutation Test.

