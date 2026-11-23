# Quickstart: Predicting Avian Foraging Guilds from Public eBird Data and Land Cover Maps

## Prerequisites

- Python 3.11+
- `pip`
- ~15 GB disk space (for raw data and intermediates)
- ~7 GB RAM

## Installation

1.  Clone the repository and navigate to the project directory.
2.  Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Pipeline

Execute the full pipeline using the orchestration script:

```bash
bash code/scripts/run_pipeline.sh
```

**Or run steps individually:**

1.  **Download Data**:
    ```bash
    python code/data/download_ebd.py
    python code/data/download_guild_source.py
    ```
2.  **Select Top Species**:
    ```bash
    python code/data/load_and_count.py
    python code/data/select_top_species.py
    ```
3.  **Process Land Cover**:
    ```bash
    python code/data/calculate_100m_buffers.py
    python code/data/join_guild_labels.py
    python code/data/write_merged_observations.py
    ```
4.  **Aggregate & Transform**:
    ```bash
    python code/data/aggregate.py
    python code/data/transform_clr.py
    ```
5.  **Train & Validate**:
    ```bash
    python code/models/train.py
    python code/models/stratified_permutation.py
    ```
6.  **Visualize**:
    ```bash
    python code/viz/generate_plots.py
    ```

## Expected Outputs

- `data/processed/merged_observations.csv`: Filtered and merged dataset.
- `data/processed/species_profiles.csv`: Aggregated and CLR-transformed data for training.
- `models/logistic_regression.pkl`: Trained model.
- `models/training_metrics.json`: Balanced accuracy and F1 scores.
- `models/null_distribution.npy`: Permutation test results.
- `viz/confusion_matrix.png`, `viz/feature_importance.png`, `viz/habitat_map.png`.

## Troubleshooting

- **FileNotFoundError (guild_source.csv)**: Ensure `download_guild_source.py` has run.
- **Memory Error**: The pipeline streams data. Ensure no other heavy processes are running.
- **Rasterio Errors**: Verify the NLCD ZIP was downloaded correctly and extracted.
- **Buffer Validation Error**: Ensure the 100m parameter is correctly set in `calculate_100m_buffers.py`.
