# Quickstart: The Impact of Network Centrality on Neural Synchrony in Resting-State fMRI

## Prerequisites

- Python 3.11 or higher.
- Git.
- Access to the Hugging Face datasets library (for data fetching).
- A GitHub Actions runner or a local machine with ≥14 GB disk space and ≥7 GB RAM.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-268-the-impact-of-network-centrality-on-neur
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

## Running the Pipeline

The pipeline is executed as a sequence of scripts. Run them in order:

1.  **Download Data**:
    ```bash
    python code/download_data.py --subjects 10
    ```
    *Note: This will attempt to fetch data from the verified source. If the source is a Parquet file, it will load the data into memory.*

2.  **Preprocess and Generate Matrices**:
    ```bash
    python code/preprocess.py --atlas schaefer400
    ```
    *This step generates the SC and FC matrices for each subject. If raw data is unavailable, it switches to "Pre-computed Mode".*

3.  **Compute Metrics**:
    ```bash
    python code/compute_metrics.py
    ```
    *This step calculates centrality and synchrony for all nodes.*

4.  **Run Analysis**:
    ```bash
    python code/analyze.py --permutations 1000
    ```
    *This step performs the Spearman correlation and **subject-level** permutation test.*

5.  **Generate Visualizations**:
    ```bash
    python code/visualize.py
    ```
    *This step creates the scatter plots and saves them to `data/results/`.*

## Verifying Results

- Check `data/results/analysis_results.json` for the correlation coefficients and p-values.
- Check `data/results/processing_summary.json` for the subject processing count (e.g., 9/10).
- Check `data/results/` for the generated scatter plots.
- Verify that the `subject_log.txt` contains at least 10 valid subjects (or a "Data Gap" error if less).

## Troubleshooting

- **Data Download Failed**: Ensure you have an internet connection and that the Hugging Face token is set (if required). Check the `data/raw/` directory for partial downloads.
- **Disk Space Error**: The pipeline will automatically delete raw NIfTI files after matrix generation. If you still run out of space, the pipeline will halt with a "Storage Limit" error.
- **Memory Error**: The pipeline is designed to run within 7 GB RAM. If you encounter memory errors, ensure no other heavy applications are running.
- **Data Gap**: If the pipeline halts with "Data Gap", the verified source lacks raw dMRI/fMRI. The study will proceed only if pre-computed matrices are available in the source.
