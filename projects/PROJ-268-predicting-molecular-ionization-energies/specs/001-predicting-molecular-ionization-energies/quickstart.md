# Quickstart: Predicting Molecular Ionization Energies

## Prerequisites
- Python 3.11+  
- Git  
- At least **7 GB** of RAM (local) or a GitHub Actions runner (Multiple CPU cores, 7 GB RAM).  

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-268-predicting-molecular-ionization-energies

# Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies (includes qm9pack)
pip install -r code/requirements.txt
```

## Step‑by‑Step Execution

### 1. Download & Verify Data
```bash
python code/data/download.py
```
- Downloads the QM9 parquet from the verified HuggingFace URL.  
- Computes and stores SHA‑256 checksum; aborts if mismatch.

### 2. Preprocess & Split
```bash
python code/data/preprocess.py \
    --input data/raw/qm9.parquet \
    --output data/processed/graphs.pt

python code/data/split.py \
    --graphs data/processed/graphs.pt \
    --train-ratio 0.80 --val-ratio 0.10 --test-ratio 0.10 \
    --strategy scaffold
```
- Generates `MoleculeGraph` objects, derives the `-HOMO` target, and creates a scaffold split with a large majority allocated to the primary set and smaller equal portions for the secondary sets.  
- Logs any excluded molecules (missing `homo` or unparsable SMILES) and performs a post‑hoc covariate balance check; if needed, the script will automatically re‑split stratified by molecular weight and rotatable bonds.

### 3. Proxy Validation (Construct Validity)
```bash
python code/data/validate_proxy.py \
    --qm9 data/processed/graphs.pt \
    --nist-url https://huggingface.co/datasets/Raziel1234/WebBooks-1/resolve/main/books_dataset.txt \
    --sample-size 500
```
- Computes $R^2$ and MAE between `-HOMO` and experimental ionization energies.  
- If $R^2 < 0.9$ **or** MAE > 0.4 eV, the script exits with status 1 and prints a “Construct Validity Failure” message.

### 4. **Job A – Train the MPNN (CPU‑only)**
```bash
python code/experiments/train.py \
    --config code/utils/config.yaml \
    --batch-size 64 \
    --max-epochs 200 \
    --timeout-hours 6
```
- Early‑stopping on validation loss.  
- Peak RAM and total runtime are logged; training aborts if RAM > 7 GB.  
- Checkpoint saved automatically on timeout.

### 5. Run Baselines
```bash
# Fingerprint linear regression
python code/models/baselines.py --type lr

# DFTB baseline (full dataset). If runtime >30 min, a stratified 5k‑molecule subset is used.
python code/models/baselines.py --type dftb
```

### 6. **Job B‑1 – Ablation Half 1 (Retraining)**
```bash
python code/experiments/ablation.py \
    --feature bond_type \
    --perturbation zero \
    --num-runs 3 \
    --subset-size <sufficiently large subset> \
    --batch-size 64 \
    --max-epochs 100 \
    --bootstrap-samples a sufficiently large number of samples \
    --runtime-guard-hours 4
```
- Trains **3** baseline models and **3** perturbed models (3 runs per config).  
- Each baseline run is paired with its perturbed counterpart via a shared random seed.  
- Results are saved to `results/ablation_part1.json`.

### 7. **Job B‑2 – Ablation Half 2 (Retraining)**
```bash
python code/experiments/ablation.py \
    --feature bond_type \
    --perturbation zero \
    --num-runs 3 \
    --subset-size 10000 \
    --batch-size 64 \
    --max-epochs 100 \
    --bootstrap-samples 1000 \
    --runtime-guard-hours 4 \
    --resume-from results/ablation_part1.json
```
- Completes the remaining **3** runs and merges with part 1, producing the final `results/ablation.json` that conforms to `contracts/ablation_result.schema.yaml`.

### 8. **Job C – Attribution & Evaluation**
```bash
# Integrated Gradients on a representative subset of test molecules
python code/experiments/evaluate.py \
    --model-path code/models/best_model.pth \
    --test-set data/splits/test.pt \
    --output-dir results/ \
    --ig-sample-size sufficiently large
```
- Generates `results/metrics.csv`, `results/attribution.json`, OOD flag report, and runs the qualitative IG‑intuition validation (see FR‑022).

## Expected Outputs
- `data/processed/graphs.pt` – processed graph dataset.  
- `code/models/best_model.pth` – trained MPNN checkpoint.  
- `results/metrics.csv` – MAE, RMSE, $R^2$, baseline comparisons, generalization gap, and pass/fail flags.  
- `results/ablation.json` – ablation MAE increase, p‑value, effect size, bootstrap CI.  
- `results/attribution.json` – Integrated Gradients maps for the sampled test subset.  
- `results/ood_report.txt` – count of scaffold‑OOD test molecules.

## Troubleshooting
- **Out‑of‑Memory**: Reduce `--batch-size`.  
- **Timeout**: Check `results/checkpoint_*.pth` for the latest saved state; rerun with `--resume`.  
- **Missing `homo`**: Review `logs/missing_homo.log`; if >5 % of records are missing, the pipeline will abort with a “Data Quality Warning”.  
- **Proxy Validation Failure**: Study cannot proceed; consider alternative target or dataset.  
- **Attribution Runtime**: Only a 1 k subset is processed by default; increase `--ig-sample-size` only if compute budget permits.  
