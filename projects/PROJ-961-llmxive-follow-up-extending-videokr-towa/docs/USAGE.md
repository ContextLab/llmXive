# Usage Guide: VideoKR Reasoning Cliff Analysis

This guide details how to run the analysis pipeline, interpret outputs, and troubleshoot common issues.

## Quick Start

The entire pipeline can be run sequentially. Ensure you have sufficient disk space (approx. 2GB for raw data + processed artifacts).

```bash
# 1. Ingest and Annotate
python code/ingest/annotate_graph.py

# 2. Stratify Accuracy
python code/analysis/stratify_accuracy.py

# 3. Detect Threshold
python code/analysis/detect_threshold.py

# 4. Fit GAM
python code/analysis/fit_gam.py

# 5. Sensitivity Analysis
python code/analysis/sensitivity.py

# 6. Generate Plots
python code/analysis/generate_plots.py
python code/analysis/plot_sensitivity_overlay.py
```

## Detailed Script Reference

### `code/ingest/annotate_graph.py`

**Purpose**: Downloads VideoKR-SFT and the Knowledge Graph, then annotates each question with its shortest path chain length.

**Key Features**:
- **Two-Stage Sampling**: Implements a pilot (1000 records) followed by oversampling to ensure at least 50 records per hop bin.
- **Entity Linking**: Uses fuzzy matching to map question entities to graph nodes.
- **Disconnected Graphs**: Records with no path are labeled "unresolvable" and excluded from statistical tests.

**Outputs**:
- `data/processed/annotated_videokr.csv`: Full dataset with `chain_length` and `correctness` columns.
- `data/processed/sampling_log.json`: Log of the sampling strategy execution.

### `code/analysis/detect_threshold.py`

**Purpose**: Performs grid-search change-point detection using a Permutation Test.

**Key Features**:
- **Bonferroni Correction**: Adjusts p-values for multiple comparisons across potential knot locations.
- **Small Bin Handling**: Automatically merges 3+ hop bins if sample size < 50, or defers the test with a logged reason.

**Outputs**:
- `data/processed/threshold_results.json`: Contains `p_value`, `effect_size`, `optimal_knot`, and `bin_status`.

### `code/analysis/fit_gam.py`

**Purpose**: Fits a Generalized Additive Model to test for non-linearity in the continuous domain.

**Warning**: GAMs are typically invalid for low-cardinality discrete ordinal variables. This implementation is required by Spec FR-007; interpret results with extreme caution.

**Outputs**:
- `data/processed/gam_results.json`: Contains `p_value_non_linearity` and smoothness parameters.

### `code/analysis/sensitivity.py`

**Purpose**: Verifies the robustness of the "cliff" by sweeping threshold definitions.

**Key Features**:
- Re-runs the two-stage sampling strategy for each threshold (2, 3, 4 hops).
- Compares significance and effect sizes across thresholds.

**Outputs**:
- `data/processed/sensitivity_results.json`: Results for each threshold iteration.
- `data/processed/sensitivity_report.md`: Markdown summary of stability.

## Troubleshooting

### "No real data source found"
The pipeline strictly requires real data. Ensure `data/raw/` is not empty. If the download fails, check your internet connection and verify the URLs in `code/ingest/download_data.py`.

### "Insufficient samples for statistical test"
If the 3+ hop bin has < 50 samples, the script will automatically merge it with the 2-hop bin. Check `data/processed/threshold_results.json` for `bin_status: "merged"`.

### "ImportError: No module named..."
Ensure you are running scripts from the project root and that `requirements.txt` has been installed.

## Output Interpretation

- **Reasoning Cliff**: A significant drop in accuracy (p < 0.05) between hop bins indicates a reasoning cliff.
- **Effect Size**: The magnitude of the accuracy drop. Larger values indicate a steeper cliff.
- **GAM p-value**: A low p-value (< 0.05) suggests non-linear performance degradation, supporting the cliff hypothesis.
