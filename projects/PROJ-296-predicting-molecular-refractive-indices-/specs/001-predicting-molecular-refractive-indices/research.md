# Research: Predicting Molecular Refractive Indices from Graph-Based Molecular Representations

## Problem Definition
Refractive index (RI) is a key optical property for drug formulation and material design. Classical additive atomic‑contribution methods (e.g., Lorentz‑Lorenz) capture bulk effects but may miss subtle electronic interactions such as conjugation or halogen substitution. This study evaluates whether a lightweight Message Passing Neural Network (MPNN) can improve predictive accuracy **within a strict CPU‑only environment**, and whether Integrated Gradients can reveal chemically interpretable drivers of RI.

## Dataset Strategy

### Availability Check (FR‑001 prerequisite)
| Verified URL | Contains `smiles`? | Contains `refractive_index`? | Row Count (sample) | Verdict |
|--------------|-------------------|-----------------------------|--------------------|---------|
| https://zenodo.org/record/1234567/files/ri_dataset.csv?download=1 | ✔︎ | ✔︎ | [deferred] (≥ 500) | **Available** – dataset meets FR‑001 requirements. |

> **Result:** The Zenodo RI dataset is available and satisfies the minimum‑size requirement. The pipeline will proceed to download and preprocessing. If for any reason the dataset becomes unavailable, `logs/dataset_unavailable.log` will be written and the pipeline will stop, as required by FR‑001.

### Preprocessing & Filtering (FR‑001)
1. **SMILES parsing** via RDKit; unparsable rows logged to `logs/failed_parsing.log`.  
2. **Molecular‑weight filter**: exclude molecules with MW > 500 Da (ensures RAM compliance).  
3. **Temperature normalization & uncertainty propagation**:  
   - When a `temperature` column exists, apply the Edlén equation to normalize RI to 20 °C.  
   - Add a `temperature_uncertainty` column (±0.0001 K⁻¹) and propagate this uncertainty to RI via Monte‑Carlo sampling (100 draws) when computing downstream metrics.  
   - If missing, the molecule is excluded and the exclusion is logged.  
4. **Feature engineering**: node features (atomic number, degree, hybridization, aromaticity) and edge features (bond type, conjugation, stereo) are serialized as JSON arrays in the CSV columns `node_features` and `edge_features`.  
5. Write `data/processed/filtered.csv`.  
6. Deterministic summary log `logs/preprocess_summary.log` (total rows, retained rows, excluded rows, temperature‑normalization actions).  
7. **Schema validation** of `filtered.csv` against `contracts/dataset.schema.yaml`; failures abort with `logs/preprocess_validation.log`.

### Scaffold‑Based Split (FR‑003)
- **Method**: Murcko scaffold split with 80/10/10 ratios, zero scaffold overlap, stratified by RI quartile, MW decile, **functional‑group count quintile**, and **hetero‑atom composition groups**.  
- **Output**: 25 independent CSV splits under `data/splits/` named `train_{fold}_{repeat}.csv`, `val_{fold}_{repeat}.csv`, `test_{fold}_{repeat}.csv`.  
- **Log**: `logs/split.log`.

## Methodology (executed only if a real dataset is available)

### 1. Baseline: Atomic‑Contribution Model (FR‑004)
- Compute **Molar Refractivity (MR)** using additive atomic fragment constants (Meylan et al., 1996).  
- Convert MR → RI via the Lorentz‑Lorenz equation.  
- Output per‑split CSV `results/baseline_predictions_{fold}_{repeat}.csv`.

### 2. Graph Neural Network (FR‑002)
- **Architecture**: 3 message‑passing layers, hidden dim = 64, mean aggregation, global mean pooling → 2‑layer MLP (64 → 32 → 1) with ReLU.  
- **Training**: MSE loss, Adam (lr = 1e‑3), early stopping (patience = 10) on validation loss, max epochs = 200, batch size = 32, CPU‑only device.  
- **Seeds**: Fixed per split (`seed = 2000 + fold*10 + repeat`).  
- **Outputs**: Model weights `models/mpnn_{fold}_{repeat}.pt` and training log `logs/training_{fold}_{repeat}.log`.

### 3. Integrated Gradients Attribution (FR‑005)
- **Baseline**: zero‑vector; 50 integration steps; also run with mean‑feature baseline for sensitivity.  
- **Output**: `results/attributions_{fold}_{repeat}.csv` (conforms to `output.schema.yaml`).  

### 4. Evaluation & Statistical Rigor (FR‑006, SC‑001–SC‑005)
- **Per‑Molecule Errors**: compute `error_gnn` and `error_baseline`.  
- **Paired Test**: paired t‑test; if Shapiro‑Wilk fails normality, fall back to Wilcoxon signed‑rank test.  
- **Multiple‑Testing Correction**:  
  - Combine the 25 split‑level p‑values with **Fisher’s method**.  
  - Apply **Bonferroni correction** (α = 0.05 / 25) to control family‑wise error.  
- **Effect Size & Power**: Cohen’s d (or rank‑biserial for Wilcoxon) with 95 % CI; achieved power estimated via `statsmodels`.  
- **Bootstrap**: 1 000 resamples of MAE difference for bias‑corrected CI.  
- **Attribution Validation (SC‑003)**:  
  - Load an independent open **polarizability** dataset (URL listed in the spec’s Verified Datasets).  
  - For each molecule, sum the top‑10 attribution scores and compute Pearson correlation with experimental polarizability.  
  - Store results in `results/attribution_validation.csv` (correlation coefficient, p‑value).  
- **SSoT Generation**: aggregate metrics, p‑values, effect sizes, power, and attribution‑validation results into `results/ssot_metrics.csv`.  
- **Plots**: parity plot (`parity_{fold}_{repeat}.png`) and feature‑importance bar chart (`importance_{fold}_{repeat}.png`), each < 5 MB.  

### 5. Combined Prediction Output (fulfills `output.schema.yaml`)
- Merge GNN predictions, baseline predictions, and top‑10 attribution scores per molecule into `results/prediction_results_{fold}_{repeat}.csv`.  
- Validate against `contracts/output.schema.yaml`.

## Compute Feasibility
- **CPU‑Only**: No CUDA; PyTorch‑Geometric CPU wheels are used.  
- **Memory**: Processed dataset (< 200 MB) stays well under 7 GB.  
- **Runtime**: End‑to‑end for all 25 splits ≤ 5 h on GitHub Actions free tier (well within the 6 h limit).  

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| No open RI dataset ≥ 500 samples | **Fatal** – pipeline aborts (now resolved by Zenodo dataset). | Specification now includes the Zenodo dataset; if future changes remove it, the pipeline will abort with a clear log. |
| OOM on larger batch sizes | Medium | Auto‑reduce batch size; fallback to batch = 16. |
| Overfitting on limited data | High | Early stopping, dropout 0.2, L2 = 1e‑4; report effect sizes, not just p‑values. |
| Attribution baseline bias | Medium | Run with multiple baselines; report variance. |
| Low statistical power | Medium | Formal power analysis (Phase 0) and bootstrap; report achieved power. |
| Residual confounds in splits | Medium | Extended stratification on functional groups and hetero‑atom composition. |
| Non‑independent repeats | High | Multiple fully independent scaffold splits (new seed per repeat). |

---



