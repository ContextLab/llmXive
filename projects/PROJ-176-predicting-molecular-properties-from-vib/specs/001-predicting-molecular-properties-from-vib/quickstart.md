# Quickstart: Predicting Molecular Properties from Vibrational Spectra  

## Prerequisites  
- Python 3.11+  
- Git  
- At least **10 GB** free disk space (raw + processed data)  
- ≤ 7 GB RAM (recommended for smooth operation)  

## Installation  

```bash
# 1. Clone the repository (or navigate to the project root)
git clone 
cd PROJ-176-predicting-molecular-properties-from-vib

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies (CPU‑only PyTorch)
pip install -r code/requirements.txt
```

*`requirements.txt` pins `torch==2.2.0+cpu` and all other libraries.*

## Step‑by‑Step Runbook  

All commands below are **CPU‑only** and respect the 6‑hour GitHub Actions limit.

### 0. Create top‑level logs directory & compileall check (T001)  

```bash
mkdir -p logs
python -m compileall -q code/ > logs/compileall.log 2>&1
```

The `compileall.log` must end with `Finished` (exit code 0).  

### 0.5 (optional) Generate paired IR spectra in‑house (if needed)  

```bash
python code/main.py generate_spectra
```

- Uses QM9 geometries to compute harmonic frequencies and approximate IR intensities with the **same B3LYP functional** via PySCF, ensuring functional consistency with the QM9 property targets.  
- Writes `data/generated/generated_spectra.npz`.  
- Skipped automatically if the external IR dataset’s `dft_method` matches B3LYP.

### 1. Download raw data & verify checksums  

```bash
python code/main.py download
```

- Downloads QM9 properties and IR spectra to `data/raw/`.  
- Computes SHA‑256 checksums, writes `logs/download.log`.  

### 2. Align datasets on InChIKey  

```bash
python code/main.py align
```

- Performs an inner join, discards mismatches, logs counts to `logs/alignment.log`.  
- Fails with exit code 1 if no matches are found.  

### 3. Preprocess spectra  

```bash
python code/main.py preprocess
```

- Interpolates to a 400‑4000 cm⁻¹, 1 cm⁻¹ grid, applies Gaussian smoothing (σ = 2 cm⁻¹), normalizes to unit area.  
- Writes `data/processed/aligned_dataset.npz`.  
- Logs KS‑test bias audit to `logs/bias_audit.log`.  

### 4. Train the 1‑D CNN (CPU‑only)  

```bash
python code/main.py train --max-samples 130000
```

- Samples (or weighted‑samples) up to 130 k aligned molecules, splits 80/10/10, trains with early stopping (patience = 10).  
- Saves `models/checkpoint_best.pt` and TensorBoard logs under `runs/`.  
- Training progress is stored in `logs/training.log`.  

### 5. Evaluate on held‑out test set  

```bash
python code/main.py evaluate --checkpoint models/checkpoint_best.pt
```

- Generates `results/evaluation_metrics.json` (MAE, R², TOST p-values, Hotelling’s T²).  

### 6. Independent validation (mandatory)  

```bash
python code/main.py validate --checkpoint models/checkpoint_best.pt
```

- Loads the B3LYP validation set, aligns on `InChIKey`, applies offset calibration if functional tags differ, computes MAE & R², writes `results/validation_metrics.json`.  

### 7. Control experiments (mandatory)  

```bash
# Scrambled‑order baseline
python code/main.py control --checkpoint models/checkpoint_best.pt

# Random‑noise baseline
python code/main.py control_random --checkpoint models/checkpoint_best.pt
```

- Both scripts write their respective JSON result files.  

### 8. Static analysis & testing (required evidence)  

```bash
# Static analysis with ruff
ruff check --fix code/ > logs/ruff_check.log 2>&1

# Run pytest suite
pytest tests/ -v > logs/pytest.log 2>&1
```

Both logs must end with a successful exit code (0).  

### 9. Pipeline runtime monitoring  

After the full run, inspect:

```bash
cat results/pipeline_runtime.json
```

The JSON must contain `"elapsed_seconds"` ≤ 21600 and `"status": "completed"`.

### 10. Profile report  

```bash
cat results/profile_report.txt
```

Shows peak memory (≤ 7 GB) and CPU usage.  

### 11. Structure report (T001)  

```bash
python code/utils/structure_report.py > results/structure_report.txt
```

Lists SHA‑256 hashes of all major artifacts; required for the top‑level `logs/` verification step.

## Final Deliverables Checklist  

| Artifact | Location | Verification |
|----------|----------|--------------|
| Top‑level logs directory | `logs/` | Exists; contains `compileall.log`, `download.log`, `alignment.log`, `bias_audit.log`, `training.log`, `ruff_check.log`, `pytest.log`. |
| Structure report | `results/structure_report.txt` | Load with `cat`; must list SHA‑256 hashes for raw, processed, model, and result files. |
| Aligned NPZ | `data/processed/aligned_dataset.npz` | Load with `np.load`; shapes must match schema. |
| Model checkpoint | `models/checkpoint_best.pt` | Valid PyTorch checkpoint; passes `contracts/model_output.schema.yaml`. |
| Evaluation metrics | `results/evaluation_metrics.json` | Valid against `contracts/evaluation_results.schema.yaml`. |
| Validation metrics | `results/validation_metrics.json` | Same schema; MAE increase flagged if > 20 %. |
| Scrambled‑order control | `results/control_metrics.json` | Same schema; MAE should be higher than main model. |
| Random‑noise control | `results/control_random_metrics.json` | Same schema; MAE should be substantially higher. |
| Runtime JSON | `results/pipeline_runtime.json` | `"elapsed_seconds"` ≤ 21600, `"status": "completed"`. |
| Profile report | `results/profile_report.txt` | Peak memory ≤ 7 GB, reasonable CPU usage. |
| Static analysis log | `logs/ruff_check.log` | Exit code 0. |
| Compileall log | `logs/compileall.log` | Exit code 0. |
| Pytest log | `logs/pytest.log` | All tests pass (`=== X passed`). |
| State file update | `state/projects/PROJ-176-predicting-molecular-properties-from-vib.yaml` | Updated SHA‑256 hashes for all artifacts. |

Follow the steps in order; each phase writes its own log file, enabling deterministic verification by the CI pipeline.  

---  

## Scientific Soundness & Circularity Mitigation  

1. **Functional Consistency** – By generating IR spectra in‑house with the same B3LYP functional used for QM9 target properties, we eliminate the primary source of circularity.  
2. **Independent Validation** – Evaluation on a separate B3LYP‑computed dataset (different molecules) tests generalisation beyond the training distribution.  
3. **Offset Calibration** – When functional mismatches exist but overlapping molecules are present, per‑property mean residuals are subtracted before metric computation, preventing systematic bias from contaminating the validation results.  
4. **Baseline Controls** – Scrambled‑order and pure random‑noise baselines demonstrate that the model’s performance relies on genuine spectral ordering and signal, not on trivial intensity statistics.  

These measures collectively ensure that any reported predictive capability reflects real information encoded in vibrational spectra rather than artefacts of shared computational methodology.  
