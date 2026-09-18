# Usage Examples

## Quick Start

### 1. Project Setup

```bash
# Clone and setup
git clone <repository-url>
cd PROJ-026-the-influence-of-visual-complexity-on-im

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r code/requirements.txt
```

### 2. Running the Full Pipeline

```bash
# Production mode (requires real data)
python code/main.py

# CI/Test mode (synthetic data)
python code/main.py --null-effect
```

## Detailed Examples

### Stimulus Complexity Quantification (User Story 1)

#### Step 1: Validate Input Images

```python
from stimuli.validate import validate_batch, get_valid_images, get_invalid_images

# Validate all images in a directory
valid_images, invalid_images = validate_batch("data/raw/stimuli/")

print(f"Valid: {len(valid_images)}, Invalid: {len(invalid_images)}")
```

#### Step 2: Compute Complexity Metrics

```python
from stimuli.process import process_stimuli_batch

# Process all stimuli and save raw scores
process_stimuli_batch(
 input_dir="data/raw/stimuli/",
 output_path="data/processed/complexity_scores_raw.csv"
)
```

#### Step 3: Categorize Complexity

```python
import pandas as pd
from stimuli.process import categorize_complexity

# Load raw scores and categorize
df = pd.read_csv("data/processed/complexity_scores_raw.csv")
categorized_df = categorize_complexity(df)

# Save final CSV
categorized_df.to_csv("data/processed/complexity_scores.csv", index=False)

# View distribution
print(categorized_df['complexity_category'].value_counts())
```

### Experimental Data Aggregation (User Story 2)

#### Step 1: Load Response Logs

```python
from data.load import load_response_logs

# Load real data
response_logs = load_response_logs("data/raw/responses/")

# Or generate synthetic data for testing
from data.load import generate_synthetic_response_logs
synthetic_logs = generate_synthetic_response_logs(n_participants=50)
```

#### Step 2: Filter and Aggregate

```python
from data.process import aggregate_d_scores

# Aggregate D-scores per participant
aggregated = aggregate_d_scores(response_logs)

# Save results
aggregated.to_csv("data/processed/aggregated_d_scores.csv", index=False)
```

#### Step 3: Generate Counterbalance Assignments

```python
from data.counterbalance import generate_counterbalance_assignments

# Generate session order assignments
assignments = generate_counterbalance_assignments(
 n_participants=100,
 split_ratio=0.5,
 seed=42
)

# Save assignments
assignments.to_csv("data/processed/counterbalance_assignment.csv", index=False)
```

### Statistical Analysis (User Story 3)

#### Step 1: PCA Validation

```python
from analysis.pca import run_pca_check

# Load complexity metrics
import pandas as pd
df = pd.read_csv("data/processed/complexity_scores.csv")

# Run PCA check
results = run_pca_check(df[['edge_density', 'entropy', 'fractal_dim']])

# Check cumulative variance
print(f"Cumulative variance: {results['cumulative_variance']:.4f}")
assert results['cumulative_variance'] > 0.8, "PCA validation failed"
```

#### Step 2: Permutation Test

```python
from analysis.permutation import run_permutation_test, calculate_effect_size

# Load aggregated D-scores
d_scores = pd.read_csv("data/processed/aggregated_d_scores.csv")

# Split by complexity condition
low_group = d_scores[d_scores['complexity_condition'] == 'Low']['d_score']
high_group = d_scores[d_scores['complexity_condition'] == 'High']['d_score']

# Run permutation test
p_value, observed_diff = run_permutation_test(
 low_group.values,
 high_group.values,
 n_permutations=1000,
 seed=42
)

# Calculate effect size
cohen_d = calculate_effect_size(low_group.values, high_group.values)

print(f"P-value: {p_value:.4f}, Cohen's d: {cohen_d:.4f}")
```

#### Step 3: Power Analysis

```python
from analysis.permutation import run_post_hoc_power_analysis
import json

# Load permutation results
with open("data/results/permutation_results.json", "r") as f:
 results = json.load(f)

# Run power analysis
power_results = run_post_hoc_power_analysis(
 eta2=results['partial_eta2'],
 n=len(d_scores),
 alpha=0.05,
 target=0.80
)

# Save results
with open("data/results/power_analysis.json", "w") as f:
 json.dump(power_results, f, indent=2)
```

#### Step 4: Sensitivity Analysis

```python
from analysis.permutation import run_sensitivity_analysis, run_loio_analysis

# Threshold sweep
sensitivity_results = run_sensitivity_analysis(
 d_scores,
 metric_std=1.0, # Standard deviation of complexity metric
 n_permutations=1000
)

# LOIO analysis
loio_results = run_loio_analysis(
 d_scores,
 n_permutations=1000
)

# Combine and save
combined = {
 "threshold_sweep": sensitivity_results,
 "loio_results": loio_results
}

with open("data/results/sensitivity_results.json", "w") as f:
 json.dump(combined, f, indent=2)
```

### Visualization

#### Generate Publication-Quality Plot

```python
from viz.plot import plot_boxplot

# Load aggregated data
d_scores = pd.read_csv("data/processed/aggregated_d_scores.csv")

# Generate boxplot
plot_boxplot(
 df=d_scores,
 x_col='complexity_condition',
 y_col='d_score',
 output_path="data/results/d_score_comparison.png",
 dpi=300,
 confidence_level=0.95
)
```

#### Plot Sensitivity Analysis

```python
from viz.plot import plot_sensitivity, plot_loio_sensitivity
import json

# Load sensitivity results
with open("data/results/sensitivity_results.json", "r") as f:
 sensitivity_data = json.load(f)

# Plot threshold sweep
plot_sensitivity(
 sensitivity_data['threshold_sweep'],
 output_path="data/results/sensitivity_sweep.png"
)

# Plot LOIO results
plot_loio_sensitivity(
 sensitivity_data['loio_results'],
 output_path="data/results/loio_sensitivity.png"
)
```

## Configuration

### Environment Variables

The pipeline uses `code/config.py` for all path and constant management:

```python
from config import get_project_root, ensure_directories, get_data_path

# Get project root
root = get_project_root()

# Ensure all directories exist
ensure_directories()

# Get specific data path
stimuli_path = get_data_path("raw/stimuli/")
```

### Logging Configuration

```python
from utils.logging import setup_logging, get_logger, log_counterbalance_strategy

# Setup logging
setup_logging("logs/app.log")
logger = get_logger(__name__)

# Log counterbalance strategy
log_counterbalance_strategy(seed=42, split_ratio=0.5)
```

## Error Handling

### Data Loading Failures

The data loader raises `RuntimeError` when real data is missing in production mode:

```python
from data.load import load_response_logs

try:
 logs = load_response_logs("data/raw/responses/")
except RuntimeError as e:
 print(f"Data loading failed: {e}")
 # Handle missing data appropriately
```

### Metric Calculation Errors

Invalid images are skipped and logged:

```python
from stimuli.validate import validate_batch

valid, invalid = validate_batch("data/raw/stimuli/")
if invalid:
 print(f"Skipped {len(invalid)} corrupted images")
```

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test module
pytest tests/test_stimuli/test_metrics.py

# Run with coverage
pytest tests/ --cov=code --cov-report=html
```

### Test Examples

```python
# Example: Test edge density calculation
def test_edge_density_solid_color():
 from stimuli.metrics import calculate_edge_density
 import numpy as np
 from PIL import Image

 # Solid color image (should have 0 edge density)
 img = Image.new('RGB', (100, 100), color='red')
 density = calculate_edge_density(np.array(img))
 assert density == 0.0
```

## Troubleshooting

### Common Issues

1. **Missing Data Files**: Ensure `data/raw/stimuli/` and `data/raw/responses/` contain valid files
2. **Memory Errors**: The pipeline is optimized for CPU-only runners; reduce batch size if needed
3. **Import Errors**: Verify virtual environment is activated and all dependencies are installed

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

## Performance

### Memory Limits

The pipeline is designed to run within 7GB RAM limits:

```bash
# Profile memory usage
python code/utils/profile_memory.py
```

### Execution Time

Full pipeline typically completes in under 6 hours on CPU-only runners.