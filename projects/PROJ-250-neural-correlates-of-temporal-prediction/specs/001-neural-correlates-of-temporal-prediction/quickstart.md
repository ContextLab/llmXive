# Quickstart: Neural Correlates of Temporal Prediction Errors in Auditory Scene Analysis  

## Prerequisites  

* Python 3.11 (or newer)  
* Git  
* A Linux environment with at least 7 GB RAM (GitHub Actions free tier works out‑of‑the‑box)  

## Installation  

```bash
git clone <repo-url>
cd projects/PROJ-250-neural-correlates-of-temporal-prediction
python -m venv .venv
source .venv/bin/activate
pip install -r code/requirements.txt
```

## Step‑by‑Step Execution  

### 0️⃣ Dataset‑Gap Check (mandatory)  
```bash
python code/dataset_gap.py
```
*If a suitable open dataset is found **with BOTH “simple” and “complex” condition labels**, the script prints “Dataset OK – proceeding”.*  
*If not, it aborts with a clear error explaining the missing “complex” condition (fulfills FR‑008).*

### 1️⃣ Data Acquisition (only after Phase 0 succeeds)  
```bash
python code/download.py
```
*Downloads the verified EEG dataset, verifies SHA‑256 checksums (SC‑007), and records hashes in `state/...yaml` (FR‑001, FR‑013).*

### 2️⃣ Preprocessing (NaN validation)  
```bash
python code/preprocess.py
```
*Band‑pass, ICA, mastoid re‑reference, baseline correction, epoching, QC, and channel interpolation (FR‑002, FR‑003). After epoch creation the script asserts `np.isnan(epochs.get_data()).any() == False` (SC‑008).*

### 3️⃣ Core Analysis (includes power analysis & covariate modelling)  
```bash
python code/analysis.py
```
Performs:
- MMN amplitude/latency extraction (150–250 ms, fronto‑central cluster) (FR‑004)  
- Pre‑stimulus noise‑floor SNR validation (SNR ≥ 3 → SC‑001)  
- Leave‑one‑out canonical topography generation saved to `data/templates/canonical_mmn.npy` (FR‑009)  
- Topographic consistency & validity (Pearson r ≥ 0.8, SC‑004)  
- Paired t‑test with Benjamini‑Hochberg FDR (FR‑005, SC‑002)  
- Cohen’s d vs. benchmark from `data/benchmarks/mmn_effect_sizes.json` (FR‑010, SC‑003)  
- **Power analysis** (α = 0.05, power = 0.8, effect size = 0.5); aborts confirmatory testing and flags results as exploratory if N < required (FR‑016, SC‑006)  
- **Covariate mixed‑effects model** when stimulus‑level covariates are present (addresses methodology‑0f0359eb)  
- Writes per‑subject **MMNMetric** rows to `results/metrics.csv` (FR‑015) and group‑level **GroupStats** to `results/stats.json`.  

### 4️⃣ Visualization (file‑existence checks)  
```bash
python code/visualize.py
```
Generates PNG/SVG files in `results/figures/`:
- ERP waveforms with MMN window highlighted  
- Scalp topography maps for simple and complex conditions  
- Significance heatmaps  

After each save the script asserts the file exists and its size > 0 KB; any failure raises an error (SC‑005).  

### 5️⃣ Contract Tests & Reference Validation (final gate)  
```bash
pytest code/tests/
```
Validates:
- `data/raw/` metadata against `contracts/dataset.schema.yaml` (SC‑007)  
- `results/metrics.csv` against `contracts/output.schema.yaml` (covers SC‑005‑SC‑009)  
- `results/stats.json` against `contracts/stats.schema.yaml` (SC‑008)  
- Presence and non‑empty size of all figure files (SC‑005, SC‑009)  
- Executes `verify_references.py` to run the Reference‑Validator **before reporting** (fulfills FR‑012‑3).  

All tests must pass before the pipeline is considered research‑ready.

---


