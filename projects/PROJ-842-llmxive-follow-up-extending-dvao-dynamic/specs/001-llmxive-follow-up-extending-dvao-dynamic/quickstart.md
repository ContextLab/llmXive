# Quickstart: llmXive follow‑up – Extending DVAO

## Prerequisites
- Python 3.11 or newer
- Git
- `pip`

## Installation

```bash
# 1️⃣ Clone the repository
git clone <repo-url>
cd projects/PROJ-842-llmxive-follow-up-extending-dvao-dynamic/code

# 2️⃣ Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3️⃣ Install pinned dependencies
pip install -r requirements.txt
```

## Step‑by‑Step Run

### 0️⃣ Verify citations (Constitution II)
```bash
python src/verification/verify_citations.py
# Should exit with a successful code and produce docs/citations_report.json
```

### 1️⃣ Derive the theoretical bound (FR‑001, FR‑002)
```bash
python src/derivation/sample_complexity.py
# Generates data/processed/theoretical_bound.json
python src/derivation/verify_symbolic.py
# Checks algebraic consistency; see data/processed/symbolic_verification.json
```

### 2️⃣ Generate a synthetic environment (FR‑003, FR‑014, FR‑016)
```bash
python src/environment/synthetic_mdp.py \
    --n 50 \
    --rho 0.0 \
    --distribution gaussian \
    --seed 42
# Output: data/processed/noise_properties.json (includes full correlation matrix)
```
*If `--n 50` triggers the resource guard, the script will automatically halve the **episode count** (not the state space) to keep RAM ≤ 7 GB and will log the effective episode count.*

### 3️⃣ Run the full experimental suite (FR‑005‑FR‑019)
```bash
python src/main.py --config configs/default.yaml
# Produces:
#   data/processed/empirical_results.json
#   data/processed/statistical_results.json
#   reports/*.png (figures)
```
The script enforces a multi‑core / 7 GB RAM limit; any breach aborts with a clear error.

### 4️⃣ Sensitivity sweep over window size (FR‑007)
```bash
python src/analysis/statistics.py --sweep window_size \
    --values 0.01,0.05,0.1
# Updates statistical_results.json with TOST outcomes.
```

### 5️⃣ Validate construct validity across reward families (FR‑010)
```bash
python scripts/validate_construct_validity.py \
    --distributions Linear,Sparse,Non-Convex,NonLinearMLP
# Output: data/processed/construct_validity_results.json
```

### 6️⃣ Held‑out heavy‑tailed validation (FR‑012)
```bash
python src/environment/synthetic_mdp.py \
    --n 20 --rho 0.0 --distribution heavy_tailed --seed 999 \
    --held-out
# Re‑runs the heuristic on the held‑out set; results merged into empirical_results.json.
```

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| **MemoryError** | State space still large for \(N>50\) | Reduce `--n` or increase the reduction factor via `--state-reduction 0.4`. |
| **`ResourceLimitExceeded`** | CPU or RAM guard triggered | Verify that `--cores` is not set > 2; ensure no other processes are running on the runner. |
| **Correlation matrix mismatch** | Target \(\rho\) not achieved | Check `noise_properties.json`; the script logs the achieved matrix. Adjust seed or increase `--samples-per-objective`. |
| **Statistical test fails** | Insufficient runs (< 30) | Increase `--episodes` in `configs/default.yaml` (still within the 6 h budget). |
| **Citation audit fails** | Missing or mismatched reference | Edit `docs/citations.md` to include the correct DOI/URL and re‑run `verify_citations.py`. |

All generated JSON files can be validated locally:

```bash
pip install jsonschema
jsonschema -i data/processed/empirical_results.json contracts/empirical_results.schema.yaml
```

Enjoy reproducible, resource‑constrained MORL research!  

---


