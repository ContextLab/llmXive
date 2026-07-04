# Quickstart: Investigating the Correlation Between Gut Microbiome Composition and Sleep Quality

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- Git

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-org/your-repo.git
    cd your-repo/projects/PROJ-087-investigating-the-correlation-between-gu
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

**IMPORTANT**: This pipeline is currently **BLOCKED** due to missing data sources. It will halt with a clear error message if the required dataset is not found.

1.  **Data Feasibility Check**:
    ```bash
    python code/src/main.py --step check_data
    ```
    *Note: This step verifies if a valid dataset (OTU + Sleep) exists in the verified list. If not, the pipeline halts.*

2.  **Download and preprocess data** (only if check passes):
    ```bash
    python code/src/main.py --step ingest
    ```
    *Note: This step will attempt to fetch the American Gut Project data. If the dataset is unavailable, it will fail gracefully.*

3.  **Compute diversity and correlations**:
    ```bash
    python code/src/main.py --step analyze
    ```

4.  **Generate visualizations**:
    ```bash
    python code/src/main.py --step viz
    ```

5.  **Run the full pipeline**:
    ```bash
    python code/src/main.py --step all
    ```

## Output

- **Data**: `data/processed/analysis_ready.csv`
- **Results**: `data/processed/correlation_results.csv`
- **Plots**: `data/processed/plots/`

## Troubleshooting

- **Dataset Unavailable**: If the AGP data cannot be downloaded, check the network connection and the status of the AGP repository. **If the dataset is not in the verified list, the pipeline will halt with a clear error message.**
- **Memory Issues**: If the dataset is too large, the pipeline will attempt to process it in chunks. If it still fails, consider reducing the dataset size or increasing available RAM (though the plan targets the 7 GB limit).
- **Missing Variables**: If the dataset lacks required variables (e.g., sleep metrics), the pipeline will halt with an error indicating the missing fields.
- **Sequencing Depth**: If diversity indices are unstable, ensure the rarefaction step is enabled in the `diversity.py` script.

## Testing

Run the test suite to verify the pipeline:
```bash
pytest tests/
```

## Reproducibility

To ensure reproducibility, run the pipeline on a clean environment and compare the output file hashes with the expected values stored in `state/projects/PROJ-087-investigating-the-correlation-between-gu.yaml`.