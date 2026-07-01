# JoyAI-VL-Interaction Adaptation Run-Book

This run-book executes the scaled-down adaptation of the JoyAI-VL-Interaction paper.
It runs on a standard CPU (2 cores, ~7GB RAM) and produces real quantitative results
by testing the core "vision-triggered responsiveness" logic.

## Prerequisites
- Python 3.9+
- `pip`

## Installation
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install transformers opencv-python pillow matplotlib numpy
```

## Execution
Run the adaptation script. It will:
1. Generate a synthetic video (simulating real events).
2. Load a CLIP model (proxy for the 8B VL model).
3. Analyze the video frame-by-frame.
4. Output metrics and plots.

```bash
python code/joyvl_adapter.py
```

## Outputs
After completion, check:
- `data/predictions.csv`: Frame-by-frame decisions.
- `data/metrics.json`: Precision, Recall, F1-Score.
- `figures/interaction_probability.png`: Visualization of the trigger probability.
