# The Influence of Visual Complexity on Implicit Bias

**Project ID**: PROJ-026
**Description**: Automated research pipeline investigating the relationship between visual complexity metrics (edge density, entropy, fractal dimension) and implicit bias scores (IAT D-scores).

## Installation

### Prerequisites
- Python 3.11+
- pip

### Setup
1. Clone the repository and navigate to the project root.
2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Usage

### Running the Full Pipeline
Execute the main orchestration script:
```bash
python code/main.py
```

### CI / Null-Effect Mode
To run the pipeline with synthetic data for Continuous Integration (CI) purposes:
```bash
python code/main.py --null-effect
```
*Note: This flag bypasses real data loading and generates synthetic response logs. In production, omit this flag to load real data from `data/raw/responses/`.*

### Individual Modules
- **Stimuli Processing**: `python code/stimuli/process.py`
- **Data Aggregation**: `python code/data/process.py`
- **Statistical Analysis**: `python code/analysis/permutation.py`
- **Visualization**: `python code/viz/plot.py`

## Data Format

### Input Data
- **Stimuli**: Images placed in `data/raw/stimuli/`. Supported formats: `.png`, `.jpg`.
- **Responses**: CSV logs in `data/raw/responses/` containing columns: `participant_id`, `session_id`, `stimulus_file`, `response_time`, `is_correct`.

### Output Data
- **Processed Metrics**: `data/processed/complexity_scores.csv` (Image metrics + Low/High category).
- **Aggregated Scores**: `data/processed/aggregated_d_scores.csv` (Participant D-scores joined with complexity conditions).
- **Results**:
 - `data/results/permutation_results.json`: Statistical significance (p-value) and effect size.
 - `data/results/sensitivity_results.json`: Threshold sweep and Leave-One-Image-Out (LOIO) analysis.
 - `data/results/d_score_comparison.png`: Publication-quality boxplot.

## API Reference

### `code/stimuli/metrics.py`
- `calculate_edge_density(image)`: Computes Canny edge density.
- `calculate_entropy(image)`: Computes grayscale histogram entropy.
- `calculate_fractal_dim(image)`: Computes fractal dimension via box-counting.

### `code/data/process.py`
- `filter_trials(df)`: Removes trials outside 300ms-10000ms bounds.
- `calculate_d_score(trials)`: Implements Greenwald D2 algorithm.

### `code/analysis/permutation.py`
- `run_permutation_test(d_scores, condition, n_permutations=1000)`: Performs non-parametric significance testing.
- `calculate_effect_size(observed, null_dist)`: Computes Cohen's d from permutation distribution.

### `code/viz/plot.py`
- `plot_boxplot(data, output_path)`: Generates Seaborn boxplot with 95% CI.

## License
Research code for internal academic use.
