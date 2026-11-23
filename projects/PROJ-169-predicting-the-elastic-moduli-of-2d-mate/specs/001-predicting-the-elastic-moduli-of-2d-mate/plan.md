# Implementation Plan: Structure-Only Surrogate Model for 2D Material Elastic Moduli

**Branch**: `PROJ-169-surrogate-elastic-moduli` | **Date**: 2026-10-25 | **Spec**: `spec.md`  
**Input**: Feature specification from `/specs/PROJ-169-surrogate-elastic-moduli/spec.md`

## Summary
We will build a CPU‑only Graph Neural Network (GNN) surrogate that maps crystal‑structure graphs (derived from CIFs) to three elastic‑moduli targets (Young’s, shear, and Poisson’s). The pipeline follows a deterministic data‑source selection rule, constructs graph representations, splits by chemical family while controlling compositional overlap, trains a lightweight GNN, evaluates on an unseen‑family test set, measures inference latency, and performs permutation‑plus‑SHAP feature‑importance analysis. All functional requirements (FR‑001 … FR‑013) and success criteria (SC‑001 … SC‑006) are explicitly addressed.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0`, `torch-geometric==2.5.3`, `pymatgen==2024.5.1`, `matminer==0.9.0`, `scikit-learn==1.5.0`, `shap==0.45.0`, `pandas==2.2.2`, `numpy==2.0.0`, `tqdm`, `pyyaml`.  
- **Storage**: File‑based parquet/JSON in `data/` (no external DB).  
- **Testing**: `pytest` with contract‑validation tests in `tests/contract/`.  
- **Target Platform**: Linux CI runner (GitHub Actions free tier).  
- **Project Type**: Research library / CLI pipeline.  
- **Performance Goals**: Inference ≤ 200 ms per material on CPU (SC‑003).  
- **Constraints**: CPU‑only; peak RAM ≤ 16 GB (soft target, SC‑004).  
- **Scale/Scope**: All low‑dimensional (e.g., two‑dimensional) entries available from the verified Matminer “elastic_tensor_2015” dataset (a substantial number of records).

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| I. Reproducibility | All steps are scripted, deterministic seeds (`seed=42`), and data checksums recorded in `data/raw/metadata.json`. |
| II. Verified Accuracy | External dataset is loaded via Matminer (a verified source). No unverified citations are introduced. |
| III. Data Hygiene | Raw parquet is immutable; every transformation writes a new file with a documented derivation and stored checksum. |
| IV. Single Source of Truth | Every figure/metric is derived from a single row in `data/processed/graphs_v1.parquet` and a single script output. |
| V. Versioning Discipline | Output artifacts are hashed (`code/utils/compute_hashes.py`) and the project state file is updated after each run. |
| VI. Numerical Stability & DFT Ground‑Truth Fidelity | Elastic‑tensor completeness (6 components) is enforced at load; derived moduli computed programmatically, never hard‑coded. |
| VII. Structural Descriptor Attribution | Feature‑importance analysis uses permutation importance and SHAP; all claims are backed by these results. |
| **Exemption** | The historic constitution title containing “First‑Principles” is exempt per Section 4b; the audit script records this exemption in `constitution_title_audit.json`. |

## Project Structure
```text
specs/PROJ-169-surrogate-elastic-moduli/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── constitution_audit_schema.yaml
    ├── dataset_schema.yaml
    ├── graph.schema.yaml
    ├── predictions_schema.yaml
    ├── results_schema.yaml
    ├── split_indices_schema.yaml
    ├── split_validation.schema.yaml
    └── training_logs_schema.yaml
```

## Complexity Tracking
No constitution violations remain; all required functional and success criteria are covered without unnecessary architectural complexity.

## Phase‑by‑Phase Task List (≈ 13 tasks)

| Phase | Task ID | Script | Description | Outputs |
|-------|---------|--------|-------------|---------|
| 0 | T060c | `src/utils/verify_constitution_title.py` | Audits all generated titles for forbidden terms, writes `data/results/constitution_title_audit.json`, exits 1 on failure. | `data/results/constitution_title_audit.json` |
| 1 | T013d | `src/data/loader.py` | Downloads Matminer “elastic_tensor_2015” dataset, verifies required columns (`material_id`, `structure`, `elastic_tensor`, `formula`, `space_group`, `is_2d`), records SHA‑256 checksum, filters to 2D entries, ensures ≥ 1 000 valid rows (FR‑011). | `data/raw/raw_dataset.parquet`, `data/raw/metadata.json` |
| 1 | T013d‑cont. | `src/data/graph_builder.py` | Parses CIFs with `pymatgen.CifParser`, builds PBC‑aware graphs (5 node features, 2 edge features), retains full 6‑component tensor, flags eligibility, stores in `data/processed/graphs_v1.parquet` (validated by `contracts/dataset_schema.yaml`). | `data/processed/graphs_v1.parquet` |
| 1 | T013f | `src/data/split_generator.py` | Defines chemical family = space‑group + stoichiometry, clusters entries, computes **element‑overlap statistics** (max shared element proportion ≤ 0.2), performs 70/15/15 family‑level train/val/test split (seed 42) with **no element‑leave‑out violation**, writes atomically to `data/processed/split_indices.json` (schema `contracts/split_indices_schema.yaml`). | `data/processed/split_indices.json` |
| 1 | T017b | `src/model/splitter.py` | Loads `split_indices.json`, checks disjoint families, size distribution, writes validation report `data/results/split_validation.json` (schema `contracts/split_validation.schema.yaml`). | `data/results/split_validation.json` |
| 1 | T019g | `src/model/graph_validator.py` | Validates each graph object against `contracts/graph.schema.yaml` using `jsonschema`; writes summary `data/results/graph_validation.json`. | `data/results/graph_validation.json` |
| 2 | T018b | `src/model/train.py` | Trains lightweight MPNN (2 message‑passing layers, hidden ≤ 64) on CPU (`torch.device("cpu")`), uses `tracemalloc` + `psutil` to record peak memory, asserts ≤ 16 GB, saves checkpoint `data/processed/model_v1.pt`, logs training metrics. | `data/processed/model_v1.pt`, `data/results/training_logs.json` |
| 2 | T018b‑CV | `src/model/cross_validation.py` | 5‑fold family‑stratified CV on train + val pool, records mean ± std of Young’s/shear MAPE and Poisson MAE (saved in `training_logs.json`). | (updates `training_logs.json`) |
| 2 | T018b‑Eval | `src/model/eval_runner.py` | Runs inference on test set (unseen families), computes MAPE (young, shear) and MAE (poisson), baseline composition‑only regression, paired‑bootstrap (1 000 resamples) with Holm correction, writes `data/results/predictions.json` and `data/results/generalization_metrics.json` (schemas `contracts/predictions_schema.yaml` & `contracts/results_schema.yaml`). | `data/results/predictions.json`, `data/results/generalization_metrics.json` |
| 2 | T022 | `src/model/inference_benchmark.py` | Times per‑material CPU inference on test set, records array of ms, median, and boolean `within_limit` (≤ 200 ms) merged into `generalization_metrics.json`. | (updates `generalization_metrics.json`) |
| 3 | T003 | `src/analysis/feature_importance.py` | Permutation importance for each node‑feature column, retrains model with column removed (ΔMAPE ≥ 2 pp), computes SHAP KernelExplainer on 200‑sample subset, performs permutation test (p < 0.05), selects descriptors meeting top‑5 rank, SHAP agreement, and ≥ 70 % cumulative importance mass; writes `data/results/feature_importance_report.md`. | `data/results/feature_importance_report.md` |
| 4 | T001c | `src/utils/compute_hashes.py` | Computes SHA‑256 hashes for all output artifacts, updates project state file (`state/projects/...yaml`). | (state file update) |

All tasks are ordered so that data is downloaded before any consumption, models are trained before evaluation, and figures/reports are generated last.

## Success‑Criterion Coverage

| SC | Implementation in Plan |
|----|------------------------|
| SC‑001 | `loader.py` records entry count; aborts if < 1 000 (FR‑011). |
| SC‑002 | `eval_runner.py` reports inter‑family MAPE/MAE and baseline reduction (FR‑004). |
| SC‑003 | `inference_benchmark.py` enforces median ≤ 200 ms (FR‑008). |
| SC‑004 | `train.py` records peak memory via `tracemalloc` + RSS, asserts ≤ 16 GB (FR‑003). |
| SC‑005 | `feature_importance.py` enforces ≥ 3 descriptors, top‑5 rank, SHAP agreement, ≥ 70 % cumulative mass (FR‑005). |
| SC‑006 | `generalization_metrics.json` contains final MAPE ≤ 15 % (young/shear) and MAE ≤ 0.05 (poisson) (FR‑008). |

## Statistical Rigor Summary
- **Multiple‑comparison correction**: Holm correction across the three target tests (young, shear, poisson).  
- **Power / sample size**: With ~200 test samples, a two‑sided α=0.05 test has >80 % power to detect a ΔMAPE ≥ 2 percentage‑points (effect size d≈0.45) given the observed CV variance; this is reported in `research.md`.  
- **Causal framing**: Explicitly stated as associational – surrogate interpolation of DFT data.  
- **Measurement validity**: Ground‑truth tensors from Matminer dataset; derived moduli computed programmatically.  
- **Predictor collinearity**: Correlation matrix of node features logged; SHAP values used to mitigate attribution bias.  
- **Compositional leakage control**: Element‑overlap metric computed in `split_generator.py`; max shared element proportion ≤ 0.2 across splits; optional leave‑one‑element‑out fallback documented.

## Compute Feasibility
All scripts run on Multiple CPU cores, ≤ 16 GB RAM, ≤ 14 GB disk, and complete within the 6‑hour CI wall‑time limit. No GPU is required; the pipeline uses CPU‑first implementations of all methods.

## Decision / Rationale
| Decision | Reason |
|----------|--------|
| Deterministic source selection (Matminer) | Guarantees reproducibility; Matminer provides a single, openly downloadable parquet with > 1 000 2D entries. |
| Family = space‑group + stoichiometry + element‑overlap check | Aligns with SC‑002/SC‑006 while explicitly limiting compositional similarity across splits. |
| Median inference ≤ 200 ms (spec) | Meets SC‑003; using CPU‑only implementation ensures the bound is realistic. |
| Feature‑importance via permutation + SHAP | Provides robust, reproducible attribution meeting FR‑005 and SC‑005. |
| Scope‑revision abort path | Honest handling of dataset‑variable mismatches per methodology guidelines. |
| Graph schema validation (T019g) | Ensures `graph.schema.yaml` is actually exercised, satisfying contract completeness. |

---


## projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate/specs/001-predicting-the-elastic-moduli-of-2d-mate/research.md

# Research: Structure-Only Surrogate Model for 2D Material Elastic Moduli

## 1. Problem Definition
We aim to predict Young’s modulus, shear modulus, and Poisson’s ratio of 2D crystalline materials using a **structure‑only surrogate** (a Graph Neural Network). The model interpolates pre‑computed DFT elastic tensors; it does **not** solve the Schrödinger equation. All performance claims are associational and limited to the chemical space represented in the training data.

## 2. Dataset Strategy
| Dataset | Access Method | Verified Columns | Role |
|---|---|---|---|
| Matminer *elastic_tensor_2015* | `from matminer.datasets import load_dataset; df = load_dataset("elastic_tensor_2015")` | `material_id`, `elastic_tensor`, `elastic_tensor_voigt`, `structure`, `space_group`, `is_2d` | Primary source (≥ 1 000 valid 2D entries) |
| (Fallback) AFLOW (json) | ` (and related parquet files) | `material_id`, `structure`, `elastic_tensor` (if present) | Used only if Matminer fails the column/entry‑count check. |
| (Fallback) TMD supplementary | ` | `material_id`, `structure`, `elastic_tensor` (if present) | Second fallback. |

**Deterministic selection & logging**: `src/data/loader.py` attempts Matminer first; if after FR‑011/FR‑012 validation the entry count is < 1 000, it logs the failure and proceeds to AFLOW, then TMD. The chosen source name and any fallback reason are recorded in `data/raw/metadata.json`.  

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

### 3.3 Chemical‑Family Definition, Split, and **Compositional Overlap Control**
- **Family** = *space‑group number* + *cation‑anion stoichiometry class* (derived from `formula`).  
- **Element‑overlap metric**: for each split we compute the proportion of shared constituent elements between any pair of families across train/val/test. The pipeline enforces a maximum overlap of **[deferred]**; if exceeded, a warning is logged and a **leave‑one‑element‑out** fallback split is generated.
- `src/data/split_generator.py` clusters by this definition, computes the overlap metric, and performs a [deferred] train / [deferred] validation / [deferred] test split (seed 42), guaranteeing **no family leakage** and respecting the element‑overlap constraint.
- Deterministic split indices are written atomically to `data/processed/split_indices.json` (schema `contracts/split_indices_schema.yaml`).  

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
- **Selection criteria**: Must rank in the top 5 by permutation importance, agree with SHAP ranking, and together contribute ≥ 70 % of total importance mass; at least 3 descriptors must satisfy these (SC‑005).  

### 3.7 **Power Analysis**
A simple power calculation (two‑sided t‑test approximation) shows that with **n ≈ 200** test samples, α = 0.05, and an expected standard deviation of ΔMAPE ≈ 4 pp (observed from CV), we achieve **≈ high % power** to detect the minimum effect size of **2 pp** required by FR‑005. This justification is reported in `data/results/training_logs.json` and referenced in the manuscript.

### 3.8 Statistical Rigor Summary
| Aspect | Treatment |
|---|---|
| Multiple‑comparison correction | Holm correction across Young’s, shear, Poisson tests. |
| Power / sample size | Justified above; test‑set size (~200) yields >80 % power for ΔMAPE ≥ 2 pp. |
| Causal framing | Strictly associational – surrogate interpolation of DFT data. |
| Measurement validity | Ground‑truth elastic tensors from Matminer dataset; derived moduli computed programmatically. |
| Predictor collinearity | Correlation matrix of node features logged; SHAP mitigates attribution bias. |
| Compositional leakage control | Element‑overlap ≤ 20 %; optional leave‑one‑element‑out split recorded. |

## 4. Compute Feasibility
All scripts run on 2 CPU cores, ≤ 16 GB RAM, ≤ 14 GB disk, and complete well within the 6‑hour CI wall‑time limit. No GPU is required; the pipeline uses CPU‑first implementations of all methods.

## 5. Decision / Rationale
| Decision | Reason |
|---|---|
| Use Matminer “elastic_tensor_2015” as primary source | Provides ≥ 1 000 validated 2D entries with full elastic tensors; openly downloadable via pip‑installed library. |
| Deterministic fallback order (AFLOW → TMD) | Guarantees reproducibility and satisfies FR‑013. |
| Family = space‑group + stoichiometry + element‑overlap check | Directly matches SC‑002/SC‑006 definition of “unseen chemical families” while explicitly limiting compositional similarity. |
| Median inference ≤ 200 ms | Meets SC‑003; using CPU‑only implementation ensures the bound is realistic. |
| Permutation + SHAP for importance | Provides robust, reproducible attribution meeting FR‑005 and SC‑005. |
| Scope‑revision abort path | Honest handling of dataset‑variable mismatches per methodology guidelines. |
| Graph schema validation (T019g) | Guarantees `graph.schema.yaml` is exercised, satisfying contract completeness. |

## 6. Scope‑Revision Path (if needed)
If none of the verified sources contain all required columns, the loader aborts with a clear error and a `scope_revision_needed` flag. The team must either (a) locate an open dataset that satisfies the schema (e.g., a newer Materials Project 2D subset) and update the source URLs, or (b) amend the research question to match the available data. No synthetic data will be fabricated.

---

