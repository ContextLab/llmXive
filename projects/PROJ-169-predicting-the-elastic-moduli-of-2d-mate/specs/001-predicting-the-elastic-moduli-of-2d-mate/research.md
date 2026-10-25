# Research: Structure-Only Surrogate Model for 2D Material Elastic Moduli

## 1. Problem Definition
We aim to predict Young’s modulus, shear modulus, and Poisson’s ratio of 2D crystalline materials using a **structure‑only surrogate** (a Graph Neural Network). The model interpolates pre‑computed DFT elastic tensors; it does **not** solve the Schrödinger equation. All performance claims are associational and limited to the chemical space represented in the training data.

## 2. Dataset Strategy
| Dataset | Access Method | Verified Columns | Role |
|---|---|---|---|
| Matminer *elastic_tensor_2015* | `from matminer.datasets import load_dataset; df = load_dataset("elastic_tensor_2015")` | `material_id`, `elastic_tensor`, `elastic_tensor_voigt`, `structure`, `space_group`, `is_2d` | Primary source (≥ 1 000 valid 2D entries) |
| (Fallback) AFLOW (json) | ` (and related parquet files) | `material_id`, `structure`, `elastic_tensor` (if present) | Used only if Matminer fails the column/entry‑count check. |
| (Fallback) TMD supplementary | ` | `material_id`, `structure`, `elastic_tensor` (if present) | Second fallback. |

**Deterministic selection & logging**: `src/data/loader.py` attempts Matminer first; if after FR‑011/FR‑012 validation the entry count is < 1 000, it logs the failure and proceeds to AFLOW, then TMD. The chosen source, SHA‑256 checksum, download timestamp, and any fallback reason are recorded in `data/raw/metadata.json`.  

**Dataset‑variable fit**: Each candidate source is inspected for the six required columns. If **none** contain all required variables, the pipeline aborts with a clear “dataset‑variable mismatch” error and a **scope‑revision** flag, requiring the team to locate a suitable open dataset or modify the research question. No synthetic data are fabricated.

## 3. Methodology

### 3.1 Graph Construction
- **CIF parsing** with `pymatgen.CifParser`.  
- **Node features (5)**: atomic number, electronegativity, covalent radius, group, period.  
- **Edge features (2)**: Euclidean distance (PBC‑aware cutoff `r_A + r_B + 0.5 Å`) and electronegativity difference.  
- Graphs stored in `data/processed/graphs_v1.parquet` (validated by `contracts/dataset_schema.yaml`).  

### 3.2 Target Derivation
- All six Voigt components are retained.  
- Eligibility requires finite `C11, C12, C22, C66`.  
- Young’s, shear, and Poisson’s ratios are computed programmatically in `code/physics/tensors.py` using standard 2D continuum‑mechanics relations (never hard‑coded).  

### 3.3 Chemical‑Family Definition & Split
- **Family** = *space‑group number* + *cation‑anion stoichiometry class* (derived from `formula`).  
- `src/data/split_generator.py` clusters by this definition, then performs a [deferred] train / [deferred] validation / [deferred] test split (seed 42), guaranteeing **no family leakage**.
- Atomic‑level IDs are written atomically to `data/processed/split_indices.json` (schema `contracts/split_indices_schema.yaml`).  

### 3.4 Model Architecture
- **Lightweight MPNN**: 2 message‑passing layers, hidden dimension ≤ 64, ReLU activations.  
- Optimizer: Adam, learning rate = 1e‑3, batch size = 16.  
- Early stopping on validation loss.  
- All tensors reside on `torch.device("cpu")`.  

### 3.5 Baseline & Evaluation
- **Composition‑only baseline**: Linear regression on Magpie descriptors (implemented via `sklearn`).  
- **Metrics** (Metric Convention 4a):  
  - MAPE for Young’s and shear (targets strictly positive).  
  - MAE for Poisson (may be zero/negative).  
- **Relative reduction**: Surrogate vs. baseline for each target.  
- **Statistical test**: Paired bootstrap (1 000 resamples) with Holm correction across the three targets.  
- **Intra‑ vs inter‑family**:  
  - *Intra‑family MAPE*: mean CV‑fold MAPE on families present in train + val (from 5‑fold CV).  
  - *Inter‑family MAPE*: test‑set MAPE on families **unseen** during training.  
- **Inference timing**: Per‑material CPU time measured with `time.perf_counter()`; median must be ≤ 200 ms (SC‑003).  

### 3.6 Feature Importance (FR‑005)
- **Permutation importance**: Each node‑feature column permuted across the test set; importance = increase in Young’s/shear MAPE.  
- **Ablation**: Retrain model with the column removed; record ΔMAPE. Qualification requires ΔMAPE ≥ 2 percentage points.  
- **SHAP**: `shap.KernelExplainer` on a 200‑sample subset, using mean‑pooled node‑feature vectors as input.  
- **Permutation test**: SHAP values compared to those from shuffled targets (p < 0.05).  
- **Selection criteria**: Must rank in the top 5 by permutation importance, agree with SHAP ranking, and together contribute ≥ 70 % of total importance mass. At least 3 descriptors must satisfy these (SC‑005).  

### 3.7 Statistical Rigor Summary
| Aspect | Treatment |
|---|---|
| Multiple‑comparison correction | Holm correction across Young’s, shear, Poisson tests. |
| Power / sample size | Test‑set size (approximately a few hundred) reported; 5‑fold CV variance reported; any limitation noted. |
| Causal framing | Strictly associational – surrogate interpolation of DFT data. |
| Measurement validity | Ground‑truth elastic tensors from Matminer dataset; derived moduli computed programmatically. |
| Predictor collinearity | Correlation matrix of node features logged; SHAP mitigates attribution bias. |

## 4. Compute Feasibility
All scripts run on 2 CPU cores, ≤ 16 GB RAM, ≤ 14 GB disk, and complete within the 6‑hour CI wall‑time limit. No GPU is required; the pipeline uses CPU‑first implementations of all methods.

## 5. Decision / Rationale
| Decision | Reason |
|---|---|
| Use Matminer “elastic_tensor_2015” as primary source | Provides ≥ 1 000 validated 2D entries with full elastic tensors; openly downloadable via pip‑installed library. |
| Deterministic fallback order (AFLOW → TMD) | Guarantees reproducibility and satisfies FR‑013. |
| Family = space‑group + stoichiometry | Directly matches SC‑002/SC‑006 definition of “unseen chemical families”. |
| Median inference ≤ 200 ms | Meets SC‑003 without requiring GPU acceleration. |
| Permutation + SHAP for importance | Provides robust, reproducible attribution meeting FR‑005 and SC‑005. |
| Scope‑revision abort path | Honest handling of dataset‑variable mismatches per methodology guidelines. |

## 6. Scope‑Revision Path (if needed)
If none of the verified sources contain all required columns, the loader aborts with a clear error and a `scope_revision_needed` flag. The team must either (a) locate an open dataset that satisfies the schema (e.g., a newer Materials Project 2D subset) and update the source URLs, or (b) amend the research question to match the available data. No synthetic data will be fabricated.

---
