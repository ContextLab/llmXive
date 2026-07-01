# Quickstart: Predicting Species‑Specific Responses to Climate Change from Museum Collection Data

## Prerequisites

*   R 4.3+
*   Access to WorldClim v2 data (downloaded to `data/raw/worldclim/`)
*   Internet access for GBIF API calls
*   (Optional) Phylogenetic tree file (Newick format) for PGLS

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment (optional)** or use system R.
3.  **Install R dependencies**:
    ```bash
    # If using renv
    R -e "renv::init()"
    R -e "renv::restore()"
    
    # Or manual installation
    R -e "install.packages(c('rgbif', 'raster', 'sf', 'ggplot2', 'dplyr', 'tidyr', 'caper', 'phylolm', 'pwr', 'tibble', 'lubridate', 'here', 'testthat'))"
    ```

## Configuration

1.  **Prepare WorldClim Data**:
    Ensure the following files exist in `data/raw/worldclim/`:
    *   `bio1_1970-2000.tif`
    *   `bio12_1970-2000.tif`
    *   `bio1_1991-2020.tif`
    *   `bio12_1991-2020.tif`
2.  **Define Species List**:
    Create `data/species_list.csv` with columns: `species_name`, `taxonomic_group`.
3.  **Phylogenetic Tree (Optional)**:
    Place `data/phylogeny.tre` in the data directory if PGLS is to be used.

## Running the Pipeline

Execute the main pipeline script:

```bash
Rscript code/main_pipeline.R --species data/species_list.csv --output results/
```

### Steps Executed
1.  **Fetch**: Downloads GBIF records for each species (FR-001, FR-002) via `rgbif`.
2.  **Extract**: Extracts climate values from WorldClim (FR-003, FR-006) via `raster`.
3.  **Compute**: Calculates centroids and niche shifts (FR-004, FR-005).
4.  **Regional Warming**: Computes ΔT from static historical envelopes (FR-006).
5.  **Sensitivity**: Runs subsampling for variance estimation (FR-009).
6.  **Power Analysis**: Computes margin of error (FR-012).
7.  **Analyze**: Runs PGLS regression (FR-007, FR-011).
8.  **Plot**: Generates scatter plots (FR-008).
9.  **Log**: Writes comprehensive logs to `logs/pipeline.log`.

## Verification

*   Check `results/regression_summary.csv` for regression outputs.
*   Check `results/power_analysis_report.csv` for margin of error.
*   Verify `results/plots/niche_shift_vs_warming.png` (1200x800px).
*   Inspect `logs/pipeline.log` for warnings and errors.

## Troubleshooting

*   **GBIF API Errors**: Ensure network connectivity. The script retries on 429/503.
*   **Missing Climate Data**: Verify WorldClim files are in `data/raw/worldclim/` and have the correct names.
*   **Memory Errors**: The script processes species in batches. Reduce the number of species in the input list if RAM is exceeded.
*   **Phylogenetic Tree Missing**: If no tree is provided, the script will fall back to WLS (Weighted Least Squares) and log a warning.