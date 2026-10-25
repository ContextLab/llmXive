# Quickstart: llmXive follow-up: extending "Multi-Turn Reflective Masking Elicits Reasoning in Mask Diffusion Mode"

## Prerequisites
- Python 3.11+
- Git
- ~ sufficient free RAM for the model and data, and adequate disk space.

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-878-llmxive-follow-up-extending-multi-turn-r

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install pinned dependencies
pip install -r code/requirements.txt

# Verify CPU‑only torch
python - <<EOF
import torch
print("Torch version:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())
EOF
```

## Workflow

### 1️⃣ Generate Synthetic Dataset
```bash
python code/graph_generator.py \
  --count <sufficiently large sample> \
  --depth-min 1 --depth-max 10 \
  --branch-min 1 --branch-max 5 \
  --output data/raw/synthetic_puzzles.jsonl \
  --seed 42
```
- **Output**: `data/raw/synthetic_puzzles.jsonl`
- **Validate**: `pytest tests/test_graph_generator.py`

### 2️⃣ Run Reflective Masking Loop (CPU)
```bash
python code/rm_executor.py \
  --input data/raw/synthetic_puzzles.jsonl \
  --output data/processed/execution_log.csv \
  --max-turns 50 \
  --batch-size 5 \
  --device cpu
```
- For the extended budget run (FR‑008) on the **full** dataset:
```bash
python code/rm_executor.py \
  --input data/raw/synthetic_puzzles.jsonl \
  --output data/processed/execution_log_extended.csv \
  --max-turns 1000 \
  --batch-size 5 \
  --device cpu
```

### 3️⃣ Statistical Analysis
```bash
python code/analyzer.py \
  --puzzles data/raw/synthetic_puzzles.jsonl \
  --results data/processed/execution_log.csv \
  --output results/statistical_report.json \
  --thresholds 40 50 60
```
- Figures are saved to `results/paper_figures/`.

## Verification

```bash
# Check dataset size and depth range
python - <<EOF
import json, itertools
data = [json.loads(l) for l in open('data/raw/synthetic_puzzles.jsonl')]
print("Instances:", len(data))
print("Depth range:", min(d['nesting_depth'] for d in data),
      "-", max(d['nesting_depth'] for d in data))
print("Branching range:", min(d['branching_factor'] for d in data),
      "-", max(d['branching_factor'] for d in data))
EOF

# Inspect analysis report
cat results/statistical_report.json
```

## Troubleshooting
- **OOM**: Reduce `--batch-size` in `rm_executor.py`.
- **Slow runtime**: Ensure no other CPU‑intensive jobs are running; the process is CPU‑bound.
- **Graph generation failures**: Extreme depth/branch combos may be infeasible; adjust ranges or increase the number of rejection‑sampling attempts.
- **High collinearity**: If orthogonalization repeatedly fails, consider a sparser grid of target pairs (still respects FR‑007).
- **Success mis‑labeling**: Remember that a run is marked **successful** only when the inferred path exactly matches the ground‑truth path; `path_coverage` alone is insufficient.
- **Extended budget analysis**: The 1000‑turn run processes the **full** dataset; expect longer runtime but still within CI limits.

---


