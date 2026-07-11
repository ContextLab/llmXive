# Quickstart: llmXive follow-up: extending "Wan-Streamer v0.1"

## Prerequisites

- Python 3.11+
- Access to Wan-Streamer v0.1 training logs (local directory) OR internet access to load `carnival13/video_conversation_v1`.
- Sufficient RAM available (for CI runner simulation).

## Installation

1.  **Clone the repository** (or navigate to the project directory).
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins `torch` to a CPU-only version to ensure compatibility with the CI runner.*

## Data Preparation

1.  **Place Wan-Streamer v0.1 logs** in `data/raw/`.
    - Ensure logs contain latent vectors, semantic/prosodic features, and turn-taking metadata.
2.  **Run the extraction script**:
    ```bash
    python code/data/extract_logs.py --input data/raw/ --output data/processed/extracted_latents.parquet
    ```
    - This script filters for interruptions/pauses, samples the data (stratified), and outputs a Parquet file.
3.  **Validate the data against contracts**:
    ```bash
    python code/data/validate_logs.py --input data/processed/extracted_latents.parquet --schema contracts/latents.schema.yaml
    ```
    - Checks for schema compliance and non-null values against the defined contract.

## Training the Estimator

1.  **Run the training script**:
    ```bash
    python code/models/train_estimator.py --data data/processed/extracted_latents.parquet --output data/checkpoints/gru_estimator.pth
    ```
    - Trains a lightweight GRU on CPU.
    - Logs MSE and correlation metrics to the console.
2.  **Update State**:
    ```bash
    python code/data/update_state.py --artifact data/checkpoints/gru_estimator.pth
    ```
    - Computes hash and updates `state.yaml` (Task T050).

## Running the Hybrid Simulation

1.  **Run the hybrid inference pipeline**:
    ```bash
    python code/inference/hybrid_pipeline.py --model data/checkpoints/gru_estimator.pth --data data/processed/extracted_latents.parquet --output data/processed/hybrid_predictions.parquet
    ```
    - Simulates skipping flow-matching steps based on predictions.
    - Falls back to full solver for high uncertainty.

## Evaluation & Statistical Testing

1.  **Compute metrics**:
    ```bash
    python code/inference/metrics.py --predictions data/processed/hybrid_predictions.parquet --output data/processed/hybrid_metrics.parquet
    ```
2.  **Run statistical tests**:
    ```bash
    python code/stats/significance_test.py --metrics data/processed/hybrid_metrics.parquet
    python code/stats/equivalence_test.py --metrics data/processed/hybrid_metrics.parquet
    ```
    - Outputs p-values for latency reduction (stratified bootstrap) and quality equivalence (TOST).
3.  **Update State**:
    ```bash
    python code/data/update_state.py --artifact data/processed/hybrid_metrics.parquet
    ```

## Troubleshooting

- **Memory Error**: If `RuntimeError: CUDA out of memory` appears, ensure `torch` is installed in CPU-only mode and no GPU flags are passed.
- **Data Missing**: If the extraction script fails, verify that `data/raw/` contains the expected log files. If missing, the script will automatically load the fallback dataset `carnival13/video_conversation_v1`.
- **Statistical Failure**: If TOST fails to reject the null hypothesis, the quality degradation may exceed the predefined threshold. Check the `fid_degradation_pct` in the metrics.
