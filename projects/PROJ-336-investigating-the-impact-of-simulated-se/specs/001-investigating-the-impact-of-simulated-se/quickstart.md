# Quickstart: Investigating the Impact of Simulated Sensory Deprivation on Resting-State Brain Network Dynamics

## Prerequisites

-   Python 3.11+
-   Git
-   Access to GitHub Actions (for running the pipeline)
-   Internet connection (to download datasets)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-org/your-repo.git
    cd your-repo
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

The pipeline is designed to run on GitHub Actions. To run locally (for development):

1.  **Download and preprocess data**:
    ```bash
    python src/data/download.py --dataset ds001770
    python src/data/preprocess.py --atlas schaefer400
    python src/data/quality_check.py --fd_threshold 0.5 --volume_threshold 0.10
    ```
    *Note: `quality_check.py` calculates `motion_fd_mean` and `motion_fd_max` from residual motion parameters.*

2.  **Compute connectivity and metrics**:
    ```bash
    python src/analysis/connectivity.py
    python src/analysis/metrics.py
    ```

3.  **Run statistical analysis**:
    ```bash
    python src/analysis/stats.py --n_permutations 1000
    ```

4.  **Generate visualizations**:
    ```bash
    python src/viz/plot_networks.py
    python src/viz/plot_metrics.py
    ```

## Output

-   **Preprocessed Data**: `data/preprocessed/`
-   **Connectivity Matrices**: `data/connectivity/`
-   **Network Metrics**: `results/metrics.csv`
-   **Statistical Results**: `results/stats.csv`
-   **Visualizations**: `results/plots/`

## Troubleshooting

-   **Dataset Download Fails**: Ensure you have internet access and the dataset is available on OpenNeuro.
-   **Dataset Lacks Labels**: If the dataset does not contain 'deprivation' or 'control' task labels, the pipeline will halt with an error.
-   **Memory Errors**: Reduce the number of subjects or ROIs. The pipeline is designed for n=20 subjects and 400 ROIs.
-   **Runtime Errors**: Check `logs/pipeline.log` for detailed error messages.

## License

This project is licensed under the MIT License. See `LICENSE` for details.