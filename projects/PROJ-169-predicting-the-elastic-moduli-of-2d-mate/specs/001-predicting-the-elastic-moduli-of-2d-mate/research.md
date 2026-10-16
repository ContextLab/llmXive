# Research: Structure-Only Surrogate Model for 2D Material Elastic Moduli

## 1. Problem Definition

Predict Young's modulus, shear modulus, and Poisson's ratio of 2D crystalline materials with a structure‑only GNN surrogate trained on pre‑computed DFT elastic tensors. The model interpolates; it does **not** solve the Schrödinger equation. All claims are associational and valid only within the training chemical space.

## 2. Dataset Strategy

We use a **single canonical source per run** (see deterministic selection order below). The verified parquet files are openly downloadable from HuggingFace; however, none of the three listed datasets have been confirmed to contain **2D crystal structures** with the required columns (`structure` as CIF, `elastic_tensor` with 6 components, `space_group`, `is_2d`). Consequently, the pipeline adopts a **scope‑revision abort path**: if the primary source fails schema validation, the loader proceeds to the alternates, and if **all** sources lack the required variables, the pipeline aborts with a clear “dataset‑variable mismatch” error and a **scope‑revision** flag, requiring the project to locate an appropriate open dataset or amend the research question.

| Dataset | Verified URL | Role |
|---|---|---|
| Primary | https://huggingface.co/datasets/bio-datasets/dft23-full/resolve/main/data/test-00000-of-00001-a791a8874f9adf69.parquet | First attempt (primary) |
| Alternate‑1 | https://huggingface.co/datasets/sdmattpotter/dftest61523/resolve/main/data/train-00000-of-00001-17dbf6e61ca73a23.parquet | Fallback if primary fails schema check |
| Alternate‑2 | https://huggingface.co/datasets/sdmattpotter/dftest61623/resolve/main/data/train-00000-of-00001-17dbf6e61ca73a23.parquet | Second fallback |

**Deterministic selection & logging**: The pipeline attempts the primary URL first; on schema failure it logs the reason and proceeds to Alternate‑1, then Alternate‑2. The chosen URL, its SHA‑256 checksum, download timestamp, and any fallback reason are recorded in `data/raw/metadata.json` for reproducibility (Constitution I).

**Dataset‑variable fit (honest assessment)**: Each parquet is inspected for the required columns (`material_id`, `structure` (CIF), `elastic_tensor` (6‑component list), `formula`, `space_group`, `is_2d`). The loader **aborts** with a clear “dataset‑variable mismatch” report if **none** contain all required variables. In that case a **scope‑revision** is required (the project must either locate an open dataset that satisfies the schema or amend the research question). No synthetic or toy data are generated.

## 3. Methodology

### 3.1 Graph Construction
- **Node features (5)**: atomic number, electronegativity, covalent radius, group, period.  
- **Edge features (2)**: bond distance (PBC‑aware cutoff `r_A + r_B + 0.5 Å`), electronegativity difference.  
- Graphs are built with `pymatgen.CifParser` and stored in `data/processed/graphs_v1.parquet`.

### 3.2 Targets
- All six Voigt components are retained; eligibility requires finite `C11, C12, C22, C66`.  
- Young’s, shear, and Poisson’s ratios are derived in `code/physics/tensors.py` via standard 2D continuum‑mechanics relations (never hard‑coded).

### 3.3 Model
- Lightweight MPNN (2 message‑passing layers, hidden ≤ 64, CPU‑only).  
- Early stopping on validation loss; Adam lr = 1e‑3, batch = 16.

### 3.4 Family Definition & Split
- **Family** = *space‑group number* + *cation‑anion stoichiometry class* (derived from the chemical formula).  
- `code/data/split_generator.py` clusters by this unified family definition (no StructureMatcher) and performs a 70/15/15 family‑level split (seed 42) guaranteeing no family appears in more than one split.  
- `code/model/splitter.py` validates disjointness and writes `split_validation.json`.

### 3.5 Baseline & Evaluation
- **Composition‑only baseline**: linear regression on Magpie descriptors.  
- **Metrics** (Section 4a): MAPE for Young’s & shear (strictly positive), MAE for Poisson.  
- **Relative reduction**: computed for Young’s, shear (MAPE) **and Poisson (MAE)** against the baseline.  
- **Statistical test**: paired bootstrap (1 000 resamples) with Holm correction across the three targets.  
- **Intra‑ vs inter‑family**: intra‑family MAPE = mean CV‑fold MAPE on families present in train/val; inter‑family MAPE = test‑set MAPE on unseen families.  
- **Inference timing**: per‑material CPU time measured; median must be < 100 ms.

### 3.6 Feature Importance (FR‑005)
- **Permutation importance**: each of the five node‑feature columns is permuted across the test set; importance is the increase in MAPE.  
- **Ablation**: the model is retrained with the column removed; ΔMAPE ≥ 2 percentage points is required for qualification.  
- **SHAP**: `shap.KernelExplainer` applied to a 200‑sample subset using the *mean‑pooled node feature vector* as input.  
- **Permutation test**: SHAP values are compared to those from shuffled targets (p < 0.05).  
- **Selection criteria**: top‑5 by permutation importance, SHAP rank agreement, ΔMAPE ≥ 2 pp, and cumulative contribution ≥ 70 % of total importance mass. At least 3 descriptors must satisfy these conditions (SC‑005).

### 3.7 Statistical Rigor
| Aspect | Treatment |
|---|---|
| Multiple comparisons | Holm correction across Young’s, shear, Poisson tests |
| Power / sample size | Test‑set size reported; CV spread quantifies stability; any limitation explicitly noted |
| Causal framing | Associational only – surrogate interpolation of DFT data |
| Measurement validity | Ground‑truth elastic tensors from the verified parquet; derived moduli computed programmatically |
| Predictor collinearity | Correlated descriptors reported descriptively; SHAP cross‑checks mitigate attribution bias |

## 4. Compute Feasibility

All stages run on a modest number of CPU cores, ≤ 7 GB RAM, ≤ 14 GB disk, ≤ 6 h on GitHub Actions free tier. No GPU is required; the pipeline uses CPU‑first implementations of all methods.

## 5. Decision / Rationale

| Decision | Reason |
|---|---|
| Deterministic source order & validation | Guarantees reproducibility; avoids silent fallback to unsuitable data. |
| Unified family definition (space‑group + stoichiometry) | Aligns with SC‑002/SC‑006 and removes ambiguity with StructureMatcher. |
| Poisson MAE relative‑reduction metric | Fulfills SC‑002 requirement for all three targets. |
| Explicit permutation/ablation on node‑feature columns + SHAP on graph‑level aggregation | Provides a well‑defined, reproducible feature‑importance pipeline for GNNs. |
| Intra‑ vs inter‑family metrics derived from CV folds and test set | Makes intra‑family MAPE computable despite test set containing only unseen families. |
| Scope‑revision abort path | Honest handling of the case where none of the verified parquet files contain the required columns. |


## 6. Scope‑Revision Path (if needed)

If the dataset‑variable abort is triggered, the pipeline stops and emits a clear error message in `code/data/loader.py`. The project team must then either (a) locate an open dataset that satisfies the required schema (e.g., a Materials Project 2D subset with elastic tensors) and update the source URLs, or (b) amend the research question to a scope that matches the available data. No synthetic data will be fabricated.  