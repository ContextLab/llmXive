# Implementation Plan: Structure-Only Surrogate Model for 2D Material Elastic Moduli

**Branch**: `PROJ-169-surrogate-elastic-moduli` | **Date**: 2026-10-16 | **Spec**: `spec.md`

## Overview

We will build a CPU‑only Graph Neural Network (GNN) surrogate that maps crystal‑structure graphs (derived from CIFs) to three elastic‑moduli targets (Young’s, shear, Poisson’s). The pipeline follows a strict, reproducible, single‑source data workflow, respects the 7 GB RAM limit, and implements all functional requirements (FR‑001…FR‑010) and success criteria (SC‑001…SC‑006).

## Deterministic Data Source Selection & Validation (Addresses methodology‑eee67652, data_resources‑f7480ec9, data_resources‑25b0cca1)

1. **Source order** (primary → fallbacks):  
   - Primary: `https://huggingface.co/datasets/bio-datasets/dft23-full/resolve/main/data/test-00000-of-00001-a791a8874f9adf69.parquet`  
   - Alternate‑1: `https://huggingface.co/datasets/sdmattpotter/dftest61523/resolve/main/data/train-00000-of-00001-17dbf6e61ca73a23.parquet`  
   - Alternate‑2: `https://huggingface.co/datasets/sdmattpotter/dftest61623/resolve/main/data/train-00000-of-00001-17dbf6e61ca73a23.parquet`

2. **Validation step** (Phase 0, `code/data/loader.py`):  
   - Attempt to download the primary URL. Load the parquet, compute SHA‑256 checksum, store under `data/raw/metadata.json`.  
   - Verify presence of **required columns**: `material_id`, `structure` (CIF string), `elastic_tensor` (6‑component list), `formula`, `space_group`, `is_2d`.  
   - **Deterministic fallback rule**: If the primary fails schema validation, log the reason and proceed to Alternate‑1, then Alternate‑2, applying the same checks. The chosen URL, its SHA‑256 checksum, download timestamp, and any fallback reason are recorded in `data/raw/metadata.json` for reproducibility (Constitution I).  
   - **Dataset‑fit abort**: If **none** of the three URLs contain *all* required columns, abort the pipeline with a clear “dataset‑variable mismatch” error and a **scope‑revision** flag. No synthetic data are generated; the project will require a different open dataset or a revised scope.  

## Phase 0 – Terminology Audit (FR‑006, FR‑009)

- `code/utils/verify_constitution_title.py` audits the renamed project title and all generated document titles, writes `data/results/constitution_title_audit.json` (schema `contracts/constitution_audit_schema.schema.yaml`), and exits 1 on any failure.

## Phase 1 – Data Pipeline (US1, FR‑001, FR‑002, FR‑007)

| Task | Script | Key Actions | Outputs |
|------|--------|-------------|---------|
| **T013d** | `code/data/loader.py` | Downloads selected parquet, validates schema, records checksum, parses CIFs with `pymatgen.CifParser`. | `data/raw/*.parquet`, `data/raw/metadata.json` |
| **T013d (cont.)** | `code/data/graph_builder.py` | Converts each structure to a PBC‑aware graph: 5 node features (atomic number, electronegativity, covalent radius, group, period); 2 edge features (distance, electronegativity difference). Stores all 6 elastic‑tensor components; flags eligibility (finite C11, C12, C22, C66). | `data/processed/graphs_v1.parquet` (validated by `contracts/dataset_schema.schema.yaml`) |
| **T013f** | `code/data/split_generator.py` | **Family definition** = space‑group + cation‑anion stoichiometry class (derived from `formula`). Clusters by this definition (no StructureMatcher). Performs a 70/15/15 family‑level split with seed 42, ensuring zero family leakage. Writes atomically (`temp.json → os.replace`). | `data/processed/split_indices.json` (schema `contracts/split_indices_schema.yaml`) |
| **T017b** | `code/model/splitter.py` | Loads `split_indices.json`, verifies disjoint families, size distribution, writes validation report. | `data/results/split_validation.json` (schema `contracts/split_validation.schema.yaml`) |

## Phase 2 – Training & Evaluation (US2, FR‑003, FR‑004, FR‑008, FR‑010)

| Task | Script | Highlights |
|------|--------|------------|
| **T018b** | `code/model/train.py` | CPU‑only (`torch.device("cpu")`), lightweight MPNN (2 MP layers, hidden ≤ 64). Wrapped in `tracemalloc` **and** OS‑level RSS sampling; records `peak_memory_gb` and asserts ≤ 7 GB (exit 1 otherwise). Saves checkpoint `data/processed/model_v1.pt` (includes disclaimer from `code/utils/disclaimer_template.py`). |
| **T018b (cont.)** | `code/model/cross_validation.py` | 5‑fold family‑stratified CV on train + val pool; reports mean ± std for Young’s/shear MAPE and Poisson MAE (saved in `training_logs.json`). |
| **T018b (cont.)** | `code/model/eval_runner.py` | Inference on test set (unseen families). Computes: <br>• MAPE for Young’s & shear (positive targets). <br>• MAE for Poisson. <br>• Baseline composition‑only linear regression (Magpie features). <br>• Relative reduction for Young’s, shear **and Poisson** against baseline. <br>• **Paired‑bootstrap (1 000 resamples) with Holm correction** across the three targets. <br>• **Intra‑family MAPE** = mean CV‑fold MAPE on families present in train/val (from cross‑validation). <br>• **Inter‑family MAPE** = test‑set MAPE on families **unseen** during training. <br>• Writes `predictions.json` (schema `contracts/predictions_schema.yaml`) and `generalization_metrics.json` (schema `contracts/results_schema.schema.yaml`). |
| **T022** | `code/model/inference_benchmark.py` | Times per‑material CPU inference on test set; records per‑material ms array, median, limit = 100 ms, and boolean `within_limit`. Merges into `generalization_metrics.json`. |
| **T001c** | `code/utils/compute_hashes.py` | Computes SHA‑256 hashes for all output artifacts and updates the project state file (`updated_at`). |
| **T001c** | `code/utils/compute_hashes.py` | (re‑listed for clarity) |

## Phase 3 – Feature Importance (US3, FR‑005, SC‑005)

| Task | Script | Method |
|------|--------|--------|
| **T003** | `code/analysis/feature_importance.py` | **Permutation importance** performed on each of the five node‑feature columns (features permuted across the entire test set). **Ablation**: retrain the model with the column removed; record ΔMAPE (≥ 2 percentage points required). **SHAP**: KernelExplainer applied to a 200‑sample subset using the *mean‑pooled node feature vector* as input. **Permutation test**: SHAP values compared to those from shuffled targets (p < 0.05). Qualifying descriptors must rank top‑5 by permutation importance, agree with SHAP ranking, and together contribute ≥ 70 % of total importance mass. Writes `feature_importance_report.md`. |

## Phase 4 – Finalization

1. `code/utils/disclaimer_template.py` provides `DISCLAIMER_TEXT` and `FEYNMAN_QUOTE`; imported by training and evaluation scripts (T046).  
2. `code/utils/compute_hashes.py` computes SHA‑256 hashes for all output artifacts and updates the project state file (`updated_at`).  
3. End‑to‑end integration test (`pytest tests/integration/`) runs the full pipeline and asserts all contract‑validated artifacts exist and exit codes are correct.

## Success‑Criterion Coverage (SC‑001…SC‑006)

| SC | Implementation |
|----|----------------|
| SC‑001 | Loader logs entry count; aborts if < 1 000 valid entries (recorded in `training_logs.json`). |
| SC‑002 | Eval runner computes relative reduction for Young’s, shear (MAPE) **and Poisson (MAE)**; gates `sc_002_baseline_reduction`. |
| SC‑003 | Inference benchmark enforces median < 100 ms; gate `sc_003_inference_time`. |
| SC‑004 | `train.py` records peak memory (tracemalloc + RSS) and asserts ≤ 7 GB; gate `within_limit` in `training_logs.json`. |
| SC‑005 | Feature‑importance script enforces ≥ 3 descriptors, top‑5 rank, ΔMAPE ≥ 2 pp, SHAP agreement, ≥ 70 % cumulative mass; gate `feature_importance_pass`. |
| SC‑006 | Final metrics (MAPE ≤ 15 % for Young’s/shear, MAE ≤ 0.05 for Poisson) are gated in `generalization_metrics.json`. |

## Statistical Rigor Summary

- **Multiple‑comparison correction**: Holm correction across the three target tests.  
- **Power / sample size**: Test‑set size reported; CV spread quantifies stability; any limitation is explicitly noted.  
- **Causal framing**: Strictly associational – surrogate interpolation of DFT data.  
- **Measurement validity**: Ground‑truth elastic tensors from the verified parquet; derived moduli computed via `code/physics/tensors.py`.  
- **Predictor collinearity**: Correlated descriptors reported descriptively; SHAP cross‑checks mitigate attribution bias.

## Compute Feasibility

All steps run on 2 CPU cores, ≤ 7 GB RAM, ≤ 6 h on GitHub Actions free tier. No GPU is required; the pipeline uses CPU‑first implementations of all methods.

## Constitution Check

The plan explicitly references each numbered principle in the project constitution (I–VII) to ensure reproducibility, verified accuracy, data hygiene, single source of truth, versioning discipline, numerical stability, and structural descriptor attribution. Each stage logs required metadata to satisfy these principles.  