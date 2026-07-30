# Quickstart: Evaluating the Robustness of LLM-Generated Code to Input Perturbations

## Prerequisites

- Python 3.11+
- GB RAM available (for CPU inference)
- Sufficient disk space
- Access to HuggingFace Hub (for dataset and model download)

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `bitsandbytes` is required for 4-bit quantization. If using CPU, ensure the CPU-only version is installed or the library is configured for CPU.*

## Data Download

Run the data download script to fetch HumanEval:
```bash
python code/data/download.py
```
This will save the dataset to `data/raw/humaneval.parquet`.

## Running the Pipeline

The pipeline is executed in stages. You can run the full pipeline or individual stages.

### 1. Generate Perturbations
```bash
python code/data/perturbation.py --output data/processed/perturbation_candidates_raw.json
```
This generates candidates and scores them.

### 2. Filter Perturbations
```bash
python code/data/filter.py --input data/processed/perturbation_candidates_raw.json --threshold 0.95 --output data/processed/perturbation_candidates.json
```

### 3. Run Inference
```bash
python code/model/inference.py --input data/processed/perturbation_candidates.json --output data/processed/inference_logs.json
```
*Note: This step may take several hours. If it fails due to OOM, the system will attempt to offload to a GPU (if configured).*

### 4. Analyze Results
```bash
python code/analysis/stats.py --input data/processed/inference_logs.json --output data/processed/results.csv
```

## Verification

To verify the pipeline:
1.  Check that `data/processed/inference_logs.json` exists and contains entries for `original` and `perturbed` prompts.
2.  Run the unit tests:
    ```bash
    pytest tests/unit/
    ```
3.  Run the integration test:
    ```bash
    pytest tests/integration/
    ```

## Troubleshooting

- **OOM Error**: If you encounter Out-Of-Memory errors, ensure you are using the 4-bit quantized model. If the issue persists, the system is designed to offload to a GPU.
- **Timeout Errors**: The sandbox has a timeout. If code execution is slow, it will be logged as a timeout error.
- **Semantic Similarity**: If no perturbations pass a high-confidence threshold, the raw log will be empty. Check the `similarity_score` distribution in `perturbation_candidates_raw.json`.