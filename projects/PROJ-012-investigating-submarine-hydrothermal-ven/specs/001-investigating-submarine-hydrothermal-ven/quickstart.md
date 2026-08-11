# Quickstart: Submarine Hydrothermal Vent Microbial Communities as Indicators of Ocean Acidification

## Prerequisites

-   Python 3.11+
-   `pip` (Python package installer)
-   Git (for cloning the repository)
-   (Optional) `q2cli` if using QIIME2 for specific taxonomic processing (optional, can use Biopython for basic parsing).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-012-investigating-submarine-hydrothermal-ven
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

## Running the Pipeline

### 1. Prepare Data

Place your raw data in the `data/raw/` directory:
-   `sequences.fastq` (or `.fq`)
-   `ph_sensors.csv` (columns: `timestamp`, `sample_id`, `pH_value`)
-   `temp_sensors.csv` (columns: `timestamp`, `sample_id`, `temp_value`)

*Note: If you do not have real data, run the `generate_synthetic_data.py` script (if provided) to create a mock dataset for testing. **Warning**: Synthetic data is for pipeline validation only and cannot be used for scientific claims.*

### 2. Execute the Pipeline

Run the main script:
```bash
python code/main.py --input-dir data/raw --output-dir data/processed --config config.yaml
```

### 3. Review Outputs

-   **Analysis Table**: `data/processed/analysis_results.csv` (contains diversity, pH, model stats).
-   **Logs**: `data/processed/rejected_samples.log` (samples excluded due to temporal mismatch or pH outliers).
-   **Visualizations**: `data/processed/plots/` (PCA/NMDS plots, diversity vs pH scatter plots).

### 4. Verify Results

Check the `analysis_results.csv` for the `flag` column. Look for:
-   `associational_only`: Confirms the study is non-causal.
-   `low_power`: Indicates sample size was too small for LME.
-   `heteroscedastic` or `dispersion_confounded`: Indicates PERMANOVA may be confounded by unequal dispersions.
-   `synthetic_data`: Indicates the analysis used generated data (not real observations).

## Troubleshooting

-   **Error: "No pH data found"**: Ensure `ph_sensors.csv` has a `sample_id` that matches the FASTQ headers.
-   **Error: "Memory limit exceeded"**: The dataset is too large. Reduce the `rarefaction_depth` in `config.yaml` or subsample the FASTQ file.
-   **Error: "VIF > 5"**: Temperature and pH are highly correlated. The pipeline will flag this, but you may need to remove one variable from the model.
-   **Error: "Dispersion Confounded"**: The `betadisper` test was significant. The results rely on PERMDISP or dbRDA, not PERMANOVA F-statistic.