# Quickstart: Investigating the Correlation Between Gut Microbiome Composition and Immune Response to Influenza Vaccination

## Prerequisites

- Python 3.11+
- `pip`
- Access to a Linux environment (GitHub Actions runner or local Linux/WSL).

## Installation

1. **Clone the repository** (or navigate to the project directory):
   ```bash
   cd projects/PROJ-251-investigating-the-correlation-between-gu
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Dependencies include: pandas, scipy, scikit-learn, numpy, biom-format, ruff, black.*

## Running the Pipeline

The pipeline is executed via a single entry point script:

```bash
# Step 1: Lint and Format (Mandatory Pre-requisite)
ruff check code/
black code/
# If the above fails, the pipeline stops.

# Step 2: Run the pipeline
python code/main_pipeline.py
```

### What happens when you run it?

1. **Data Search (T010)**:
   - Attempts to find a real, open-access NCBI SRA dataset with paired 16S and serology.
   - **Blocking**: If no real data is found, the pipeline halts and reports "No Real Data Found".
   - **Fallback**: If the user explicitly enables "CI Mode", it generates a **synthetic dataset** with N=50 subjects and ~500 taxa to demonstrate the pipeline's logic.

2. **Data Ingestion & Merging (T011d)**:
   - Filters for complete records.
   - Merges microbiome and serology data into `cleared_with_diversity.csv`.
   - Converts BIOM format to CSV if necessary.

3. **Preprocessing (T020c, T021, T020a)**:
   - Calculates Shannon diversity.
   - Log-transforms titers.
   - Applies zero-replacement (pseudo-count 1e-6) and CLR transformation.

4. **Correlation Analysis (T032)**:
   - Runs **Permutation-based Spearman correlation** for each taxon.
   - Applies Benjamini-Hochberg correction.
   - Selects features based on BH-corrected p-values (with variance pre-filter fallback).

5. **Predictive Modeling (T034d)**:
   - Trains a Random Forest with nested cross-validation.
   - Re-runs outer splits for each threshold in sensitivity analysis.

## Output Artifacts

After successful execution, check the `data/` directory:

- `processed/cleared_with_diversity.csv`: The clean, merged dataset.
- `results/correlation_results.json`: List of taxa with correlation stats and FDR.
- `results/model_metrics.json`: Cross-validation accuracy and feature importance.
- `results/lint_report.txt`: Linting output (if T039 ran).

## Verification

To verify the pipeline integrity:

```bash
pytest tests/ -v
```

This runs unit tests for:
- Data filtering logic.
- CLR transformation correctness.
- Nested CV isolation (ensuring no leakage).

## Troubleshooting

- **Error: "Insufficient Sample Size"**: The pipeline halted because the dataset (or synthetic fallback) had N < 50. This is a hard stop per SC-001.
- **Error: "No Real Data Found"**: T010 failed to find a real dataset. The project cannot proceed with scientific claims. Enable "CI Mode" for synthetic validation only.
- **Error: "Missing Columns"**: The input data lacks `titer_pre` or `titer_post`. The script will fall back to synthetic data generation if the verified URL is accessible but lacks schema.
- **Memory Error**: If running on a machine with < 4GB RAM, reduce the `N` parameter in the synthetic generator or stream the data (if using real large files).
- **Linting Error**: If `ruff` or `black` fails, the pipeline stops. This is a mandatory pre-requisite.
- **Error: "Significant Taxa Count Out of Range"**: T025 halted execution because the number of significant taxa was outside the expected range (for real data). This indicates a potential failure of the hypothesis or data quality.

## Next Steps

- **Scientific Interpretation**: Review `correlation_results.json` for significant taxa (FDR < 0.05).
- **Sensitivity Analysis**: Run the pipeline with different responder thresholds (e.g., 3-fold vs 4-fold rise) to test stability.
- **Real Data Integration**: Replace the synthetic generator in `code/ingestion.py` with a parser for the actual NCBI SRA study once a verified open-source dataset is identified.
- **Success Criteria**: Note that for synthetic data, success is defined as "Code Correctness" (no errors, no leakage), while for real data, success is defined as ">60% accuracy".