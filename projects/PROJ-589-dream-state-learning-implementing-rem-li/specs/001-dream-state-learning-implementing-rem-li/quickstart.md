# Quickstart: Dream-State Learning

## Prerequisites
- Python 3.11 or newer  
- Git  
- A Linux environment (local VM or GitHub Actions runner) with **≥ 8 GB RAM** (allows headroom for the 7 GB limit)  

## Installation
```bash
# 1️⃣ Clone the repository
git clone <repository-url>
cd projects/PROJ-589-dream-state-learning-implementing-rem-li

# 2️⃣ Create a virtual environment
python -m venv venv
source venv/bin/activate

# 3️⃣ Install pinned dependencies
pip install -r code/requirements.txt
```

## Step‑by‑Step Run

### 1. Download GLUE data (once)
```bash
python code/data_loader.py --download
# Data will appear under data/raw/
```

### 2. Run a **debug** experiment (fast sanity check)
```bash
python code/train.py \
  --seed 42 \
  --total_steps 20 \
  --warmup_steps 5 \
  --ratio 4:1 \
  --mode debug
```
*Expected*: Logs show wake → dream transitions, entropy checks, and a checkpoint saved to `checkpoints/debug.pt`.

### 3. Run the **pilot** experiment (primary analysis)
```bash
python code/train.py \
  --seeds 0,1,2 \
  --total_steps 100 \
  --warmup_steps 20 \
  --ratio 4:1 \
  --temp 1.0 \
  --baseline
```
- This launches multiple experimental runs (wake/dream) and multiple baseline runs, each respecting the memory/timeout caps.  
- Checkpoints are stored under `checkpoints/seed_{N}_{regime}.pt`.

### 4. (Optional) Run the **temperature sweep** ablation
```bash
python code/train.py \
  --seeds 3,4 \
  --total_steps 100 \
  --warmup_steps 20 \
  --ratio 4:1 \
  --temp_sweep 0.5 1.0 1.5 2.0 \
  --baseline
```
- Executes up to **2** additional seeds *only if* remaining compute budget permits.  
- Results are logged as separate ablation variants.

### 5. Evaluate & compute statistics
```bash
python code/eval.py --results_dir data/results/
```
*Output*: `data/results/experiment_summary.json` containing the paired t‑test, effect size, power estimate, and any notes about insufficient power (per `statistical_report_schema.yaml`).

## Troubleshooting
| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| **OOM / MemoryError** | Batch size too large or temperature causing long generations. | Reduce `--batch_size` in `code/config.py` or switch to a lower temperature. |
| **Dream step skipped** | Entropy < 0.5 bits or perplexity > 50. | This is expected for low‑quality generations; the run will continue with a dummy wake step to keep token exposure equal. |
| **Timeout (>5 h)** | Too many seeds or steps. | Reduce `--total_steps` or run a subset of seeds (as shown above). |
| **Missing `statistical_report.json`** | Evaluation script failed due to < 5 evaluation samples. | Verify that `data/raw/` contains at least 5 QNLI validation examples per seed; otherwise the report will contain `"note": "insufficient power"` as designed. |

## Verification Checklist
1. Run `debug` mode – confirm `logs/debug.log` contains `"phase": "wake"` and `"phase": "dream"` entries.  
2. Ensure a checkpoint file (`checkpoints/debug.pt`) loads without error (`torch.load`).  
3. After pilot run, verify that each JSON result validates against its schema (`pytest -k contract`).  

---

