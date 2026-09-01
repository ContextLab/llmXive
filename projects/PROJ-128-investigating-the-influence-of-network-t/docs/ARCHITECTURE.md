# Architecture Overview

## Design Principles

1. **Modularity**: Each component (preprocessing, analysis, reporting) is encapsulated in its own module.
2. **Reproducibility**: All random seeds are fixed; data processing steps are deterministic.
3. **Statistical Rigor**: Leave-One-Out (LOO) strategy ensures independence between training and testing data.
4. **Associational Framing**: All findings are presented as correlations, not causal predictions.

## Component Breakdown

### 1. Data Loading (`code/preprocess/loader.py`)
- **Purpose**: Fetch and load HCP dMRI and fMRI data from OpenNeuro.
- **Key Functions**: `load_hcp_fmri`, `load_hcp_dmri`, `load_hcp_data`.
- **Constraints**: Must fail loudly if real data is not available; no synthetic fallbacks.

### 2. Structural Preprocessing (`code/preprocess/structural.py`)
- **Purpose**: Convert dMRI tractography results into graph metrics.
- **Key Functions**: `calculate_graph_metrics`, `process_subject_structural_metrics`.
- **Metrics**: Global efficiency, average clustering coefficient, modularity.
- **Constraints**: Sparsity >90% exclusion.

### 3. Functional Preprocessing (`code/preprocess/functional.py`)
- **Purpose**: Extract dynamic functional states from fMRI time series.
- **Key Functions**: `compute_sliding_window_correlation`, `extract_dynamic_states_loo`, `calculate_dynamic_metrics`.
- **LOO Strategy**:
 - Concatenate windowed correlations from all subjects except the current one.
 - Apply K-Means (k=5) to generate centroids.
 - Assign the current subject's windows to these LOO centroids.
- **Metrics**: Dwell time, number of visited states.

### 4. Correlation Analysis (`code/analysis/correlation.py`)
- **Purpose**: Correlate structural and dynamic metrics.
- **Key Functions**: `check_normality`, `calculate_correlation`, `benjamini_hochberg_fdr`.
- **Method**:
 - Shapiro-Wilk test for normality.
 - Pearson (if normal) or Spearman (if non-normal) correlation.
 - FDR correction (q=0.05) on p-values.

### 5. Robustness Analysis (`code/analysis/robustness.py`)
- **Purpose**: Verify stability of results to parameter changes.
- **Key Functions**: `run_sensitivity_analysis`, `calculate_sensitivity_metrics`.
- **Parameters**:
 - Window length (30 TR vs. 20 TR).
 - Density threshold (±5% variation).

### 6. Reporting (`code/reports/generate_report.py`)
- **Purpose**: Generate the final summary report.
- **Key Functions**: `generate_final_report`, `calculate_sensitivity_metrics`.
- **Requirements**: Explicit "associational" language; sensitivity tables included.

### 7. Main Orchestrator (`code/main.py`)
- **Purpose**: Coordinate the full pipeline.
- **Key Functions**: `process_subject`, `aggregate_metrics_to_csv`.
- **Output**: Aggregated CSVs and exclusion logs.

## Data Flow

1. **Raw Data** (`data/raw/`) → **Loader** → **Preprocessed Data** (in memory).
2. **Preprocessed Data** → **Structural/Functional Modules** → **Per-Subject Metrics**.
3. **Per-Subject Metrics** → **Aggregator** → **CSV Files** (`data/processed/`).
4. **CSV Files** → **Correlation/Robustness Modules** → **Analysis Results**.
5. **Analysis Results** → **Report Generator** → **Final Report** (`data/reports/`).

## Dependencies

- **Python**: >=3.8
- **Core Libraries**: numpy, pandas, scipy, scikit-learn, networkx, nilearn, statsmodels, pyyaml.
- **Hardware**: CPU-only (no GPU acceleration).

## Error Handling

- **Data Loading**: Fails loudly if real data is missing.
- **Convergence**: Subjects failing K-Means convergence are logged and excluded.
- **Sparsity**: Graphs with sparsity >90% are excluded and logged.

## Future Work

- Integration with additional datasets.
- Extension to multi-modal connectivity analysis.
- Real-time visualization of state transitions.
