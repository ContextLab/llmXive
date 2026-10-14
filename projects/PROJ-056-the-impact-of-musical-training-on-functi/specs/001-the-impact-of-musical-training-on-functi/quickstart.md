# Quickstart: The Impact of Musical Training on Functional Connectivity in Adolescent Brains

## 1. Prerequisites
- Python 3.11+  
- ~2 GB free RAM (≥ 7 GB recommended for larger synthetic runs)  
- Git  

## 2. Installation
```bash
# Clone the repository
git clone <REPO_URL>
cd projects/PROJ-056-the-impact-of-musical-training-on-functi

# Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install pinned dependencies
pip install -r code/requirements.txt
```

## 3. Running the Pipeline

### 3.1 Synthetic Verification Mode (default)
```bash
# Generate a balanced synthetic cohort of an appropriate size and run the full analysis
python code/main.py --mode synthetic --n-subjects <desired sample size>
```
- This creates mock NIfTI files, a subject table, computes connectivity, performs all statistical tests, and writes results under `data/results/`.  
- **Important**: Synthetic mode is **only for pipeline verification**; it does **not** provide scientific conclusions about musical training effects because it uses simulated data without a real group effect. Scientific results will be derived only when a verified dataset is supplied and `--mode real` is used.

### 3.2 Real‑Data Mode (when a verified dataset becomes available)
```bash
python code/main.py --mode real --data-path /path/to/verified/dataset
```
- The directory must contain:
  - `subjects.csv` with the exact columns listed in the **Subject** schema.
  - Resting‑state NIfTI files referenced by `rs_fmri_path`.
- If any required column or file is missing, the pipeline aborts with a clear error.
- **FR‑001** will be satisfied once such a verified dataset is provided.

## 4. Verify Outputs
```bash
# Run the full test suite (includes JSON‑Schema validation)
pytest tests/

# Inspect memory usage log
cat data/logs/memory_usage.log
```

## 5. Interpreting Results
- `data/results/statistical_results.csv` – Edge‑wise Welch’s t‑tests; look for `q_value < 0.05`.  
- `data/results/nbs_components.json` – Largest connected component; check `p_value_fwer`.  
- `data/results/sensitivity_analysis.csv` – Counts of significant edges at q = 0.01, 0.05, 0.10.  
- `data/results/master_results.json` – Single source of truth aggregating key statistics for reporting.

## 6. Troubleshooting
- **MemoryError** – Reduce `--n-subjects` or switch to synthetic mode with fewer subjects.  
- **Data Missing** – Ensure the real‑data directory follows the schema; otherwise use synthetic mode.  
- **Long Runtime** – Decrease NBS permutations via `--n-permutations` (minimum 500 for exploratory runs).  

---


