# Implementation Plan: Structure-Only Surrogate Model for 2D Material Elastic Moduli

**Branch**: `PROJ-169-surrogate-elastic-moduli` | **Date**: 2026-10-16 | **Spec**: `spec.md`  
**Input**: Feature specification from `spec.md`

## Summary
Implement a CPU‑only Graph Neural Network (GNN) surrogate that maps crystal‑structure graphs (derived from CIF files) to three elastic‑moduli targets (Young’s, shear, Poisson’s). The pipeline ingests a single verified DFT parquet dataset (if available), builds PBC‑aware graphs, creates a family‑based train/validation/test split, trains a lightweight GNN under a 7 GB RAM ceiling, evaluates against a composition‑only baseline and a composition‑only GNN control, benchmarks inference time, and produces Integrated‑Gradients plus SHAP feature‑importance analysis. All steps are gated by hard exit codes and contract‑validated JSON artifacts.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.*` (CPU wheels), `torch-geometric==2.5.*`, `pandas`, `pyarrow`, `scikit-learn`, `pymatgen`, `shap`, `captum` (for Integrated Gradients), `huggingface_hub` (pinned in `code/requirements.txt`)  
- **Storage**: File‑system under `data/` (raw, processed, results)  
- **Testing**: `pytest` + contract tests against `contracts/*.schema.yaml`  
- **Target Platform**: Linux GitHub Actions free tier (2 CPU, 7 GB RAM, 14 GB disk, ≤6 h)  
- **Constraints**: CPU‑only, single canonical source, ≤7 GB peak memory, inference < 100 ms, no “First‑Principles” terminology in model description (FR‑006).  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| I. Reproducibility | Fixed random seeds (`code/utils/seeds.py`); deterministic dataset download with SHA‑256 checksum; full pipeline orchestrated by `code/main_pipeline.py`. |
| II. Verified Accuracy | All citations limited to verified open datasets (if none are available the pipeline aborts). |
| III. Data Hygiene | Raw parquet never mutated; each transformation writes a new file (e.g., `graphs_v1.parquet`, `split_indices.json`). Checksums recorded. |
| IV. Single Source of Truth | Every metric in `data/results/*.json` is produced by a single script; no hand‑typed numbers. |
| V. Versioning Discipline | Artifacts hashed and recorded in the project state file; any change updates `updated_at`. |
| VI. Numerical Stability & DFT Fidelity | Loader filters for entries with a full 6‑component elastic tensor; `code/physics/tensors.py` computes Young’s, shear, Poisson’s from the tensor using standard continuum‑mechanics formulas (no hard‑coding). |
| VII. Structural Descriptor Attribution | Feature‑importance step uses Integrated Gradients (Captum) **and** SHAP (KernelExplainer); multicollinearity screened via VIF > 5 before importance ranking. |

## Functional Requirement Coverage
| FR ID | Requirement | Plan Phase / Task |
|-------|-------------|-------------------|
| FR‑001 | Ingest CIF + elastic tensors, build graphs | Phase 1 – `loader.py` + `graph_builder.py` (Tasks T013d1‑d4) |
| FR‑002 | Split generator clustering by chemical family | Phase 1 – `split_generator.py` (Task T013f) |
| FR‑003 | Train lightweight GNN on CPU, enforce 7 GB limit | Phase 2 – `train.py` (Task T018b) |
| FR‑004 | Evaluate against composition‑only baseline, report relative MAPE reduction | Phase 2 – `eval_runner.py` (Task T018b) |
| FR‑005 | Compute Integrated Gradients **and** SHAP values for structural descriptors (no permutation importance) | Phase 3 – `feature_importance.py` (Task T003) |
| FR‑006 | Generate constitution‑title audit, abort on forbidden terms | Phase 0 – `verify_constitution_title.py` (Task T060c) |
| FR‑007 | Persist model weights, split indices, validation metrics | Phase 2‑4 – `train.py`, `splitter.py`, `eval_runner.py` (Tasks T018b, T017b) |
| FR‑008 | Baseline GNN trained on composition‑only features (control) | Phase 2 – `train_composition_gnn.py` (Task T018c) |
| FR‑009 | Power analysis for detecting ≥10 % MAPE reduction | Phase 5 – `power_analysis.py` (Task T005) |

## Success‑Criterion Coverage
| SC ID | Requirement | Plan Phase / Task |
|-------|-------------|-------------------|
| SC‑001 | Process ≥1 000 valid 2D entries (or all if fewer) | Phase 1 – loader validates count, logs shortfall |
| SC‑002 | ≥10 % relative MAPE reduction vs composition baseline on unseen families, **statistically significant** (paired‑bootstrap p < 0.05) | Phase 2 – `eval_runner.py` computes baseline and surrogate MAPE, runs **1 000 paired‑bootstrap resamples**, applies Holm‑Bonferroni correction; gates on ≥10 % reduction **and** p < 0.05 |
| SC‑003 | Inference time < 100 ms per material on CPU | Phase 2 – `inference_benchmark.py` records `avg_inference_time_ms`; gate fails if > 100 ms |
| SC‑004 | Peak training memory ≤ 7 GB | Phase 2 – `train.py` wraps training in `tracemalloc`; gate fails if limit exceeded |
| SC‑005 | At least 3 structural descriptors identified via Integrated Gradients **and** SHAP (significant IG attribution & top‑3 SHAP magnitude) after VIF screening | Phase 3 – `feature_importance.py` merges IG and SHAP, applies VIF > 5 filter, gates on ≥3 descriptors |
| SC‑006 | Power analysis shows ≥80 % power to detect a [deferred] MAPE reduction given the actual test‑set size (≥150 samples) | Phase 5 – `power_analysis.py` runs **1 000 simulations**; aborts if estimated power < 0.8 |

## Tasks (ordered to respect data flow)

### Phase 0 – Constitution & Title Audit
- **T060c** – `code/utils/verify_constitution_title.py`  
  * Scans `constitution.md` for forbidden terms “First‑Principles” or “Schrödinger”.  
  * Writes `data/results/constitution_title_audit.json` conforming to `contracts/constitution_audit_schema.schema.yaml`.  
  * Exits 1 on FAIL, 0 on PASS (hard gate for all downstream tasks).

### Phase 1 – Data Pipeline (US1)
1. **T013d1** – `code/data/loader.py`  
   * Downloads the primary parquet URL (if none are verified the script aborts with a clear error).  
   * Verifies SHA‑256 checksum, validates required columns, filters to 2D structures with complete elastic tensors.  
   * Writes raw file to `data/raw/` and logs entry count (SC‑001).  
2. **T013d2‑d4** – `code/data/graph_builder.py`  
   * Parses CIFs with `pymatgen.CifParser`.  
   * Constructs PBC‑aware atom graphs (node + edge features).  
   * Saves `data/processed/graphs_v1.parquet` (validated by `contracts/dataset_schema.schema.yaml`).  
3. **T013f** – `code/data/split_generator.py`  
   * Loads structures, clusters by *family* = (space group + stoichiometry class) using `StructureMatcher`.  
   * Performs train/val/test split with pinned seed (70/15/15 %). No family appears in more than one split (leakage check).  
   * Atomically writes `data/processed/split_indices.json`.  
4. **T017b** – `code/model/splitter.py`  
   * Reads `split_indices.json`, checks family disjointness, size distribution.  
   * Writes `data/results/split_validation.json` (schema `contracts/split_validation.schema.yaml`).  

### Phase 2 – Model Training & Evaluation (US2)
5. **T018b** – `code/model/train.py`  
   * Enforces `torch.device("cpu")` and asserts `torch.cuda.is_available() is False`.  
   * Wraps training loop in `tracemalloc`; records `peak_memory_gb`.  
   * Saves `data/processed/model_v1.pt` (state dict + hyperparameters + disclaimer).  
   * Generates `data/results/training_logs.json`.  
   * Fails with exit 1 if `peak_memory_gb > 7`.  
6. **T018b (cont.)** – `code/model/eval_runner.py`  
   * Loads test split, runs inference, computes per‑property MAPE, RMSE, **1 000 bootstrap 95 % CI** (resamples).  
   * Trains a Magpie linear‑regression baseline, computes relative MAPE reduction.  
   * Performs **paired‑bootstrap hypothesis test** (1 000 resamples) with Holm‑Bonferroni correction; requires p < 0.05 and ≥10 % reduction (SC‑002).  
   * Writes `data/results/predictions.json` and `data/results/generalization_metrics.json` (schema `contracts/results_schema.schema.yaml`).  
7. **T018c** – `code/model/train_composition_gnn.py` (new)  
   * Same lightweight MPNN architecture but **only** composition‑derived node features, no edge features.  
   * Produces `data/results/composition_gnn_metrics.json` for internal comparison.  
8. **T022** – `code/model/inference_benchmark.py`  
   * Times inference over the test set, writes `data/results/inference_benchmark.json`.  
   * Fails if `avg_inference_time_ms > 100`.  

### Phase 3 – Analysis (US3)
9. **T003** – `code/analysis/feature_importance.py`  
   * **Integrated Gradients** (Captum) on node/edge embeddings (**Monte-Carlo samples**

A set of Monte-Carlo samples will be drawn.).  
   * **SHAP** (KernelExplainer) on a random **Sample subset**

A subset of the samples will be selected for detailed analysis.; reports mean absolute SHAP magnitude per descriptor.  
   * **Variance Inflation Factor (VIF)** computed for all structural descriptors; descriptors with VIF > 5 are removed before importance ranking.  
   * Merges IG attributions and SHAP magnitudes, selects descriptors that survive VIF screening and rank in the top‑3 by **both** metrics.  
   * Writes `data/results/feature_importance_report.md`.  
   * SC‑005 gate checks ≥3 descriptors.  

### Phase 4 – Power Analysis
10. **T005** – `code/utils/power_analysis.py` (new)  
    * Simulates paired‑bootstrap power for detecting a [deferred] MAPE reduction given the actual test‑set size.  
    * Uses **1 000 simulation runs**; reports estimated power in `data/results/power_analysis.json`.  
    * Aborts if estimated power < 0.8 (SC‑006).  

### Phase 5 – Finalization
11. **T046** – `code/utils/disclaimer_template.py` (added)  
    * Defines `DISCLAIMER_TEXT` (“This surrogate interpolates DFT‑computed elastic tensors; it does not solve the Schrödinger equation.”) and `FEYNMAN_QUOTE`.  
    * Imported by `train_logger.py` and `eval_runner.py`.  
12. **T008a** – End‑to‑end integration test (subset) via `pytest tests/integration/`.  
13. **T001c** – Compute and record content hashes for all new artifacts; update project state `updated_at`.  

All tasks are designed to complete well within the 6‑hour CI window on the free‑tier runner. No GPU escape hatch is required because the model size (≤ 64 hidden units, batch ≤ 32) is fully tractable on CPU.

## Statistical Rigor Summary
- **Bootstrap resamples**: 1 000 for confidence intervals, 1 000 for paired‑bootstrap hypothesis testing.  
- **Multiple‑comparison correction**: Holm‑Bonferroni applied to the three target‑property tests.  
- **Power analysis**: 1 000 simulations; success criterion ≥ 80 % power for detecting a [deferred] MAPE reduction with the actual test‑set size.
- **Causal framing**: All statements explicitly labeled *associational*.  
- **Collinearity control**: VIF screening (> 5) before importance ranking; no permutation importance used.  

## Compute Feasibility
- **CPU‑first**: All steps run on CPU; model fits comfortably within 7 GB RAM.  
- **Memory management**: Streaming parquet load for ingestion; `tracemalloc` monitors training memory.  
- **Inference speed**: Expected < 50 ms per graph on the runner (well under the 100 ms SC‑003 limit).  
- **No GPU escape hatch**: Model size and batch configuration are chosen to be fully tractable on CPU; therefore no GPU fallback is required.
