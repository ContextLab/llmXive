# Quickstart: Quantifying the Impact of Dataset Size on ML Accuracy for Material Properties

## Prerequisites

*   Python 3.10+
*   `pip`
*   Access to GitHub Actions (for CI) or local Linux environment.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-526-quantifying-the-impact-of-dataset-size-o
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins `scikit-learn`, `pandas`, `numpy`, `pymatgen`, `matminer`, `huggingface_hub`.*

## Running the Pipeline

The pipeline is executed in three stages via CLI scripts.

### Stage 1: Data Acquisition & Descriptors
Download data from verified sources and generate Magpie vectors.
```bash
python code/download_data.py --output data/raw/
python code/generate_descriptors.py --input data/raw/ --output data/processed/
```
*This step validates the checksums and ensures no structural features are included.*

### Stage 2: Learning Curves & Scaling
Train models and fit power laws.
```bash
python code/train_learning_curves.py --features data/processed/magpie_features.csv --output data/processed/learning_curves.csv
python code/fit_scaling_laws.py --input data/processed/learning_curves.csv --output data/processed/scaling_results.csv
```
*This step handles the 10-subset, 3-seed protocol and flags non-power-law properties.*

### Stage 3: Statistical Analysis & Visualization
Correlate physics with data efficiency and generate plots.
```bash
python code/analyze_physics.py --input data/processed/scaling_results.csv --output data/processed/final_analysis.csv
python code/visualize_results.py --input data/processed/final_analysis.csv --output figures/
```

## Verification

Run the contract tests to ensure data integrity:
```bash
pytest tests/contract/
```

## Troubleshooting

*   **Memory Error**: If OOM occurs, reduce the batch size in `download_data.py` or `generate_descriptors.py`.
*   **Fit Failure**: If a property fails to fit, check `data/processed/scaling_results.csv` for the "non-power-law" flag. This is expected behavior for some properties.
*   **Missing Data**: If a property is missing from the results, check `data/raw/` to ensure the verified URL provided data for that class.
