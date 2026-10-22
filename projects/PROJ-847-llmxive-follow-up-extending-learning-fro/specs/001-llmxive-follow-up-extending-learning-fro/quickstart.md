# Quickstart: llmxive-density-analysis

## Prerequisites
```bash
# Clone the repository (already done in CI)
git clone <repo-url>
cd llmxive-project

# Create a fresh virtual environment
python -m venv .venv
source .venv/bin/activate

# Install exact dependencies
pip install -r requirements.txt
```

## Step‑by‑Step Execution

1. **Download & checksum datasets**  
```bash
python -m src.llmxive.data --download
```
   - Streams GSM8K parquet files, downloads `bigbench_lite`, writes SHA‑256 checksums to `data/checksums.txt`.

2. **Run fixed‑density baselines (5 ρ × 20 seeds)**  
```bash
python -m src.llmxive.cli.run_experiments \
    --mode fixed \
    --rhos 0.1 0.3 0.5 0.7 0.9 \
    --seeds 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 \
    --max_epochs 5 \
    --output outputs/fixed_baselines.json
```
   - Enforces the 6‑hour wall‑clock limit; checkpoints saved automatically.

3. **Run adaptive scheduler (20 seeds)**  
```bash
python -m src.llmxive.cli.run_experiments \
    --mode adaptive \
    --seeds 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 \
    --max_epochs 5 \
    --output outputs/adaptive_run.json
```

4. **Run shuffled‑entropy control (20 seeds)**  
```bash
python -m src.llmxive.cli.run_experiments \
    --mode control_shuffle \
    --seeds 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 \
    --max_epochs 5 \
    --output outputs/control_shuffle.json
```

5. **Run fixed‑median density control (20 seeds)**  
```bash
python -m src.llmxive.cli.run_experiments \
    --mode fixed_median \
    --median_rho 0.55 \
    --seeds 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 \
    --max_epochs 5 \
    --output outputs/fixed_median.json
```

6. **Statistical validation & analysis**  
```bash
python -m src.llmxive.analysis \
    --fixed outputs/fixed_baselines.json \
    --adaptive outputs/adaptive_run.json \
    --control outputs/control_shuffle.json \
    --median outputs/fixed_median.json \
    --outdir outputs/statistics
```
   - Generates paired t‑test, quadratic fit with LOOCV, sensitivity slopes, entropy‑error correlation, causal control test JSON files, plus PNG figures in `outputs/figures/`.

7. **Inspect results**
```bash
# Human‑readable summary
cat outputs/summary.md

# View JSON artifacts
jq . outputs/fixed_baselines.json | less
jq . outputs/statistics/paired_t_test.json
```

All commands respect the 6‑hour runtime limit; the trainer will abort gracefully and mark the run as `"TIMEOUT"` if the limit is reached.

### CI Matrix Execution (recommended)
The full experiment suite is intended to be run via a GitHub Actions matrix that launches one job per `(rho, seed)` (or per adaptive/control/median seed). This ensures each job stays within the CPU and time constraints while the overall suite completes in parallel.

---

