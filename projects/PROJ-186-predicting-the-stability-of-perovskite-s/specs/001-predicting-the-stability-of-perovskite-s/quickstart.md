# Quickstart: Predicting the Stability of Perovskite Structures Using Machine Learning

## 1. Prerequisites
- Python 3.11+
- `pip` (or `conda`)
- Access to a terminal with at least 14 GB disk space.

## 2. Installation

1.  **Clone the repository** (or navigate to the project root).
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` pins specific versions of `pymatgen`, `scikit-learn`, `pandas`, and `requests`.*

## 3. Running the Pipeline

### Option A: End-to-End Run
Execute the main orchestration script to run ingestion, training, and screening:
```bash
cd code
python main.py
```
This will:
1.  Download data (with fallback to OQMD if MP fails).
2.  Calculate descriptors.
3.  Train the model with 5-fold CV.
4.  Perform virtual screening.
5.  Save results to `results/`.

### Option B: Step-by-Step
- **Data Ingestion**:
  ```bash
  python data/download.py
  python data/descriptors.py
  ```
- **Model Training**:
  ```bash
  python models/train.py
  ```
- **Screening**:
  ```bash
  python models/predict.py
  ```

## 4. Verifying Results
After the pipeline completes:
1.  Check `results/metrics.json` for the RMSE (target ≤ 0.15 eV/atom).
2.  Inspect `results/screening_candidates.md` for the top 20 candidates.
3.  View plots in `results/` (e.g., `predicted-vs-true.png`).

## 5. Troubleshooting
- **API Rate Limit**: If the script fails with a 429 error, it will automatically retry. If it fails after retries, it will fall back to the OQMD dataset.
- **Memory Error**: If you encounter OOM errors, reduce the `MAX_ENTRIES` constant in `code/utils/config.py`.
- **Missing Radii**: Check `logs/exclusions.log` for entries skipped due to missing ionic radii.

## 6. Testing
Run the test suite to verify contract compliance:
```bash
pytest tests/
```
This includes unit tests for descriptor calculation and contract tests against the YAML schemas.
