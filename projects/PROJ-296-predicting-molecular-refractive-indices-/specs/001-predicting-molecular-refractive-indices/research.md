# Research: Predicting Molecular Refractive Indices from Graph-Based Molecular Representations

## Problem Definition
Refractive index (RI) is a fundamental optical property influencing drug formulation and material design. Classical atomic‑contribution methods (e.g., Lorentz‑Lorenz) capture additive effects but may miss subtle electronic interactions such as conjugation or halogen substitution. This study evaluates whether a lightweight Message Passing Neural Network (MPNN) can improve predictive accuracy **within a strict CPU‑only environment**, and whether Integrated Gradients can reveal chemically interpretable drivers of RI.

## Dataset Strategy

### Primary Dataset Search & Availability Check
| Candidate (Verified URL) | Contains `smiles`? | Contains `refractive_index`? | Row Count (sample) | Verdict |
|--------------------------|-------------------|-----------------------------|--------------------|---------|
| ` | ✅ | ✅ | 1 200 | **Accepted** – meets FR‑001 (≥ 500 rows, RI column). |
| ` | ✅ | ❌ | ~200 k | **Rejected** – missing target |
| ` | ✅ | ❌ | ~150 k | **Rejected** – missing target |

> **Result:** The Zenodo dataset satisfies the requirements; the pipeline proceeds with it. If the download fails, a **synthetic benchmark** (see below) will be generated automatically.

### Fallback Synthetic Benchmark (triggered only if no real RI dataset)
- Downloads the open QM9 dataset (`huggingface.co/datasets/qm9`), computes synthetic RI values using the Lorentz‑Lorenz equation applied to atomic‑fragment constants, and creates `data/synthetic/ri_synthetic.csv`.  
- This synthetic set contains > 1 000 molecules, enabling the same modeling and attribution workflow while preserving the comparative research question (model vs. baseline).

### Preprocessing & Filtering (conditional on dataset availability)
1. **SMILES parsing** via RDKit; unparsable rows logged to `logs/failed_parsing.log`.  
2. **Molecular‑weight filter**: exclude molecules with MW > 500 Da (ensures RAM compliance).  
3. **Temperature normalization**: apply Edlén equation when temperature metadata is present; otherwise flag uncertainty in `logs/preprocess_summary.log`.  
4. **Feature engineering**: node features (atomic number, degree, hybridization, aromaticity) and edge features (bond type, conjugation, stereo).  
5. **Global scalar**: normalized molecular weight appended to graph readout.

### Data Splitting (conditional)
- **Method**: Murcko scaffold split (RDKit) with **25 independent splits** (5 scaffold partitions × 5 repeats).  
- **Stratification**: each split is stratified by refractive‑index quartile and molecular‑weight decile to preserve distributional balance.  
- **Ratios**: [deferred] train / [deferred] validation / [deferred] test.
- **Guarantee**: **Zero scaffold overlap** between sets, preventing leakage.

## Methodology (executed only if dataset passes the availability check)

### 1. Baseline: Atomic‑Contribution Model (FR‑004)
- Compute **Molar Refractivity (MR)** using additive atomic fragment constants from **Meylan et al., 1996**.  
- Convert MR → RI via the **Lorentz‑Lorenz** equation.  
- Output per‑split CSV `results/baseline_predictions_{i}_{j}.csv`.

### 2. Graph Neural Network (FR‑002)
- **Architecture**: 3 message‑passing layers, hidden dim = 64, mean aggregation, global mean pooling → 2‑layer MLP (64 → 32 → 1) with ReLU.  
- **Training**: MSE loss, Adam (lr = 1e‑3), early stopping (patience = 10) on validation loss, max epochs = 200.  
- **Device**: `torch.device("cpu")` enforced.  
- **Seeds**: Fixed per split (`seed = 2000 + i*10 + j`).  
- **Outputs**: Model weights `models/mpnn_{i}_{j}.pt`, training log `logs/training_{i}_{j}.log`.

### 3. Integrated Gradients Attribution (FR‑005)
- **Baseline**: zero‑vector; 50 integration steps; also run with mean‑feature baseline for sensitivity.  
- **Output**: `results/attributions_{i}_{j}.csv` (conforms to `FeatureAttribution` entity).

### 4. Evaluation & Statistical Rigor (FR‑006)
- **Per‑Molecule Errors**: For each test set, compute error vectors `e_gnn` and `e_baseline`.  
- **Paired Test**: Perform a **paired t‑test** on `e_gnn` vs `e_baseline`. Test normality with **Shapiro‑Wilk** (α = 0.05); if normality fails, fall back to **Wilcoxon signed‑rank test**.  
- **Effect Size & Power**: Compute Cohen’s d, 95 % CI, and estimate achieved power using `statsmodels`. Report both p‑value and power for each split.  
- **Bootstrap MAE Difference**: Several thousand bootstrap resamples per split. to obtain bias‑corrected CI for the MAE difference.  
- **SSoT Generation**: Aggregate all metrics, p‑values, effect sizes, and power into `results/ssot_metrics.csv`. This file is the **authoritative source** for the paper (Principle IV).  
- **Plots**: Parity plot (`parity_{i}_{j}.png`) and feature‑importance bar chart (`importance_{i}_{j}.png`), each < 5 MB.

### 5. External Attribution Validation (addresses SC‑003)
- Download the QM9 dataset (contains polarizability `alpha` and dipole moment `mu`).  
- For molecules that appear in both the RI dataset and QM9, compute Pearson correlation between the **Integrated Gradients importance scores for conjugated substructures** and the **polarizability values**.  
- Report correlation coefficients and significance in `results/attribution_validation.csv`. This demonstrates that the model’s attributions align with independent, physically‑relevant properties not explicitly encoded as features.

### 6. Robustness & Sensitivity (User Story 3)
- **MAE Variance**: Compute variance of test MAE across the 25 independent splits; require ≤ 0.01 (report observed value).  
- **Hyper‑parameter Sweep**: L2 weight decay ∈ {0, 1e‑4, 1e‑3}; plot MAE vs. decay → `results/robustness/l2_sweep.png`.  
- **Over‑fit Detection**: early‑stopping trigger logged; if validation loss rises for 10 epochs, a warning is added to `logs/robustness.log`.

### 7. Combined Prediction Output (fulfills `output.schema.yaml`)
- Merge GNN predictions, baseline predictions, and the top‑10 attribution scores per molecule into `results/prediction_results_{i}_{j}.csv`.  
- This file validates against `contracts/output.schema.yaml` and serves as the primary artifact for downstream reporting.

### 8. Contract Validation
- After each major step, validate outputs against the appropriate JSON‑Schema contracts.  
- Validation failures abort with a deterministic error log (`logs/validation_error.log`).

## Compute Feasibility
- **CPU‑First**: All code runs on CPU; no CUDA imports.  
- **Memory**: Even the largest candidate dataset (< 200 MB) stays well below the a modest storage limit.  
- **Runtime**: End‑to‑end for 25 splits ≤ 5 h on GitHub Actions free tier (well within the 6 h limit).

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| No open RI dataset ≥ 500 samples | Fatal to FR‑001 | Identified Zenodo dataset; fallback synthetic benchmark from QM9 ensures pipeline can still run. |
| OOM on larger batch sizes | Medium | Auto‑reduce batch size; fallback to batch = 16. |
| Overfitting on limited data | High | Early stopping, dropout 0.2, L2 = 1e‑4; report effect sizes, not just p‑values. |
| Attribution baseline bias | Medium | Run with multiple baselines; report variance. |
| Low statistical power | Medium | Formal power analysis (statsmodels) and bootstrap; report achieved power. |
| Distributional confounds in splits | Medium | Stratified scaffold splits by RI quartile and MW decile. |
| Non‑independent repeats | High | 25 fully independent scaffold splits (new random seed per repeat). |

---


## Quickstart: Predicting Molecular Refractive Indices

## Prerequisites
- Python 3.11+  
- `pip` (or `conda`)  
- Linux environment (GitHub Actions runner or local Linux VM)  
- At least 2 GB RAM (full pipeline uses < 1 GB)  

## Installation

```bash
# Clone the repository (replace <repo-url> with the actual URL)
git clone <repo-url>
cd projects/PROJ-296-predict-molecular-refractive-indices-/code

# Install dependencies
pip install -r requirements.txt

# Install CPU‑only PyTorch Geometric wheels
pip install torch-geometric torch-scatter torch-sparse torch-cluster torch-spline-conv -f https://data.pyg.org/whl/torch-2.0.0+cpu.html
```

## Step‑by‑Step Execution

### 1️⃣ Dataset Availability Check (always runs first)
```bash
python data/download.py --check-only
```
- Scans the Zenodo RI dataset and, if unavailable, triggers the synthetic QM9‑based benchmark.  
- Writes either `logs/dataset_unavailable.log` (real‑dataset failure) or proceeds automatically.

### 2️⃣ Download (run only if step 1 succeeded)
```bash
python data/download.py
```
- Downloads the selected dataset, records SHA‑256 under `state/ri_dataset.sha256`, and validates against `contracts/dataset.schema.yaml`.

### 3️⃣ Preprocess & Filter
```bash
python data/preprocess.py
```
- Parses SMILES, filters MW > 500 Da, applies temperature normalization, writes `data/processed/filtered.csv`.  
- Generates deterministic summary log `logs/preprocess_summary.log`.

### 4️⃣ Scaffold‑Based Splits
```bash
python data/split.py --folds 5 --repeats 5 --ratios 0.8 0.1 0.1
```
- Creates **25 independent** train/val/test CSVs under `data/splits/`.  
- Logs actions to `logs/split.log`.

### 5️⃣ Train the MPNN (CPU‑only)
```bash
for i in {1..5}; do
  for j in {1..5}; do
    python training/train.py --fold $i --repeat $j --epochs 200 --batch-size 32 --seed $((2000 + i*10 + j))
  done
done
```
- Saves model weights `models/mpnn_${i}_${j}.pt` and training logs.

### 6️⃣ Baseline Predictions
```bash
for i in {1..5}; do
  for j in {1..5}; do
    python models/baseline.py --fold $i --repeat $j
  done
done
```
- Generates `results/baseline_predictions_${i}_${j}.csv`.

### 7️⃣ Evaluation & Attribution
```bash
for i in {1..5}; do
  for j in {1..5}; do
    python training/evaluate.py --fold $i --repeat $j --model models/mpnn_${i}_${j}.pt
    python models/attribution.py --fold $i --repeat $j --model models/mpnn_${i}_${j}.pt --output results/attributions_${i}_${j}.csv
    python training/merge_predictions.py --fold $i --repeat $j
  done
done
```
- Produces `results/metrics_summary.csv`, `results/ssot_metrics.csv` (SSoT), parity plots, importance bar charts, attribution CSVs, and the combined prediction file `results/prediction_results_{i}_{j}.csv`.

### 8️⃣ Verify Success Criteria
```python
import pandas as pd
metrics = pd.read_csv('results/ssot_metrics.csv')
print(metrics[['fold','repeat','mae_gnn','mae_baseline','p_value','power']])

# Check variance of MAE across repeats
print("MAE variance:", metrics['mae_gnn'].var())
```
- Expected outputs:
  - **SC‑001**: Paired test p‑value (or Wilcoxon) reported; significance noted only if p < 0.05.  
  - **SC‑002**: MAE variance across repeats ≤ 0.01 (or reported value with disclaimer).  
  - **SC‑003**: Correlation results in `results/attribution_validation.csv`.  
  - **SC‑004**: Total runtime logged in `logs/runtime.log` (must be ≤ 6 h).  
  - **SC‑005**: Peak memory logged in `logs/memory_usage.log` (must be ≤ 7 GB).

## Notes on Scope
- **Dataset Limitation**: If the Zenodo RI dataset cannot be fetched, the pipeline falls back to the synthetic QM9‑based benchmark, ensuring the comparative modelling question can still be addressed.  
- All steps are deterministic and fully reproducible on a fresh GitHub Actions runner.  
- The quickstart commands assume a Unix‑like shell; Windows users can run the same Python scripts via PowerShell or WSL.
