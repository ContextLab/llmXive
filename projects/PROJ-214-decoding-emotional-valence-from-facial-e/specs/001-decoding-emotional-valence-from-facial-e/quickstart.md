# Quickstart: Decoding Emotional Valence from Facial EMG Patterns with Machine Learning

## Prerequisites

*   Python 3.11+
*   pip
*   Access to a GitHub Actions runner (or local machine with similar constraints).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-214-decoding-emotional-valence-from-facial-e
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

## Running the Pipeline

### Step 1: Download Data
The script downloads the DEAP-EMG dataset from the verified HuggingFace source and validates the checksum.
```bash
python code/download.py
```
*Output*: `data/raw/deap_emg.zip` (checksum verified).

### Step 2: Preprocess & Train
This step runs the full pipeline: preprocessing, nested LOSO cross-validation, and model training.
```bash
python code/train.py
```
*Output*: Trained models saved to `data/models/model_bundle.pkl`, cross-validation metrics logged to `data/results/cv_metrics.json`.

### Step 3: Analyze Importance
Calculates permutation importance, SHAP values, and Nagelkerke’s R² change.
```bash
python code/importance.py
```
*Output*: `data/results/importance_scores.json`, `data/results/variance_explanation.json`.

### Step 4: Validate & Report
Runs permutation tests, paired t-tests, sensitivity analysis, and generates the final report.
```bash
python code/validate.py
python code/report.py
```
*Output*: `data/results/final_report.md` containing p-values, Cohen’s d, and sensitivity tables.

## Verification

To verify the pipeline on a subset (e.g., 2 subjects) for debugging:
```bash
python code/train.py --subjects 1,2 --fast-mode
```

## Troubleshooting

*   **Memory Error**: Ensure `code/train.py` is processing subjects sequentially. Check `data/processed/` is empty after run.
*   **Download Failed**: Verify internet access. The script retries 3 times. Check `data/raw/` for partial downloads.
*   **No GPU**: The code is designed for CPU. Do not attempt to install CUDA dependencies.
*   **Model Not Found**: Ensure Step 2 (`train.py`) completed successfully before running Step 3. The model is saved at `data/models/model_bundle.pkl`.