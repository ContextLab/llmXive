# Quickstart: llmXive follow-up: extending "TransitLM"

## Prerequisites

*   Python 3.11+
*   Access to Hugging Face Hub (for dataset download).
*   (Optional) None (No GPU offload required).

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r projects/PROJ-978-llmxive-follow-up-extending-transitlm-a/code/requirements.txt
    ```

## Data Preparation

1.  **Download and Preprocess**:
    Run the data download and preprocessing script. This will fetch the TransitLM dataset, map stations to cities, filter for the four target cities, build the adjacency graph (with transition frequencies), generate valid path sets, and stratify the routes.
    ```bash
    python projects/PROJ-978-llmxive-follow-up-extending-transitlm-a/code/data/download.py
    python projects/PROJ-978-llmxive-follow-up-extending-transitlm-a/code/data/preprocess.py
    ```
    *Output*: `data/processed/` directory containing stratified routes, graphs, and city mappings.

## Running the Analysis

1.  **Execute the Main Pipeline**:
    This script runs the lightweight model (deterministic lookup), attempts the baseline LLM inference (CPU only, with timeout handling), performs the dual-method survival and chi-squared analysis, and generates the report.
    ```bash
    python projects/PROJ-978-llmxive-follow-up-extending-transitlm-a/code/main.py
    ```
    *Note*: If the baseline model exceeds the 6-hour runtime or 7GB RAM limit, the script will record the failure and proceed with the lightweight model analysis.

2.  **View Results**:
    The results will be saved in `data/analysis/`.
    *   `inflection_points.json`: Contains the identified cognitive horizon (if found).
    *   `survival_curves.csv`: Data for plotting KM curves.
    *   `profiling_report.json`: CPU memory and time metrics.

## Testing

Run the unit and contract tests to verify data integrity and model behavior:
```bash
pytest projects/PROJ-978-llmxive-follow-up-extending-transitlm-a/code/tests/
```

## Troubleshooting

*   **City Mapping Error**: If the city identification step fails, check the `data/processed/city_mapping.json` file. The mapping is derived from station name patterns; if a city is missing, the mapping file may need manual update.
*   **Baseline Timeout**: If the baseline model times out, the results will reflect "timeout/infeasible" for the baseline. This is an expected outcome if the model is too large for the CPU runner.
*   **Data Sparsity**: If a city has no "long-haul" routes, the stratification for that city will be skipped. Check `data/processed/stratified_routes.parquet` for row counts.