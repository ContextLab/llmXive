# Quickstart: Testing the Equivalence Principle with Satellite Laser Ranging

## Prerequisites

*   Python 3.11+
*   Git
*   Access to a Linux environment (recommended for SLR data processing).
*   **Note**: A verified source for LAGEOS/Etalon SLR data and composition metadata is currently **missing** from the project's verified dataset block. The pipeline will **fail** with a `DataUnavailableError` until a verified URL is added to the `# Verified datasets` block.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd <project-dir>
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

## Data Setup

1.  **Verify Data Availability**:
    *   Check the `# Verified datasets` block in `research.md`. If no valid URL exists for LAGEOS/Etalon SLR data, the pipeline cannot run.
    *   If a verified URL is available, run:
        ```bash
        python code/data/ingestion.py --satellites LAGEOS-1,LAGEOS-2,ETALON-1,ETALON-2,STARLETTE
        ```
    *   **Manual Data**: If you have manually downloaded data from a verified source (e.g., a verified HuggingFace mirror), place it in `data/raw/`. Ensure filenames match the pattern `slr_{satellite_id}_*.parquet`.

2.  **Verify Data**:
    *   Check that `data/raw/` contains files with ≥ 500 points per satellite.
    *   Run the checksum validation:
        ```bash
        python code/utils/validate_data.py --dir data/raw
        ```

## Running the Pipeline

Execute the full analysis pipeline:

```bash
python code/main.py
```

This will:
1.  Ingest and preprocess data.
2.  Perform **joint** orbit determination for satellite pairs.
3.  Calculate the Eötvös parameter ($\\eta$) and confidence intervals.
4.  Run sensitivity analysis with multiple geopotential models.
5.  Generate a diagnostic report in `data/results/report.html`.

## Verification

1.  **Check Outputs**:
    *   `data/results/eotvos_results.csv`: Contains the final $\\eta$ estimates.
    *   `data/results/orbit_solutions/`: Contains JSON files for each satellite pair's joint fit.
    *   `data/results/report.html`: Visual summary of the analysis.

2.  **Run Tests**:
    ```bash
    pytest code/tests/ -v
    ```

3.  **Reproducibility**:
    *   Ensure `random_seed` in `config.py` is pinned.
    *   Re-run the pipeline; outputs should match exactly (within floating-point tolerance).

## Troubleshooting

*   **"DataUnavailableError"**: The pipeline found no verified source for the required satellites in the `# Verified datasets` block. You must add a verified URL to proceed.
*   **"Convergence failed"**: Check `data/results/orbit_solutions/` for the `converged` flag. If false, the solver may have hit the iteration limit. Adjust tolerance in `config.py`.
*   **"Memory Error"**: Reduce the data subset size in `config.py` or run on a machine with more RAM.
