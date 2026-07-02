# Quickstart: Investigating Microbial Community Succession in Constructed Wetlands

## Prerequisites

*   Python 3.11+
*   Git
*   Access to GitHub Actions (for CI execution) or local environment.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-280-investigating-microbial-community-succes
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
    *Note: `requirements.txt` pins `scikit-bio`, `networkx`, `pandas`, `scipy`, `statsmodels`.*

## Configuration

1.  **Setup Dataset IDs**:
    Create `data/config/dataset_ids.json`.
    *   *Note*: As no verified 16S wetland dataset URL is available in the current list, this file will initially contain placeholder IDs. The pipeline will generate synthetic data for demonstration.
    ```json
    {
      "dataset_ids": ["placeholder-wetland-001"]
    }
    ```

2.  **Verify Checksums**:
    Ensure `state/projects/PROJ-280-investigating-microbial-community-succes.yaml` is initialized with expected checksums (if real data were present).

## Running the Pipeline

Execute the full pipeline sequentially:

```bash
# 1. Retrieve (or generate synthetic) data
python code/01_retrieve_data.py

# 2. Preprocess (filter, subsample)
python code/02_preprocess.py

# 3. Diversity & PERMANOVA
python code/03_diversity.py

# 4. Network Construction
python code/04_network.py

# 5. Correlation & Regression
python code/05_correlation.py
```

## Expected Outputs

*   `data/processed/filtered_counts.biom` (or `.csv`)
*   `data/processed/metadata_filtered.csv`
*   `data/results/diversity_stats.csv`
*   `data/results/permanova_results.csv`
*   `data/results/network_edges.csv`
*   `data/results/correlation_results.csv`

## Troubleshooting

* **Memory Error**: Ensure `code/02_preprocess.py` is subsampling to [deferred] reads.
*   **Under-determined Network**: If `n_samples < n_taxa`, check logs for the 'under-determined' flag.
*   **Missing Data**: If no samples have N/P metrics, check `data/config/dataset_ids.json` or the synthetic generator logic.
