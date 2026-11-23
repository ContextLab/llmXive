# PROJ-379: Predicting Molecular Excitation Wavelengths with Graph Neural Networks

## Overview
This project implements a pipeline to predict molecular excitation wavelengths (λmax) from SMILES strings using Graph Neural Networks (GNNs) and baseline models. The pipeline ingests real UV-Vis spectral data, processes it into scaffold-split datasets, trains models on CPU, and performs rigorous statistical evaluation including power analysis and feature attribution.

## Quickstart

### 1. Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Data Ingestion and Preprocessing

Run the full data pipeline to fetch real UV-Vis data from PubChem/SDBS, process molecules, and generate scaffold splits:

```bash
# Fetch and process data
python code/ingest.py

# Validate data integrity
python code/validate_data.py

# Generate scaffold splits
python code/split.py

# Merge data with splits
python code/merge_split.py
```

**Output**: `data/processed/cleaned.csv`, `data/processed/split_indices.json`, `data/processed/train_val_test.csv`

### 3. Model Training

Train the GNN model and baseline on CPU:

```bash
python code/train.py
```

**Output**: `data/processed/model.pt`, `data/processed/timing.json`

### 4. Evaluation and Metrics

Evaluate model performance and compute statistical metrics:

```bash
python code/evaluate.py
```

**Output**: `data/processed/metrics_partial.json`, `data/processed/power_analysis.json`

### 5. Feature Attribution and Sensitivity Analysis

Analyze feature importance and perform sensitivity sweeps:

```bash
# Check collinearity and generate redundancy masks
python code/collinearity_check.py

# Compute raw attribution
python code/explain.py

# Apply masks to attribution
python code/apply_mask.py

# Run sensitivity sweep
python code/sensitivity.py

# Generate sensitivity report
python code/generate_sensitivity_report.py
```

**Output**: `data/processed/redundancy_masks.json`, `data/processed/raw_attribution.json`, `data/processed/masked_attribution.json`, `data/processed/sensitivity_report.csv`

### 6. Aggregate Results

Generate the final metrics summary:

```bash
python code/analyze_results.py
```

**Output**: `data/processed/metrics.json`

## Interpreting `metrics.json`

The final `metrics.json` file contains the complete evaluation results:

```json
{
 "mae": 25.3,
 "r2": 0.82,
 "wilcoxon_p_value": 0.003,
 "confidence_interval_95": [15.2, 35.4],
 "sc001_status": "PASS",
 "collinearity_flags": {
 "ecfp_correlation": false,
 "gnn_similarity": false
 },
 "redundancy_masks": {
 "molecule_1": [0, 1, 0,...],
 "molecule_2": [1, 0, 0,...]
 },
 "power_status": {
 "n": 150,
 "effect_size": 0.65,
 "power_status": "ADEQUATE"
 },
 "attribution_results": {
 "top_contributing_atoms": [...],
 "masked_weights": [...]
 }
}
```

### Key Fields Explained

- **`mae`**: Mean Absolute Error in nanometers. Lower is better. Success threshold: < 30 nm.
- **`r2`**: Coefficient of determination. Higher is better (closer to 1.0).
- **`wilcoxon_p_value`**: p-value from Wilcoxon signed-rank test comparing GNN vs baseline. < 0.05 indicates significant improvement.
- **`confidence_interval_95`**: 95% confidence interval for the MAE difference between models.
- **`sc001_status`**: "PASS" if p < 0.05 AND MAE < 30 nm; otherwise "FAIL".
- **`collinearity_flags`**: Indicates whether ECFP bits or GNN subgraphs show high correlation (>0.9).
- **`redundancy_masks`**: Binary masks applied to attribution weights to remove spurious contributions from redundant substructures.
- **`power_status`**: Test set size (n), effect size (Cohen's d), and whether power is adequate (n ≥ 50).
- **`attribution_results`**: Final masked attribution weights identifying molecular substructures contributing to λmax predictions.

## Project Structure

```
projects/PROJ-379-predicting-molecular-excitation-waveleng/
├── code/
│ ├── ingest.py # Data ingestion from PubChem/SDBS
│ ├── validate_data.py # Data validity checks
│ ├── split.py # Scaffold splitting
│ ├── merge_split.py # Merge data with splits
│ ├── model.py # GNN and baseline models
│ ├── train.py # Training loop
│ ├── evaluate.py # Evaluation and statistics
│ ├── collinearity_check.py # Collinearity detection
│ ├── explain.py # Feature attribution
│ ├── apply_mask.py # Apply redundancy masks
│ ├── sensitivity.py # Sensitivity analysis
│ ├── generate_sensitivity_report.py # Report generation
│ ├── analyze_results.py # Aggregate final metrics
│ ├── timing_logger.py # Pipeline timing
│ ├── utils.py # Utility functions
│ ├── models.py # Pydantic data models
│ └──...
├── data/
│ ├── raw/ # Raw downloaded data
│ └── processed/ # Cleaned data, splits, models, metrics
├── tests/ # Test suite
├── docs/ # Documentation
├── requirements.txt # Dependencies
└── README.md # This file
```

## Requirements

- Python 3.9+
- CPU-only execution (no GPU required)
- Memory: ≤7GB RAM
- Time: ≤6 hours for full pipeline

## Data Sources

- **Primary**: PubChem and SDBS (Spectral Database for Organic Compounds)
- **Secondary**: HuggingFace `zjunlp/UV-Vis-ML` dataset (fallback only)

## License

MIT License