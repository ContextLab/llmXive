# Quickstart: llmXive follow-up

## Prerequisites

*   Python 3.11+
*   Git
*   Access to GitHub Actions (for CI) or a local environment with ≥ 7 GB RAM.

## Installation

1.  **Clone the repository** and navigate to the project directory:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-964-llmxive-follow-up-extending-wan-streamer
    ```

2.  **Create a virtual environment**:
    ```bash
    cd projects/PROJ-964-llmxive-follow-up-extending-wan-streamer
    python -m venv venv
    source venv/bin/activate
    pip install -r code/requirements.txt
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: This installs CPU-only versions of PyTorch and other libraries.*

4.  **Dataset Version Pinning**: Ensure `code/config.py` contains the correct dataset revision hash for VoxCeleb2 (e.g., `revision: 'main'`) to guarantee reproducibility (Constitution Principle I).

2.  **Verify Datasets**:
    Ensure you have access to the data source.
    *   **Option A (Local Logs)**: Place Wan-Streamer v0.1 logs in `data/raw/`. **If these are missing, the system will exit with "Data Unavailable" (FR-022).**
    *   **Option B (Proxy)**: The system can use VoxCeleb2 for turn-taking labels *only if* the Wan-Streamer logs are present to provide latent trajectories.

1.  **Download Data**:
    *   If you have local Wan-Streamer logs, place them in `data/raw/wan_streamer_logs/`.
    *   If not, the system will automatically download **VoxCeleb2** from the verified HuggingFace source.
    ```bash
    python code/data/extract_latents.py --source voxceleb2
    ```
    *This script will generate `data/processed/extracted.parquet`.*

2.  **Validate Data**:
    ```bash
    python code/data/validate_sampling.py --input data/processed/extracted.parquet
    ```

The pipeline is executed sequentially via the `code/tasks/` modules.

1.  **Run Training**:
    ```bash
    python code/models/trainer.py --input data/processed/train.parquet --epochs [specified number of training epochs]
    ```
    *This will output `data/artifacts/model.pt`.*

2.  **Monitor Resources**:
    Ensure RAM usage stays within acceptable limits. If the process hangs or exceeds time limits, the script will automatically reduce the sample size (FR-014).

## Running the Simulation

1.  **Execute Hybrid Inference**:
    ```bash
    python code/inference/hybrid_sim.py --model data/artifacts/model.pt --data data/processed/val.parquet
    ```
    *This runs the hybrid pipeline with randomized counterfactuals and outputs `data/artifacts/simulation_metrics.parquet`.*

2.  **Run Statistical Tests**:
    ```bash
    python code/metrics/stats_tests.py --input data/artifacts/simulation_metrics.parquet
    ```
    *This performs TOST and bootstrap tests, outputting `data/artifacts/statistical_results.json`.*

## Validation & Reporting

1.  **Check Results**:
    Review `data/artifacts/statistical_results.json` for:
    *   Latency reduction (Target: ≥ 20%).
    *   FID degradation (Target: ≤ 5%).
    *   TOST p-values (Target: < 0.05).

2.  **Update State**:
    ```bash
    python code/utils/state_manager.py --update
    ```
    *This updates `state.yaml` with artifact hashes (FR-020).*

## Troubleshooting

*   **Out of Memory**: Reduce the `--sample-size` flag in `extract_latents.py` or `trainer.py`.
*   **Data Missing**: If Wan-Streamer logs are missing, the system defaults to VoxCeleb2. Check logs for "Fallback to VoxCeleb2" message.
*   **Training Timeout**: If training exceeds 6 hours, the script will fail with "Power Limitation" error. Reduce sample size and retry.
*   **Hypothesis Failure**: If Phase 0 (Preliminary Validation) reports a weak delta-FID correlation, the main experiment may be aborted or pivoted.