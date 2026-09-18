# Quickstart: llmXive follow-up: extending "TriSplat: Simulation-Ready Feed-Forward 3D Scene Reconstruction"

## Prerequisites

-   Python 3.11+
-   2-core CPU (simulated GitHub Actions runner)
-   ~7 GB RAM
-   ~14 GB disk space (for dataset and temporary files)
-   Internet access (for dataset download)

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` pins all dependencies to ensure reproducibility.*

## Running the Pipeline

### Step 1: Download the Dataset
The pipeline will automatically download the RealEstate10K dataset if not present. To manually trigger download:
```bash
python code/cli.py --action download --dataset real_estate_10k --path data/raw
```

### Step 2: Run a Single Scene (Debug)
Test the pipeline on a single scene with views:
```bash
python code/cli.py \
  --scene_id "re10k_val_scene_001" \
  --view_count 3 \
  --resolution 320x240 \
  --timeout 1800 \
  --seed 42
```
*Output*: A `.obj` file and a JSON metrics file in `data/processed/results/`.

### Step 3: Run the Full Batch (50 Scenes)
Execute the full statistical evaluation:
```bash
python code/cli.py \
  --batch_size 50 \
  --view_counts 2 3 4 5 \
  --timeout 1800 \
  --seed 42 \
  --output data/processed/results/batch_results.json
```
*Note*: This will take up to 6 hours on a 2-core CPU runner.

### Step 4: Analyze Results
View the statistical summary and threshold identification:
```bash
python code/cli.py --action analyze --input data/processed/results/batch_results.json
```
*Output*: A report identifying the sparsity threshold and statistical significance (p-values).

## Expected Output Structure

```text
data/
├── raw/
│   └── test.tar.gz (and extracted shards)
└── processed/
    ├── results/
    │   ├── scene_001_views_2.json
    │   ├── scene_001_views_3.json
    │   ├── ...
    │   └── batch_results.json
    └── meshes/
        ├── scene_001_views_2.obj
        ├── scene_001_views_3.obj
        └── ...
```

## Troubleshooting

-   **OOM Error**: Ensure `--resolution 320x240` is set. If still failing, reduce `--batch_size` to 1.
-   **Non-Convergence**: Check `error_log` in the JSON output. The system will log "max_iter_reached" if the ray-surface layer fails to converge within 100 steps.
-   **Dataset Not Found**: Verify internet connection and that the HuggingFace URL is accessible.
