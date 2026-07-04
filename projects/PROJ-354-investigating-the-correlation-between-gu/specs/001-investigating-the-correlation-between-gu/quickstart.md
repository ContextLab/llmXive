# Quickstart: Investigating the Correlation Between Gut Microbiome Composition and Cognitive Function in Aging Using UK Biobank Data

## Prerequisites

*   Python 3.10+
*   Access to UK Biobank data (credentials or local files).
*   7 GB RAM, 14 GB disk space.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd <repo-path>
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

4.  **Prepare Data**:
    *   If you have UK Biobank credentials, configure the `config.py` with your credentials.
    *   If using local files, place `microbiome_data.parquet` and `cognitive_data.parquet` in `data/raw/`.
    *   **Note**: The `# Verified datasets` block does not provide a direct URL for UK Biobank data. You must obtain this data via the official UK Biobank application or provide it manually.

## Running the Pipeline

1.  **Download and Preprocess**:
    ```bash
    python code/download.py
    python code/preprocess.py
    ```
    *This will filter participants, apply ILR transformation, and save processed data to `data/processed/`.*

2.  **Run Statistical Analysis**:
    ```bash
    python code/analysis.py
    ```
    *This will fit linear models, apply BH correction, and save results to `results/associations/`.*

3.  **Generate Visualizations**:
    ```bash
    python code/visualize.py
    ```
    *This will generate Manhattan plots and save them to `results/plots/`.*

4.  **Run Tests**:
    ```bash
    pytest tests/
    ```

## Output

*   `results/associations/association_results.parquet`: Contains all association statistics.
*   `results/plots/manhattan_plot.png`: Visualization of -log10(p-values).
*   `results/sensitivity/`: Contains sensitivity analysis outputs.

## Troubleshooting

*   **Data Missing**: If the pipeline fails due to missing data, ensure you have provided the UK Biobank data files or credentials.
*   **Memory Error**: If you encounter memory errors, check that you are not loading the entire dataset at once. The code is designed to stream data, but ensure your environment has sufficient RAM.
*   **ILR Transformation Errors**: Ensure that zero counts are handled with a pseudocount (1e-6) before transformation.
