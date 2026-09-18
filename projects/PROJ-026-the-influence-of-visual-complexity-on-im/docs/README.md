# The Influence of Visual Complexity on Implicit Bias

## Overview

This project implements a research pipeline to investigate the influence of visual complexity on implicit bias. The pipeline quantifies visual complexity metrics (edge density, entropy, fractal dimension) for background images, aggregates experimental response data into D-scores, and performs statistical analysis using Permutation Tests with sensitivity analyses.

## Installation

### Prerequisites

- Python 3.11 or higher
- pip package manager

### Setup

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd PROJ-026-the-influence-of-visual-complexity-on-im
 ```

2. Create a virtual environment (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Usage

### Running the Full Pipeline

The main entry point orchestrates the entire research pipeline:

```bash
python code/main.py
```

### Command Line Options

- `--null-effect`: Generate synthetic data for CI/testing (default: False)
- `--split-ratio`: Ratio of participants starting with Low vs High complexity (default: 0.5)

Example with options:
```bash
python code/main.py --null-effect --split-ratio 0.6
```

### Running Individual Components

#### Stimulus Processing
```bash
python code/stimuli/process.py
```

#### Data Aggregation
```bash
python code/data/process.py
```

#### Statistical Analysis
```bash
python code/analysis/permutation.py
```

#### Visualization
```bash
python code/viz/plot.py
```

## Data Format

### Directory Structure

```
data/
├── raw/
│ ├── stimuli/ # Input background images
│ └── responses/ # Raw experimental response logs
├── processed/
│ ├── complexity_scores.csv # Quantified complexity metrics
│ ├── complexity_scores_raw.csv # Raw metrics before categorization
│ ├── counterbalance_assignment.csv # Session order assignments
│ └── aggregated_d_scores.csv # Aggregated D-scores per participant
└── results/
 ├── pca_variance.json # PCA cumulative variance
 ├── permutation_results.json # Permutation test results
 ├── sensitivity_results.json # Sensitivity analysis results
 ├── power_analysis.json # Post-hoc power analysis
 └── d_score_comparison.png # Publication-quality plot
```

### CSV Schemas

#### complexity_scores.csv
- `filename`: Image file name
- `edge_density`: Canny edge density metric
- `entropy`: Grayscale histogram entropy
- `fractal_dim`: Box-counting fractal dimension
- `complexity_category`: Low/Medium/High (based on tertiles)
- `session_id`: Session identifier
- `participant_id`: Participant identifier
- `status`: 'valid' or 'skipped'

#### aggregated_d_scores.csv
- `participant_id`: Participant identifier
- `session_id`: Session identifier
- `complexity_condition`: Low/Medium/High
- `d_score`: Greenwald D2 score
- `n_trials_valid`: Number of valid trials
- `status`: 'valid' or 'NaN' (if <10 valid trials)

### JSON Output Formats

#### permutation_results.json
```json
{
 "p_value": 0.045,
 "effect_size": 0.67,
 "partial_eta2": 0.032,
 "observed_cohen_d": 0.58
}
```

#### sensitivity_results.json
```json
{
 "threshold_sweep": [...],
 "loio_results": [...]
}
```

## API Reference

### Stimuli Module

#### `code/stimuli/metrics.py`
- `calculate_edge_density(image)`: Compute Canny edge density
- `calculate_entropy(image)`: Compute grayscale histogram entropy
- `calculate_fractal_dim(image)`: Compute box-counting fractal dimension

#### `code/stimuli/process.py`
- `process_stimuli_batch(input_dir, output_path)`: Process all images in directory
- `categorize_complexity(df)`: Assign Low/Medium/High categories based on tertiles

### Data Module

#### `code/data/process.py`
- `filter_trials(trials)`: Remove invalid trials (<300ms, >10000ms, errors)
- `calculate_d_score(trials)`: Compute Greenwald D2 score
- `aggregate_d_scores(raw_logs)`: Aggregate per-participant D-scores

#### `code/data/load.py`
- `load_response_logs(path)`: Load raw response logs
- `generate_synthetic_response_logs(n_participants)`: Generate synthetic data for testing

### Analysis Module

#### `code/analysis/permutation.py`
- `run_permutation_test(d_scores, n_permutations=1000, seed=42)`: Run permutation test
- `calculate_effect_size(group1, group2)`: Compute Cohen's d
- `run_post_hoc_power_analysis(eta2, n, alpha=0.05, target=0.80)`: Power analysis
- `run_sensitivity_analysis(df, metric_std)`: Threshold sweep analysis
- `run_loio_analysis(df)`: Leave-One-Image-Out analysis

#### `code/analysis/pca.py`
- `run_pca_check(complexity_metrics)`: Validate metric construct via PCA

### Visualization Module

#### `code/viz/plot.py`
- `plot_boxplot(df, output_path)`: Generate publication-quality boxplot
- `plot_sensitivity(results, output_path)`: Plot sensitivity analysis
- `plot_loio_sensitivity(results, output_path)`: Plot LOIO results

### Configuration

#### `code/config.py`
- `get_project_root()`: Return project root path
- `ensure_directories()`: Create required directories
- `get_data_path(subpath)`: Get full path to data file

### Logging

#### `code/utils/logging.py`
- `setup_logging(log_file)`: Configure logging infrastructure
- `get_logger(name)`: Get named logger instance
- `log_counterbalance_strategy(seed, split_ratio)`: Log counterbalancing strategy

## Methodology Notes

- **Permutation Test**: Replaces repeated-measures ANOVA (FR-003) to handle stimulus-set confounds
- **Complexity Metrics**: Three orthogonal measures (edge density, entropy, fractal dimension)
- **D-Score**: Greenwald D2 algorithm for IAT effect size
- **Sensitivity Analysis**: Threshold sweep (±0.05, ±0.10, ±0.15 SD) and LOIO

## License

This project is licensed under the MIT License.
