# Quickstart: llmXive follow-up: extending "Kwai Keye-VL-2.0 Technical Report"

## Prerequisites

- Python 3.11+
- `ffmpeg` installed on the system path.
- Sufficient free disk space (for temporary video processing).
- Substantial RAM (required for inference).

## Installation

1.  **Clone and Setup Environment**:
    ```bash
    git checkout 001-extreme-aspect-ratio-robustness
    cd projects/PROJ-891-llmxive-follow-up-extending-kwai-keye-vl/code/
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Download Model Weights**:
    Ensure the Kwai Keye-VL-2.0 INT4 weights (or LLaVA-NeXT-34B INT4 fallback) are available in `models/`. If not present, download the quantized version from the HuggingFace model hub.

3.  **Validate Citations**:
    Run the validation script to ensure all dataset URLs are reachable and verified.
    ```bash
    python scripts/validate_citations.py
    ```

## Running the Pipeline

### Step 1: Generate Synthetic Dataset
Generate a set of distorted clips. **Note**: The control group consists of the original, unmodified ActivityNet videos, which are fetched from the source.

```bash
python src/generators/distort_video.py \
  --ratios "1:10,10:1,1:20,20:1" \
  --count 125 \
  --output data/distorted \
  --metadata-path data/raw/activitynet_metadata.json
```

*Note: This step may take a moderate amount of time depending on I/O speed.*

### Step 2: Run Inference
Execute the CPU-constrained inference on the generated dataset and the original control videos.

```bash
python src/inference/run_inference.py \
  --model-path models/kwai_keye_vl2_int4 \
  --input-dir data/distorted \
  --control-source data/raw/activitynet_metadata.json \
  --output data/outputs/predictions.json \
  --max-memory 7000 \
  --timeout 21600
```

*Note: The script will automatically skip clips that fail the semantic integrity check and log OOM events. It implements time-boxed adaptive sampling.*

### Step 3: Analyze Results
Calculate mIoU and perform **Independent Samples** statistical testing.

```bash
python src/analysis/stats.py \
  --predictions data/outputs/predictions.json \
  --metadata data/raw/activitynet_metadata.json \
  --output data/outputs/report.md
```

## Verification

To verify the setup, run the unit tests:

```bash
pytest tests/unit/
```

To run the full integration test (requires model and data):

```bash
pytest tests/integration/
```

## Troubleshooting

- **OOM Error**: If the process is killed, reduce the `--max-memory` limit in the inference script or decrease the number of frames per video.
- **Missing ffmpeg**: Install ffmpeg via `apt-get install ffmpeg` or `brew install ffmpeg`.
- **Model Load Failure**: If Kwai Keye-VL-2.0 fails to load, the system will automatically switch to the LLaVA-NeXT-34B fallback (if configured).
- **Time Limit**: If a predefined time limit is reached, the pipeline will stop and generate a report with the achieved power.
