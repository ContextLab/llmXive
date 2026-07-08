# Quickstart: Quantifying the Effect of Alloying Elements on the Glass-Forming Ability of Metallic Glasses

## Prerequisites

-   Python 3.11+
-   Git
-   Access to GitHub Actions (for CI execution) or a local environment with 7GB+ RAM.

## Installation

1.  **Clone the repository** and navigate to the project directory:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-124-quantifying-the-effect-of-alloying-eleme
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` pins `pymatgen`, `scikit-learn`, `statsmodels`, and `pandas`.*

## Running the Pipeline

The pipeline consists of three sequential scripts. Execute them in order:

### Step 1: Ingest and Engineer Features
Downloads the dataset from the verified HuggingFace URL and computes physics-based descriptors.
```bash
python code/01_ingest_and_engineer.py
```
*Output*: `data/processed/engineered_features.csv`

### Step 2: Train and Validate Models
Trains Random Forest and Gradient Boosting models, performs LOCO cross-validation, checks for heteroscedasticity, and saves the best model.
```bash
python code/02_train_and_validate.py
```
*Output*: `output/best_model.pkl` (and potentially `best_model_weighted.pkl`)

### Step 3: Screen Candidates
Generates ternary combinations, predicts GFA, filters by threshold, and outputs the top candidates.
```bash
python code/03_screen_candidates.py
```
*Output*: `output/top_candidates.csv`, `output/verification_requests.json`

## Verification

To verify the pipeline:
1.  Check that `output/top_candidates.csv` exists and contains rows with `predicted_log_rc < 4.0`.
2.  Verify `output/verification_requests.json` contains the top 10 candidates with `status: "pending_verification"`.
3.  Run the unit tests:
    ```bash
    pytest tests/
    ```

## Troubleshooting

-   **Dataset Download Failed**: The script retries 3 times with 5s backoff. If it fails, check your internet connection and the verified URL.
-   **Unknown Elements**: Rows with elements not in Pymatgen are logged and skipped. Check `logs/engineering.log` for details.
-   **Memory Error**: The pipeline is designed for <7GB RAM. If OOM occurs, reduce the number of hyperparameter combinations in `02_train_and_validate.py`.
