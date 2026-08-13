# Quickstart: Evaluating the Predictive Power of Machine Learning for Identifying Novel High-Entropy Alloy Compositions

## Prerequisites

*   Python 3.11+
*   Git
*   Access to a terminal (local or GitHub Codespaces)

## Installation

1.  **Clone the Repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-145-evaluating-the-predictive-power-of-machi
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins `pymatgen`, `scikit-learn`, `datasets`, `pandas`, `numpy`, `scipy`.*

## Data Setup

The pipeline automatically downloads data from verified Hugging Face sources if `data/raw/` is empty.

1.  **Run Data Ingestion**:
    ```bash
    python code/data_ingestion.py
    ```
    *This script fetches parquet files, filters for 5+ element systems, and generates `heas_train.csv`, `holdout_known.csv`, and `true_novel.csv`.*

2.  **Verify Data**:
    Check `data/processed/` for the generated CSV files. Ensure `holdout_known.csv` and `true_novel.csv` are not empty.

## Running the Pipeline

Execute the full pipeline (Feature Engineering -> Training -> Evaluation -> Report):

```bash
python code/train_model.py
python code/evaluate.py
python code/report_gen.py
```

### Output Locations

*   **Models**: `data/models/rf_model.pkl`, `data/models/gb_model.pkl`
*   **Metrics**: `data/processed/metrics_summary.csv`
*   **Novel Candidates**: `data/processed/top_100_novel_candidates.csv`
*   **Logs**: `logs/pipeline.log`

## Testing

Run unit and integration tests:

```bash
pytest tests/ -v
```

*   `tests/unit/test_descriptors.py`: Validates `pymatgen` descriptor calculation.
*   `tests/unit/test_data_split.py`: Verifies no overlap between training and hold-out sets.
*   `tests/integration/test_pipeline.py`: Runs the full ingestion-to-evaluation flow on a small sample.

## Troubleshooting

*   **OOM Error**: If `MemoryError` occurs, ensure `datasets` is using streaming mode or reduce the `sample_size` in `code/config.py`.
*   **Descriptor Errors**: If `pymatgen` fails to find an element, verify the chemical formula format in `data/raw/`.
*   **Convex Hull Error**: If the dataset is too small for a hull calculation, the script will fallback to centroid distance (logged).
