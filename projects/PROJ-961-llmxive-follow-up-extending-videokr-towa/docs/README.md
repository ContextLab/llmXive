# PROJ-961: llmXive Follow-up - Extending VideoKR

This project implements a rigorous analysis of the "VideoKR: Towards Knowledge- and Reasoning-Intensive Video Understanding" dataset to detect non-linear "reasoning cliffs" in model performance as graph traversal complexity (chain length) increases.

## Overview

The pipeline performs the following steps:
1. **Data Ingestion**: Downloads the VideoKR-SFT dataset and the associated Knowledge Graph.
2. **Structural Annotation**: Maps question entities to graph nodes and calculates the shortest path (chain length) for each record.
3. **Stratified Analysis**: Calculates accuracy rates per hop-bin (1-hop, 2-hop, 3+ hops).
4. **Threshold Detection**: Uses a Permutation Test to detect significant change-points (cliffs) in accuracy.
5. **Sensitivity Analysis**: Sweeps threshold definitions to verify robustness.
6. **GAM Implementation**: Fits a Generalized Additive Model to test for non-linearity in the continuous domain.

## Project Structure

```text
.
├── code/
│ ├── ingest/ # Data download, checksumming, and graph annotation
│ ├── analysis/ # Statistical analysis, plotting, and sensitivity sweeps
│ └── utils/ # Shared utilities (config, graph algorithms, entity linking)
├── data/
│ ├── raw/ # Downloaded raw datasets (VideoKR-SFT, KG)
│ └── processed/ # Annotated CSVs, results JSONs, and plots
├── tests/
│ ├── unit/ # Unit tests for core logic
│ └── integration/ # End-to-end pipeline tests
├── docs/ # Documentation
├── state/ # Versioning and state tracking
└── requirements.txt # Python dependencies
```

## Prerequisites

- Python 3.9+
- `pip`

## Installation

1. Clone the repository.
2. Install dependencies:

 ```bash
 pip install -r requirements.txt
 ```

## Usage

The pipeline is executed via the main scripts in `code/`.

### 1. Data Ingestion and Annotation

Downloads the dataset and annotates it with chain lengths using the two-stage sampling strategy.

```bash
python code/ingest/annotate_graph.py
```

**Output**: `data/processed/annotated_videokr.csv`, `data/processed/sampling_log.json`

### 2. Accuracy Stratification

Calculates accuracy rates for each hop bin.

```bash
python code/analysis/stratify_accuracy.py
```

**Output**: `data/processed/accuracy_by_bin.json`

### 3. Threshold Detection (Permutation Test)

Detects the optimal change-point and tests for significance.

```bash
python code/analysis/detect_threshold.py
```

**Output**: `data/processed/threshold_results.json`

### 4. Generalized Additive Model (GAM)

Fits a GAM to test for non-linearity.

```bash
python code/analysis/fit_gam.py
```

**Output**: `data/processed/gam_results.json`

### 5. Sensitivity Analysis

Sweeps threshold definitions (2, 3, 4 hops) to verify robustness.

```bash
python code/analysis/sensitivity.py
```

**Output**: `data/processed/sensitivity_results.json`

### 6. Visualization

Generates all required plots (binned, continuous, sensitivity overlay).

```bash
python code/analysis/generate_plots.py
python code/analysis/plot_sensitivity_overlay.py
```

**Output**: `figures/*.png`

## Configuration

Configuration is managed via `code/utils/config.py`. Key settings include:
- `PROJECT_ROOT`: Base directory for the project.
- `DATA_PATH`: Where raw and processed data are stored.
- `SEED`: Random seed for reproducibility.

## Testing

Run unit and integration tests:

```bash
python -m pytest tests/ -v
```

## License

[Project License]
