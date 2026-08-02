# Quickstart: Non-Neural Approximation of VLA Priors

## Prerequisites

*   Python 3.11+
*   Git
*   Access to HuggingFace (for dataset download)
*   ~15 GB disk space (for dataset and dependencies)

## Installation

1.  **Clone and Setup**
    ```bash
    git clone <repo-url>
    cd projects/PROJ-962-llmxive-follow-up-extending-qwen-vla-uni/code/
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

2.  **Verify Dependencies**
    ```bash
    python -c "import pybullet; import transformers; import sklearn; print('All dependencies OK')"
    ```

## Running the Pipeline

The pipeline is executed sequentially. Ensure you have sufficient disk space.

### Step 1: Ingest Data
```bash
python 01_ingest.py --dataset tencent/Hy-Embodied-0.5-VLA-Data
```
*Outputs*: `data/raw/hy_embodied.parquet`

### Step 2: Cluster Trajectories
```bash
python 02_cluster.py --k 50 --silhouette-threshold 0.25
```
*Outputs*: `data/processed/kinematic_features.feather`, `data/logs/clustering_report.txt`

### Step 3: Train Models
```bash
python 03_train.py --model-type conditional_gmm
```
*Note*: The `--model-type` is set to `conditional_gmm` to align with the corrected methodology (CGMM). Decision Trees are no longer supported.
*Outputs*: `data/models/cluster_*.pkl`

### Step 4: Simulate & Evaluate
```bash
python 05_simulate.py --prompts 100 --tasks grasp,navigate,place
```
*Outputs*: `data/results/simulation_logs.csv`

### Step 5: Generate Report
```bash
python 06_evaluate.py
```
*Outputs*: `data/results/final_report.md`, `data/results/statistical_tests.json`

## Testing

Run the unit tests:
```bash
pytest tests/ -v
```

Run the integration test (full pipeline on a small sample):
```bash
python -m pytest tests/integration/test_full_pipeline.py -v --sample-size=10
```

## Troubleshooting

*   **Memory Error**: If the pipeline crashes with OOM, enable streaming in `01_ingest.py` by setting `streaming=True` in the dataset loader.
*   **PyBullet Crash**: Ensure the robot URDF files are present in `data/assets/`. If the simulation fails, check `data/results/errors.log`.
*   **Dataset Missing**: Verify your HuggingFace token is set (`huggingface-cli login`) if the dataset is gated (though the specified URL is public).
*   **Model Type Error**: Ensure `--model-type` is set to `conditional_gmm`. The `decision_tree` option has been removed due to validity concerns.