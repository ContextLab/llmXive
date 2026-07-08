# Quickstart: Predicting Molecular Toxicity from Structural Alerts via Rule-Based Systems

## Prerequisites

-   Python 3.11+
-   Git
-   Access to a Linux environment (or WSL on Windows)

## Installation

1.  **Clone the Repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-356-predicting-molecular-toxicity-from-struc/code
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
    *Note: Ensure `rdkit` and `scikit-learn` are installed. DeLong's test is implemented in code, no external package required.*

## Data Acquisition

The pipeline automatically downloads the ToxCast dataset on the first run. To manually verify:
```bash
python src/data/download.py
```
*Output*: `data/raw/toxcast.csv` and `data/raw/.checksums.json`

## Running the Pipeline

Execute the full pipeline (Preprocessing -> Feature Extraction -> Training -> Evaluation -> Analysis -> Versioning):
```bash
python src/pipeline/run.py
```

### Expected Outputs

-   `data/processed/features_alerts.csv`
-   `data/processed/features_descriptors.csv`
-   `models/rule_based.pkl`, `models/logistic.pkl`
-   `results/metrics.json` (contains ROC-AUC, F1, Recall, DeLong's p-value, Recall difference, Error Analysis)
-   `state/projects/PROJ-356-...yaml` (updated with artifact hashes)

## Verification

To verify the results locally:
```bash
pytest tests/
```
*Expected*: All tests pass, and `results/metrics.json` contains a valid p-value and recall comparison.

## Troubleshooting

-   **RAM Error**: If you encounter OOM, edit `src/pipeline/run.py` to reduce `SAMPLE_SIZE` to 5000.
-   **SMARTS Error**: Check `config/structural_alerts.json` for syntax errors. Logs will indicate which pattern failed.
-   **No GPU**: Ensure no CUDA code is inadvertently called. The pipeline is CPU-only.