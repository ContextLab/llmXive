# Quickstart: llmXive Follow-up: Extending "JoyAI-VL-Interaction"

## Prerequisites
- Python 3.11+
- GB+ RAM (for streaming processing)
- A small number of vCPU cores
- Git

## Installation

1.  **Clone and Setup**:
    ```bash
    git checkout 001-llmxive-vl-intuition
    cd projects/PROJ-863-llmxive-follow-up-extending-joyai-vl-int
    python -m venv .venv
    source .venv/bin/activate
    pip install -r code/requirements.txt
    ```

2.  **Verify Environment**:
    ```bash
    python code/utils/validation.py --check-cpu
    # Should output: "Environment OK: CPU-only, RAM < 7GB available"
    ```

## Running the Pipeline

### Step 1: Generate Synthetic Data
Generates the video frames and visual-only ground truth labels with noise injection.
```bash
python code/data_synthesis/generator.py --duration 10 --seed 42 --inject-noise
# Output: data/raw/ and data/manifest.jsonl
```

### Step 2: Run Visual Baseline
Runs the Noisy Rule-Based Visual Detector.
```bash
python code/baseline/visual_detector.py --manifest data/manifest.jsonl
# Output: data/baseline/
```

### Step 3: Extract Features
Extracts internal states from the JoyAI-VL-Interaction model (CPU mode).
```bash
python code/feature_extraction/extractor.py --model-path ./models/joyai-vl-int --batch-size 100
# Output: data/features/
```
*Note: This step streams data to avoid OOM. It may take several hours for 10 hours of video.*

### Step 4: Train Scheduler
Trains the 15M-parameter Transformer classifier.
```bash
python code/scheduler/train.py --epochs 10 --lr 1e-4
# Output: models/scheduler_checkpoint.pth and logs/training.log
```

### Step 5: Evaluate
Calculates AUC-ROC, Cohen's Kappa, Mutual Information, and Nested Model Comparison.
```bash
python code/scheduler/eval.py --checkpoint models/scheduler_checkpoint.pth --baseline data/baseline/
# Output: data/evaluation/results.jsonl and metrics_summary.json
```

## Validation
Run the full test suite to ensure contract compliance:
```bash
pytest tests/
```

## Troubleshooting
- **OOM Error**: Reduce `--batch-size` in the extractor step.
- **CUDA Error**: Ensure `CUDA_VISIBLE_DEVICES=""` is set. The code should default to CPU.
- **Missing Labels**: Check `data/manifest.jsonl` for `ground_truth_label` nulls.
- **Baseline Mismatch**: Ensure `--inject-noise` was used in Step 1 if Step 2 fails due to deterministic logic.