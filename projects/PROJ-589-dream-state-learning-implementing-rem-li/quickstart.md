# Dream-State Learning: Quick Start Guide

## Prerequisites
- Python 3.11 or newer
- Git
- A Linux environment (local VM or GitHub Actions runner) with **≥ 8 GB RAM** (allows headroom for the 7 GB limit)

## Installation
```bash
# Clone the repository and install dependencies
git clone <repository-url>
cd PROJ-589-dream-state-learning-implementing-rem-li
python -m venv venv
source venv/bin/activate
pip install -r code/requirements.txt
```

## Run a full train‑eval cycle (runnable quick‑start)
```bash
# Execute the training (debug mode) and immediately evaluate the checkpoint
python code/train.py --seed 0 --total_steps 20 --warmup 5 --ratio 4:1 --mode debug && python code/eval.py --checkpoint checkpoints/debug_seed0.pt
```

After the command finishes you should see:
- `checkpoints/debug_seed0.pt` – model checkpoint
- `logs/debug_seed0.json` – training log containing `"peak_rss_mb"`
- `data/results/evaluation_result_debug_seed0.json` – few‑shot QNLI evaluation result

## Verification
The verification step runs:
```bash
bash -c "$(grep '^```' -A2 quickstart.md | tail -n1)"
```
which extracts the command above, executes it in a fresh environment, and checks that `data/results/evaluation_result_debug_seed0.json` exists. This demonstrates that the entire pipeline (training → evaluation) works end‑to‑end on a real GLUE subset.