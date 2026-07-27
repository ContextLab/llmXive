# Quickstart: Assessing Parcellation Sensitivity of Hub Resilience in Healthy Connectomes

## Prerequisites
*   Python 3.11+
*   `pip` (or `conda`)
*   Git
*   Access to the verified datasets (via Hugging Face or OpenNeuro).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-800-assessing-parcellation-sensitivity-of-hu
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
    *Note: `requirements.txt` includes `networkx`, `nilearn`, `scipy`, `pandas`, `matplotlib`, `huggingface_hub`.*

4.  **Verify environment**:
    ```bash
    python -c "import networkx; import nilearn; print('Environment OK')"
    ```

## Running the Pipeline

### Option A: Full Analysis (If Data Available)
Run the main orchestration script. This will attempt to download data, process it, and generate results.
```bash
python code/main.py --mode full
```
*   **Output**: `data/results/validation_report.json`, `data/results/plots/` (Venn, Heatmap, Line).

### Option B: Pre-computed Data Mode
If raw data processing is not feasible, run with pre-computed matrices (if available in `data/raw/`).
```bash
python code/main.py --mode precomputed
```

### Option C: Methodological Demo (Synthetic Data)
If no real data is available, run with synthetic data to demonstrate the pipeline logic.
```bash
python code/main.py --mode demo
```

## Verification
1.  **Check Artifacts**:
    ```bash
    ls -l data/processed/
    ls -l data/results/
    ```
2.  **Run Tests**:
    ```bash
    pytest tests/ -v
    ```
3.  **Validate Citations**:
    ```bash
    python code/validators/validate_citations.py
    ```

## Troubleshooting
*   **Memory Error**: Ensure `streaming=True` is used in the loader. Reduce `N` in `config.py` if necessary.
*   **Data Not Found**: Check the "Verified datasets" section in `research.md`. If the URL is invalid, the pipeline will switch to `demo` mode.
*   **Time Out**: The Spatial Spin Test will automatically reduce iterations to 500 if the time limit is approached.
