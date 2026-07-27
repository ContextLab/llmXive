# Usage Guide: llmXive VideoKR Analysis Pipeline

This guide provides detailed instructions for running the pipeline components, understanding the data flow, and interpreting the outputs.

## Quick Start

1. **Clone the repository** and navigate to the project root.
2. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```
3. **Run the pipeline**:
 Execute the scripts in the order listed below to ensure data dependencies are met.

## Step-by-Step Execution

### 1. Data Ingestion (User Story 1)

**Goal**: Download raw data and annotate with graph hops.

- **Download Data**:
 ```bash
 python code/ingest/download_data.py
 ```
 *Output*: Raw data files in `data/raw/`.

- **Annotate Graph**:
 ```bash
 python code/ingest/annotate_graph.py
 ```
 *Output*: `data/processed/annotated_videokr.csv`.
 *Note*: This script streams the dataset to handle large files and maps entities to graph nodes.

- **Verify Coverage**:
 ```bash
 python code/ingest/calculate_annotation_coverage.py
 ```
 *Output*: `data/processed/annotation_coverage.json`.

### 2. Accuracy Stratification (User Story 2)

**Goal**: Calculate accuracy per hop and detect the "reasoning cliff".

- **Stratify Accuracy**:
 ```bash
 python code/analysis/stratify_accuracy.py
 ```
 *Output*: Binned accuracy data.

- **Detect Threshold**:
 ```bash
 python code/analysis/detect_threshold.py
 ```
 *Output*: `data/processed/threshold_results.json`.
 *Method*: Permutation test with Bonferroni correction.

- **Generate Plots**:
 ```bash
 python code/analysis/generate_plots.py
 ```
 *Output*: `accuracy_vs_hop_raw.png`, `accuracy_binned.png`.

- **Binned Summary**:
 ```bash
 python code/analysis/generate_binned_summary.py
 ```
 *Output*: `data/processed/accuracy_binned.png` (binned view).

### 3. Sensitivity Analysis (User Story 3)

**Goal**: Verify robustness of the threshold across different definitions.

- **Run Sensitivity Sweep**:
 ```bash
 python code/analysis/sensitivity.py
 ```
 *Output*: `data/processed/sensitivity_thresholds.csv`.

- **Generate Reports**:
 ```bash
 python code/analysis/generate_sensitivity_table.py
 python code/analysis/generate_sensitivity_summary.py
 python code/analysis/plot_sensitivity_overlay.py
 ```
 *Output*: `sensitivity_summary.md`, `sensitivity_overlay.png`, `stability_metric.json`.

### 4. Final Reporting

- **Generate Final Report**:
 ```bash
 python code/analysis/generate_final_report.py
 ```
 *Output*: `data/processed/final_report.md`.

## Troubleshooting

- **Missing Data**: If scripts fail with "File not found", ensure `data/raw/` contains the downloaded datasets. Run `code/ingest/download_data.py` first.
- **Memory Errors**: The `annotate_graph.py` script uses chunked processing. If you encounter memory errors, ensure you have sufficient RAM (7GB+ recommended) or check the logging for chunk sizes.
- **Graph Disconnected**: If many records are marked "unresolvable", check the connectivity of the loaded knowledge graph.

## Output Interpretation

- **`threshold_results.json`**: Look for `is_significant: true`. If true, a statistically significant "cliff" was detected at the `optimal_knot` hop count.
- **`stability_metric.json`**: A `robustness_status` of "PASS" indicates the cliff is robust across multiple threshold definitions (>= 2 significant thresholds).
- **`final_report.md`**: The comprehensive document aggregating all findings, including the methodology override note regarding GAMs.
