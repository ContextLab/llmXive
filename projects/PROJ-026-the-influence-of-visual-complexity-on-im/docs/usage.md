# Usage Examples: The Influence of Visual Complexity on Implicit Bias

This guide provides detailed examples for interacting with the pipeline components.

## 1. Stimulus Complexity Quantification

Before running the experiment, ensure your images are in `data/raw/stimuli/`.
The system will automatically:
1. Validate images (corruption check).
2. Compute metrics (Edge Density, Entropy, Fractal Dimension).
3. Categorize into 'Low' and 'High' complexity groups via Median Split.

**Manual Execution**:
```bash
python code/stimuli/process.py
```
*Output*: `data/processed/complexity_scores.csv`

## 2. Data Loading and Processing

The pipeline expects response logs in `data/raw/responses/`.
If you are running the full analysis on real data, ensure these files exist.
If running in CI mode, use the `--null-effect` flag to generate synthetic data.

**Processing Flow**:
1. **Filtering**: Removes invalid trials (<300ms, >10s).
2. **Aggregation**: Calculates D-scores per session.
3. **Counterbalancing**: Joins with `data/processed/counterbalance_assignment.csv` to map stimulus sets to complexity conditions.

**Manual Execution**:
```bash
python code/data/process.py
```
*Output*: `data/processed/aggregated_d_scores.csv`

## 3. Statistical Analysis (Permutation Test)

The core analysis replaces ANOVA with a Permutation Test (n=1000) to handle stimulus confounds.

**Steps**:
1. **Permutation Test**: Computes p-value for the difference in D-scores between Low and High complexity.
2. **Effect Size**: Calculates Cohen's d derived from the permutation distribution.
3. **Sensitivity Analysis**:
 - **Threshold Sweep**: Varies the median split threshold by ±SD steps.
 - **LOIO**: Excludes one image at a time to test robustness.

**Manual Execution**:
```bash
python code/analysis/permutation.py
```
*Output*: `data/results/permutation_results.json`, `data/results/sensitivity_results.json`

## 4. Visualization

Generates publication-ready plots using Seaborn.

**Output**:
- `data/results/d_score_comparison.png`: Boxplot of D-scores by complexity condition.

**Manual Execution**:
```bash
python code/viz/plot.py
```

## 5. Full Pipeline Orchestration

To run the entire workflow from raw data to final plots:

```bash
python code/main.py
```

**Arguments**:
- `--null-effect`: Use synthetic data for testing/CI (default: False).

## Troubleshooting

### "RuntimeError: Real data missing"
If you run without `--null-effect` and no data exists in `data/raw/responses/`, the loader will fail.
**Fix**: Populate `data/raw/responses/` with valid CSV logs or use `--null-effect` for synthetic testing.

### "ValueError: Insufficient trials"
Participants with fewer than 10 valid trials are excluded. Check `logs/exclusion_report.log` for details.

### "PCA Warning"
If `data/results/pca_variance.json` shows "Low variance", the complexity metrics may not be capturing a single underlying construct. Review `data/processed/complexity_metrics_raw.csv`.
