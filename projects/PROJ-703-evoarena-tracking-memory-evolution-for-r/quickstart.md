# Quickstart: EvoArena Adaptation

This guide runs the scaled-down simulation of the **EvoArena** benchmark, specifically focusing on the **EvoMem** vs. **Baseline** comparison on persona memory evolution.

## Prerequisites
- Python 3.8+
- `pip install numpy pandas matplotlib` (optional for plotting)
- Ensure the `EvoMem-PersonaMem-Evo/data/chat_history_32k/` directory contains JSON files.

## Run Commands

```bash
python code/evomem_simulation.py
```

## Expected Outputs
- `data/evomem_results.csv`: Detailed accuracy metrics per session and aggregate summary.
- `figures/accuracy_comparison.png`: Bar chart comparing Baseline vs. EvoMem accuracy.
