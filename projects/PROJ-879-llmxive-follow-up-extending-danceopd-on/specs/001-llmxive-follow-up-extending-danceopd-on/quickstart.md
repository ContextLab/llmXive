# Quickstart: llmXive follow-up: extending "DanceOPD: On-Policy Generative Field Distillation"

## Prerequisites

*   Python 3.11+
*   GB+ RAM (Free-tier GitHub Actions compatible)
*   Access to the verified dataset URLs (Internet connection required).

## Installation

1.  **Clone and Setup**
    ```bash
    git clone <repo-url>
    cd <project-dir>
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r code/requirements.txt
    ```

3.  **Verify Weights**
    Ensure the pre-trained DanceOPD weights are available and valid.
    ```bash
    python code/utils/check_weights.py --path <path-to-weights>
    ```
    *If this fails, the pipeline will not proceed.*

## Execution Flow

The project is designed to run as a single pipeline script or step-by-step.

### Step 1: Generate Teacher Ground Truth (FR-001)
Generates `TeacherRoutingDataset.parquet`.
```bash
python code/data/generate_teacher.py \
  --source imagenet \
  --samples a substantial cohort of participants \
  --batch-size \
  --output data/processed/teacher_routing_dataset.parquet
```

### Step 2: Train Decision Trees (FR-002, FR-003)
Trains trees for `max_depth` across a range of values spanning from shallow to deep configurations.
```bash
python code/models/train_tree.py \
  --input data/processed/teacher_routing_dataset.parquet \
  --depths 2,4,6,8,10,12,14,16,18,20 \
  --output models/trained_trees/
```

### Step 3: CPU-Only Fidelity Evaluation (FR-004, FR-005)
Generates images and calculates metrics.
```bash
python code/models/inference.py \
  --dataset data/processed/teacher_routing_dataset.parquet \
  --split test \
  --models models/trained_trees/ \
  --pilot-samples \
  --target-power \
  --output data/results/inference_results.parquet
```
*Note: This step includes a dynamic power check. It runs a pilot, calculates variance, and extends N if needed. A timeout is enforced; partial results are saved if exceeded.*

### Step 4: Statistical Analysis (FR-006)
Performs bootstrap and t-tests.
```bash
python code/utils/stats.py \
  --input data/results/inference_results.parquet \
  --output data/results/statistical_tests.json
```

## Expected Outputs

*   `data/processed/teacher_routing_dataset.parquet`: The synthetic ground truth.
*   `models/trained_trees/`: A directory of `.pkl` files.
*   `data/results/inference_results.parquet`: Metrics and paths for generated images.
*   `data/results/statistical_tests.json`: P-values and conclusions.

## Troubleshooting

*   **OOM (Out of Memory)**: Reduce `--batch-size` in Step 1 or `--pilot-samples` in Step 3.
*   **Timeout**: The pipeline auto-saves partial results. Check `data/results/` for incomplete but valid data.
*   **Weight Check Failed**: Verify the SHA256 checksum of your local weights file matches the manifest.