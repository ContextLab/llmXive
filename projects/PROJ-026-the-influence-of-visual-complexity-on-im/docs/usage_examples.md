# Usage Examples

This document provides practical examples for using the `llmXive` research pipeline.

## 1. Running with Real Data

Ensure your raw data is placed in the correct directories:

- **Stimuli**: `data/raw/stimuli/` (Place image files here)
- **Responses**: `data/raw/responses/` (Place raw log files here)

Run the pipeline:

```bash
cd code
python main.py
```

## 2. Running in Synthetic Mode (CI/Testing)

For continuous integration or testing without real data, use the `--null-effect` flag. This generates synthetic data consistent with a null hypothesis scenario.

```bash
cd code
python main.py --null-effect
```

This will:
- Generate synthetic participant IDs and session orders.
- Create dummy complexity scores and D-scores.
- Run the permutation test on synthetic data.
- Output results to `data/results/`.

## 3. Customizing the Random Seed

To ensure reproducibility across runs, set a specific seed:

```bash
cd code
python main.py --seed 12345
```

## 4. Running Individual Analysis Steps

You can run specific parts of the pipeline independently if you have intermediate data ready.

### Step A: Compute Complexity Metrics
```bash
python -m stimuli.process
```
*Input*: `data/raw/stimuli/`
*Output*: `data/processed/complexity_scores.csv`

### Step B: Aggregate D-Scores
```bash
python -m data.process
```
*Input*: `data/raw/responses/`
*Output*: `data/processed/aggregated_d_scores.csv`

### Step C: Statistical Analysis
```bash
python -m analysis.permutation
```
*Input*: `data/processed/aggregated_d_scores.csv` (and complexity scores)
*Output*: `data/results/permutation_results.json`

## 5. Visualizing Results

The `main.py` script automatically generates plots. To manually inspect the logic or generate specific plots:

```python
from viz.plot import plot_boxplot, plot_sensitivity
import pandas as pd

# Load results
results = pd.read_csv("data/processed/aggregated_d_scores.csv")
complexity = pd.read_csv("data/processed/complexity_scores.csv")

# Generate boxplot
plot_boxplot(results, complexity, "data/results/boxplot.png")
```

## 6. Troubleshooting

- **OpenCV Errors**: Ensure system libraries for `opencv-python-headless` are installed (e.g., `sudo apt-get install libgl1-mesa-glx`).
- **Missing Data**: The pipeline expects specific directory structures. Run `python setup_project.py` (if available) or manually create directories in `data/raw/stimuli`, `data/raw/responses`, etc.
- **Statistical Warnings**: If sample sizes are small (<15 per condition), the sensitivity analysis may skip those points. Check `data/results/sensitivity_results.json` for details.
