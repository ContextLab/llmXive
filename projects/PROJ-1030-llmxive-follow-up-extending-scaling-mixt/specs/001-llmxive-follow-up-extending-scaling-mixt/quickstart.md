# Quickstart: llmXive follow-up: extending "Scaling Mixture-of-Experts Video Pretraining for Embodied Intelligence"

## Prerequisites

-   Python 3.11+
-   Git
-   ~15 GB Disk Space (temporary)
-   Internet Connection (for dataset download)

## Installation

1.  **Clone the Repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-1030-llmxive-follow-up-extending-scaling-mixt
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` pins versions for reproducibility.*

## Running the Pipeline

The pipeline consists of three main steps. Run them sequentially or use the orchestration script.

### Step 1: Extract Features (FR-001, FR-002)

Downloads a subset of BridgeData videos and extracts latent vectors/expert masks.

```bash
python code/extract_features.py \
  --dataset "rail-berkeley/bridgedata_v2" \
  --output-dir data/processed/features \
  --chunk-size 10 \
  --max-clips 100
```

*Output*: `data/processed/features/features.npy`

### Step 2: Generate Labels (FR-003, FR-008)

Reconstructs 3D states (with kinematic checks) and simulates physics to generate validity labels.

```bash
python code/generate_labels.py \
  --input-dir data/processed/features \
  --output-dir data/processed/labels \
  --confidence-threshold 0.9 \
  --kinematic-check
```

*Output*: `data/processed/labels/labels.csv`

### Step 3: Train Classifier (FR-004, FR-005)

Trains a lightweight classifier and evaluates performance.

```bash
python code/train_classifier.py \
  --features data/processed/features/features.npy \
  --labels data/processed/labels/labels.csv \
  --model-type random_forest \
  --shap-budget 0.2 \
  --output-dir data/processed/model
```

*Output*: `data/processed/model/metrics.json`, `data/processed/model/feature_importance.png`

## Verification

To verify the setup, run the unit tests:

```bash
pytest tests/unit/
```

To run the full integration test (simulated CI run):

```bash
pytest tests/integration/
```

## Troubleshooting

-   **OOM Error**: Reduce `--chunk-size` in Step 1.
-   **Download Failure**: Check internet connection; the script has built-in retry logic.
-   **Physics Crash**: Check `data/processed/labels/labels.csv` for "null" labels; adjust `--confidence-threshold` or check kinematic validity.
-   **Prior Overlap**: If `prior_audit.py` detects shared priors, the script will automatically switch to SfM (COLMAP) for reconstruction.
