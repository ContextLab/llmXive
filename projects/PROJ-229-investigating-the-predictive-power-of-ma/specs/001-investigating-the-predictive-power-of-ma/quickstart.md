# Quickstart: Investigating the Predictive Power of Machine Learning for Identifying Novel Phase-Change Materials

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- Access to the `matbench` library (open source)
- (Optional) Materials Project API credentials (not required for this plan)

## Installation

1. **Clone the Repository**:
   ```bash
   git clone <repo-url>
   cd <repo-dir>
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify Dependencies**:
   ```bash
   python -c "import pymatgen; import pysr; import matbench; print('All dependencies installed.')"
   ```

## Data Retrieval

1. **Run Data Retrieval Script**:
   ```bash
   python code/data/fetch_matbench.py
   ```
   - This script will download the `matbench` dataset.
   - It will also generate `data/external/literature_pcms_raw.csv` (with a fallback if external download fails).

2. **Verify Data**:
   - Check `data/raw/` for downloaded files.
   - Verify checksums in `state/`.

## Feature Engineering

1. **Run Feature Engineering Script**:
   ```bash
   python code/data/compute_features.py
   ```
   - This script computes elemental and graph-based descriptors.
   - Output: `data/processed/featurized_data.csv`.

## Model Training

1. **Train Baseline Models**:
   ```bash
   python code/models/train_baseline.py
   ```
   - Output: `data/results/baseline_metrics.json`.

2. **Train Symbolic Regression Model**:
   ```bash
   python code/models/train_symbolic.py
   ```
   - Output: `data/results/symbolic_formulas.txt`.

3. **Run SHAP Analysis**:
   ```bash
   python code/models/evaluate.py
   ```
   - Output: `data/results/shap_analysis.json`.

## Validation

1. **Run External Validation**:
   ```bash
   python code/models/validate.py
   ```
   - Output: `data/results/validation_report.json`.

2. **Run Sensitivity Analysis**:
   ```bash
   python code/models/sensitivity.py
   ```
   - Output: `data/results/sensitivity_analysis.csv`.

## Results

- **Metrics**: Check `data/results/` for all model metrics and reports.
- **Plots**: Generated plots are stored in `data/results/plots/`.

## Troubleshooting

- **Data Unavailable**: If `matbench` is unavailable, the script will log a fatal error. Check your internet connection and `matbench` installation.
- **Memory Errors**: If memory errors occur, reduce the dataset size or enable streaming.
- **Symbolic Regression Failure**: If PySR fails to converge, check the time budget and dataset size.

## Next Steps

- Review the `plan.md` for detailed implementation steps.
- Check the `contracts/` directory for schema validation.
- Run the test suite: `pytest tests/`.