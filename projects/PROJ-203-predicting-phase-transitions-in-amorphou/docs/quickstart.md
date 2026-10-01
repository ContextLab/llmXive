# Quickstart Guide: Predicting Phase Transitions in Amorphous Solids

This guide provides instructions for setting up and running the full machine learning pipeline to predict phase transitions (glass transition temperature $T_g$ and crystallization propensity) in amorphous solids.

## Prerequisites

- **Python**: Version 3.9 or higher
- **Operating System**: Linux (preferred for MD simulation tools), macOS, or Windows (with WSL2)
- **Disk Space**: Minimum 20 GB (for MD trajectories, processed data, and model artifacts) [UNRESOLVED-CLAIM: c_7e857cdd — status=not_enough_info]
- **RAM**: Minimum 16 GB (for simulation and model training) [UNRESOLVED-CLAIM: c_55398b2b — status=not_enough_info]
- **External Tools**:
 - **LAMMPS** or **OpenMM** installed and available in `PATH`
 - **OpenKIM** potentials available (verified by `code/data/simulate.py`)

## Project Structure

```
PROJ-203-predicting-phase-transitions-in-amorphou/
├── code/ # Source code
│ ├── data/ # Data generation and processing
│ ├── models/ # Model training and evaluation
│ ├── utils/ # Utilities (logging, validation, plotting)
│ ├── config.py # Configuration management
│ ├── main.py # Pipeline entry point
│ └── requirements.txt # Python dependencies
├── data/ # Data directories
│ ├── raw/ # Raw input data (literature_subset.csv)
│ ├── processed/ # Processed datasets (final_dataset.parquet)
│ └── logs/ # Simulation logs and metadata
├── docs/ # Documentation
│ ├── quickstart.md # This file
│ └── reports/ # Generated reports and figures
├── tests/ # Unit and integration tests
├── artifacts/ # Model artifacts and figures
└── specs/ # Design documents
```

## Installation

1. **Clone the repository** (if not already done):
 ```bash
 git clone <repository-url>
 cd PROJ-203-predicting-phase-transitions-in-amorphou
 ```

2. **Create a virtual environment** (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

4. **Verify MD simulation tools**:
 Ensure `lammps` or `openmm` is installed and accessible. Run the verification script:
 ```bash
 python code/data/simulate.py --verify-only
 ```

## Data Preparation

Before running the pipeline, ensure the raw literature data is available:

- **Required File**: `data/raw/literature_subset.csv`
- **Content**: Must contain 24 compositions with columns: `composition_id`, `Tg_exp`, `Tx_exp`, `dsc_cooling_rate_K_s`, `chemical_family`.
- **Validation**: The pipeline will fail loudly if this file is missing or corrupted.

To validate the data file:
```bash
python code/data/validate_literature_subset.py
```

## Running the Pipeline

The full pipeline can be executed end-to-end via the main script. This will:
1. Validate input data.
2. Run MD simulations (or use pre-existing trajectories if available).
3. Extract structural descriptors.
4. Merge descriptors with experimental labels.
5. Train regression and classification models.
6. Generate interpretability reports (SHAP, partial dependence).
7. Output all metrics and figures.

### Full Pipeline Execution

```bash
python code/main.py
```

**Expected Runtime**: ~6 hours (limited by simulation and model training).
**Output Artifacts**:
- `data/processed/final_dataset.parquet`
- `models/tg_regressor.pkl`, `models/crystallization_classifier.pkl`
- `docs/reports/metrics.json`, `docs/reports/interpretability_report.md`
- `docs/reports/shap_plots/`, `docs/reports/confusion_matrix.png`

### Individual Task Execution

If you wish to run specific stages of the pipeline:

- **Data Generation**:
 ```bash
 python code/data/simulate.py
 python code/data/descriptor_utils.py
 python code/data/merge.py
 python code/data/finalize_dataset.py
 ```

- **Model Training**:
 ```bash
 python code/models/train.py
 ```

- **Evaluation & Interpretability**:
 ```bash
 python code/models/evaluate.py
 python code/models/collinearity_analysis.py
 python code/models/sensitivity_analysis.py
 ```

## Configuration

Configuration is managed via `code/config.py`. Key settings include:
- **Paths**: `data/raw`, `data/processed`, `models`, `artifacts`
- **Simulation Parameters**: Cooling rate, time steps, trajectory truncation limits.
- **Model Parameters**: Hyperparameter search ranges for Random Forest.

To modify settings, edit `code/config.py` or set environment variables as documented in the `config.py` source.

## Outputs

Upon successful execution, the following artifacts will be generated:

| Artifact | Path | Description |
|----------|------|-------------|
| Final Dataset | `data/processed/final_dataset.parquet` | Merged dataset with descriptors and labels |
| Regression Model | `models/tg_regressor.pkl` | Trained Random Forest for $T_g$ prediction |
| Classification Model | `models/crystallization_classifier.pkl` | Trained Random Forest for crystallization propensity |
| Metrics Report | `docs/reports/metrics.json` | RMSE, ROC-AUC, CV scores |
| SHAP Plots | `docs/reports/shap_plots/` | Family-specific SHAP summary plots |
| Interpretability Report | `docs/reports/interpretability_report.md` | Analysis of universal vs. family-specific predictors |
| Confusion Matrix | `docs/reports/confusion_matrix.png` | Visualization of classification performance |
| Collinearity Report | `docs/reports/collinearity_report.json` | VIF analysis for predictors |
| Sensitivity Report | `data/processed/sensitivity_report.json` | Threshold sensitivity analysis |

## Troubleshooting

### "FATAL: literature_subset.csv missing"
Ensure `data/raw/literature_subset.csv` exists and is not corrupted.

### "OpenKIM potentials not found"
Verify OpenKIM installation and network connectivity. The `simulate.py` script includes a verification step.

### Simulation Timeout
The pipeline enforces a 6-hour total wall-clock limit. [UNRESOLVED-CLAIM: c_436850d2 — status=not_enough_info] If exceeded, partial results are saved. Check `data/logs/simulation_times.json` for details.

### Memory Errors
Reduce batch sizes or run on a machine with more RAM. The pipeline is optimized for 24 compositions but may require adjustments for larger datasets. [UNRESOLVED-CLAIM: c_4f366982 — status=not_enough_info]

## Support

For issues or questions, refer to the `docs/` directory or consult the design documents in `specs/`.

---
*Generated by llmXive research-implementer agent.*
