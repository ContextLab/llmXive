# Quickstart: llmXive Follow-up: Extending PerceptionDLM Parallel Region Perception

## Prerequisites

*   Python 3.11+
*   Access to a HuggingFace account (for model downloads).
*   GitHub Actions runner (or local machine with adequate RAM).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-833-llmxive-follow-up-extending-perceptiondl/code
    ```

2.  **Create virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins `torch` to CPU-only version.*

## Running the Pipeline

### 1. Generate Synthetic Dataset
Run the synthetic generator to create test images with varying numbers of regions, including configurations with 30 and 50 regions.
```bash
python -m synthetic.generator --region-counts [low, medium, high ranges] --samples-per-count 50
```
*Output*: `data/synthetic/` directory with images and JSON annotations.

### 2. Execute Inference
Run both parallel and sequential modes.
```bash
python -m main --mode all --max-memory 7000
```
*   `--mode all`: Runs both parallel and sequential.
*   `--max-memory`: Sets the memory limit (in MB) to prevent OOM.

*Output*: `data/processed/inference_results.json`.

### 3. Analyze and Visualize
Generate the degradation curve and Pareto frontier.
```bash
python -m analysis.regression --input data/processed/inference_results.json --output data/processed/regression_data.csv
python -m analysis.plotting --input data/processed/regression_data.csv --output data/processed/pareto_frontier.png
```
*Output*: `data/processed/pareto_frontier.png` and `regression_data.csv`.

## Validation

To verify the synthetic data generation:
```bash
python -m synthetic.validator --input data/synthetic/
```
Expected output: `All samples valid: 0 overlaps detected.`

To verify metrics:
```bash
python -m metrics.consistency --check
```
Expected output: `Geometric consistency metric logic verified.`