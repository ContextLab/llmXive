# Quickstart: Predicting the Impact of Laser Surface Texturing on Wear Resistance

## Prerequisites
- Python 3.11+
- `pip`
- At least 2 GB free disk space (for raw data + processed files)

## 1. Setup Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## 2. Data Acquisition
*Note: This step requires internet access. If specific dataset IDs are not found, the script will log warnings.*

```bash
# Run the ingestion script
python code/ingest.py
```
*   This will download data from OpenML/HuggingFace (if available) and look for local CSVs in `data/raw/`.
*   It will output `data/processed/aggregated_clean.csv`.

## 3. Run the Pipeline
Execute the full pipeline (Preprocessing -> Training -> Interpretation):

```bash
python code/train.py
python code/interpret.py
```

*   **Output**:
    *   `models/best_model.joblib`
    *   `reports/model_performance.json`
    *   `reports/interpretation.html`
    *   `final_report.md`

## 4. Verify Results
Check the `final_report.md` for:
*   **SC-004**: Record count (Target >= 300).
*   **SC-001**: Best R² score vs Linear baseline.
*   **SC-003**: LOMO transferability ratio.
*   **FR-008**: Permutation test p-values.

## 5. Troubleshooting
*   **Data Insufficiency**: If `normalized_count` < 100, the pipeline will halt primary analysis and run only sensitivity analysis (FR-011).
*   **Missing Dependencies**: Ensure `shap` and `scikit-learn` are installed.
*   **Runtime Error**: If the run exceeds 6 hours, check for infinite loops in grid search (unlikely with N=300).
