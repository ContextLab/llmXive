# Quickstart: Quantifying Composition-Dependent Grain Boundary Segregation in BCC Alloys

## Prerequisites

*   Python 3.11+
*   `pip` or `conda`
*   Git

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-448-quantifying-composition-dependent-grain-
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

The pipeline is executed via the CLI:

```bash
python code/cli/main.py run --system Fe-Cr-Mo --temp-range 500 900
```

### Expected Output

*   `data/processed/segregation_profiles.csv`: Contains the computed profiles (with injected interaction terms).
*   `data/processed/regression_results.json`: Contains the fitted model coefficients and validation metrics.
*   `data/data_manifest.json`: Tracks data sources, checksums, and content hashes.
*   `figures/`: Heatmaps of segregation energy vs. composition.

## Validation

To verify the pipeline:

```bash
pytest tests/
```

This runs unit tests for the McLean calculation and integration tests for the full pipeline, including the **Interaction Injection Mechanism** to ensure non-linear terms are detected.

## Troubleshooting

*   **Missing Data**: If `data/processed/` is empty, check `data_manifest.json` for source errors.
*   **Memory Errors**: The pipeline is designed for <7 GB RAM. If errors occur, reduce the temperature grid resolution.
*   **No Interaction Detected**: If the regression model fails to detect the injected interaction term, check the `interaction_coefficient_truth` in the generated data and ensure the regression model includes interaction terms.