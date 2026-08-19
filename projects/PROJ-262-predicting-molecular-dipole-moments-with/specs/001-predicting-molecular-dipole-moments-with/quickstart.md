# Quickstart: Predicting Molecular Dipole Moments with Graph Neural Networks

## 1. Prerequisites

*   Python 3.11+
*   `pip` (Python package manager)
*   Sufficient free disk space (for QM9 download and processing)
*   ~ GB RAM (managed to 7GB via streaming)

## 2. Installation

1.  **Clone the Repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-262-predicting-molecular-dipole-moments-with
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` includes `torch`, `torch-geometric`, `rdkit`, `scikit-learn`, `pandas`, `numpy`.*

## 3. Data Download & Preprocessing

Run the data preparation script. This will download the QM9 subset via PyTorch Geometric, verify integrity, and extract features.

```bash
python code/download_data.py
python code/preprocess.py
```

*   **Output**: `data/raw/qm9_subset.parquet`, `data/processed/features_2d.parquet`, `data/processed/features_3d.parquet`.
*   **Verification**: Check `data/processed/exclusion_log.txt` for any molecules dropped due to missing data.

## 4. Model Training & Evaluation

Execute the full pipeline (training seeds, evaluation, attribution, and visualization).

```bash
python code/train.py --seeds 0 1 2 3 4
python code/evaluate.py
python code/attribution.py
python code/visualize.py
```

*   **Output**: `results/metrics_summary.csv`, `results/predictions.csv`, `results/figures/`.
*   **Runtime**: Expected several hours on 2 CPU cores.

## 5. Statistical Analysis

Run the statistical significance tests.

```bash
python code/stats.py
```

*   **Output**: `results/statistical_summary.json` containing t-test p-values, degrees of freedom, and confidence intervals.

## 6. Validation

Validate the output data against the defined contracts.

```bash
pytest tests/contract/test_schemas.py
```

## 7. Troubleshooting

*   **Out of Memory**: If `preprocess.py` fails with OOM, reduce the subset size in `code/download_data.py` (e.g., `subset_size=5000`).
*   **CUDA Error**: This pipeline is CPU-only. If you see CUDA errors, ensure `torch` is installed in CPU mode (`pip install torch --index-url https://download.pytorch.org/whl/cpu`).
*   **Missing Data**: If the QM9 download fails, verify your internet connection and check the verified source in `research.md` (PyTorch Geometric loader).