# Quickstart: Assessing the Predictive Power of Plant Functional Traits for Species Distribution Models

## Prerequisites

-   Python 3.11+
-   `pip` or `conda`
-   Access to GitHub Actions (for CI execution) or a local CPU environment with 7GB+ RAM.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-478-assessing-the-predictive-power-of-plant-/code/
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Data Setup

1.  **Download Raw Data**:
    -   **GBIF**: Run `python src/data/fetch_gbif.py` to query the GBIF API for specific species.
    -   **WorldClim**: Run `python src/data/fetch_climate.py` to download v2.1 'bioclim' layers (requires internet).
    -   **TRY**: Run `python src/data/fetch_traits.py` to retrieve trait data (may require API key or manual upload).

2.  **Verify Data**:
    -   Check `data/metadata/provenance.yaml` for checksums, source versions, and the 'Power Analysis' result (N species).

## Running the Pipeline

### Option 1: Full Pipeline (CPU Only)
Runs the entire LOSO cycle with Trait Imputation, LMM analysis, and sensitivity analysis.
```bash
python main.py
```

### Option 2: Single Species Test (Debug)
Run for one species (e.g., *Helianthus annuus*) to verify the baseline.
```bash
python main.py --species "Helianthus annuus" --mode baseline
```

### Option 3: LOSO Validation Only
Run the cross-species validation without the final statistical aggregation.
```bash
python main.py --mode loso
```

## Output

-   **Results**: `results/model_results.json` (per-species metrics with `trait_imputed` flag).
-   **Statistics**: `results/stats_report.json` (LMM results, variance components, p-values).
-   **Sensitivity**: `results/sensitivity_analysis.json` (threshold sweep, direction consistency).
-   **Logs**: `logs/pipeline.log` (detailed execution steps, warnings, exclusions, power analysis result).

## Troubleshooting

-   **RAM Error**: The pipeline processes species sequentially. If RAM is still exceeded, reduce `n_estimators` in `src/modeling/train_rf.py` or reduce the background density (e.g., 1 point per 200 km²).
-   **Missing Traits**: Check `data/processed/trait_profile.csv` for missing values. Species with missing traits are excluded from the trait-augmented analysis.
-   **GBIF No Records**: If a species has <100 records after thinning, it is skipped. If total N < 30, the workflow halts with 'Power Insufficient'.
-   **WorldClim/TRY Unreachable**: Check `data/metadata/provenance.yaml` for version errors. The workflow halts if the specific versioned release cannot be fetched.
-   **Circularity Warning**: If the pipeline detects that test species traits are being used directly (not imputed), it will abort with a "Circular Validation Detected" error.