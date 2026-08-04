# Quickstart: Non-Neural Approximation of VLA Priors

## Prerequisites

- Python 3.11+
- `pip`
- Access to HuggingFace (for dataset download)
- Sufficient RAM (recommended for full dataset, streaming enabled for lower)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-962-llmxive-follow-up-extending-qwen-vla-uni
    ```

2.  **Create and activate virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `code/requirements.txt` explicitly pins `torch` to a CPU-only version.*

## Data Download

The pipeline automatically downloads the Qwen-VLA dataset from the verified HuggingFace source. No manual download is required.

```bash
# Run the ingestion script (automates download and validation)
python code/01_ingest_cluster.py --download
```
*Note: The script verifies the checksum of the downloaded file against the manifest in `state/`.*

## Execution Pipeline

### Step 1: Ingest and Cluster
Extracts kinematic features (statistical summaries) and clusters trajectories.
```bash
python code/01_ingest_cluster.py
```
*Output*: `data/processed/cluster_assignments.csv`, `data/processed/kinematic_features.csv`

### Step 2: Train Models
Trains Decision Trees/GMMs for each cluster.
```bash
python code/02_train_models.py
```
*Output*: `data/models/cluster_*.pkl`

### Step 3: Inference
Generates trajectories for new prompts.
```bash
python code/03_inference.py --prompts "Pick up the red block", "Navigate to the table"
```
*Output*: `data/processed/generated_trajectories.json`

### Step 4: Simulation & Evaluation
Runs trajectories in PyBullet and generates statistics.
```bash
python code/04_simulate_eval.py
```
*Output*: `data/results/simulation_results.csv`, `data/results/statistical_report.txt`

## Testing

Run the full test suite to verify edge cases (OOD prompts, simulation crashes).
```bash
pytest code/tests/ -v
```
*Expected Tests*:
- `test_ood.py`: Verifies handling of prompts outside the training distribution.
- `test_simulation.py`: Verifies that simulation crashes are caught and recorded as failures.
- `test_ingest.py`: Verifies data integrity and checksum validation.

## Expected Results

- **Clustering**: Up to 50 clusters (adaptive based on silhouette score).
- **Inference**: ≤ 2 seconds per prompt on CPU.
- **Evaluation**: Paired t-test results comparing non-neural model vs. random baseline.
- **Fidelity Report**: Percentage of VLA trajectory characteristics preserved (based on simulation success).

## Troubleshooting

- **OOM Error**: The script uses `streaming=True` by default. If OOM persists, reduce the sample size in `config.yaml`.
- **CUDA Error**: This project is **CPU-only**. If you see CUDA errors, ensure you are not running a GPU version of PyTorch. Use `pip install torch --index-url https://download.pytorch.org/whl/cpu`.
- **Simulation Crash**: The simulator catches errors and records them as "failure." Check `data/results/simulation_results.csv` for failure flags.
- **Code Hygiene**: Ensure `code/utils/` has no duplicate imports or unused variables (as per T039b requirement).

## Validation

To validate the pipeline:
1. Run the full pipeline from Step 1 to Step 4.
2. Verify that `data/results/simulation_results.csv` exists and contains non-empty rows.
3. Verify that `data/results/statistical_report.txt` contains p-values from the t-tests.
4. Check `code/tests/` for passing test results.
