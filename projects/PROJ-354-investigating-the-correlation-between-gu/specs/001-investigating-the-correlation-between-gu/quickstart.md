# Quickstart: Gut Microbiome & Cognitive Function Analysis Pipeline

## Prerequisites

*   Python 3.11+
*   `pip` or `conda`
*   Sufficient free disk space (for temporary processing)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-354-investigating-the-correlation-between-gu
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -e .
    # Or manually:
    pip install pandas numpy scipy scikit-learn statsmodels biom-format pyyaml datasets seaborn matplotlib pytest black ruff
    ```

## Running the Pipeline

### 1. Generate Synthetic Data
Since UK Biobank data is access-gated, the pipeline uses a deterministic synthetic generator.
```bash
python code/pipelines/download.py --seed 42 --output data/raw/synthetic_ukb.parquet
```
*This creates a dataset mimicking UKB structure.*

### 2. Preprocess Data (ILR Transformation)
```bash
python code/pipelines/preprocess.py --input data/raw/synthetic_ukb.parquet --output data/processed/ilr_transformed.parquet
```
*This filters out antibiotic users and applies ILR transformation.*

### 3. Run Analysis
```bash
python code/pipelines/analyze.py --input data/processed/ilr_transformed.parquet --output results/associations/
```
*This fits linear models, applies BH correction, and generates interaction terms.*

### 4. Generate Plots
```bash
python code/paper/plots.py --input results/associations/main_effects.parquet --output results/plots/
```
*Generates Manhattan-style plots.*

## Verification

Run the test suite to ensure reproducibility:
```bash
pytest tests/ -v
```

### Code Formatting & Linting
To verify code quality, run `black` and `ruff`:
```bash
black code/
ruff check code/
```
*Expected Output: No errors. A linting report is generated in `results/linting_report.txt` (Task T041).*

## Output Structure

*   `data/raw/`: Generated synthetic raw data.
*   `data/processed/`: ILR-transformed, filtered data.
*   `results/associations/`: Parquet files with beta coefficients, p-values, and BH-adjusted p-values.
*   `results/plots/`: PNG/SVG figures (Manhattan plots).
*   `results/sensitivity/`: Threshold sweep results.
*   `results/linting_report.txt`: Output from `ruff` and `black` (Task T041).

## Troubleshooting

*   **Memory Error**: The pipeline streams data. If you encounter memory errors, reduce the synthetic cohort size in `code/pipelines/download.py`.
*   **Missing Dependencies**: Ensure `biom-format` is installed. It may require `scipy` and `numpy` to be installed first.
*   **Zero Counts**: The pipeline automatically adds a small pseudocount before ILR transformation.