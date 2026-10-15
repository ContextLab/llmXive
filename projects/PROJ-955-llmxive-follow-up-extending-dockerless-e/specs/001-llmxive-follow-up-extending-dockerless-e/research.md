# Research: 001-static-dynamic-gap-analysis

## Background & Motivation
Prior work on “Dockerless: Environment‑Free Program Verifier” demonstrated that static analyses can approximate program correctness without executing code. However, the fidelity of static structural features (Control‑Flow Graphs, Call Graphs) to the **semantic** outcome of LLM‑generated patches remains unclear. This study quantifies that fidelity and isolates concrete code behaviours that cause static‑dynamic divergence.

## Dataset Strategy
| Dataset | Source URL (verified) | Format | Relevant Fields | Notes |
|---------|----------------------|--------|-----------------|-------|
| SWE‑Gym (code‑search) | https://huggingface.co/datasets/OpenHands/SWE-Gym-code-search/resolve/main/data/train-00000-of-00001.parquet | Parquet | `patch_id`, `language`, `source_code`, `test_result` | Contains Python & C++ patches with sandboxed test logs (`pass`/`fail`). |
| Multi‑SWE‑RL (OpenMathLib) | https://huggingface.co/datasets/ByteDance-Seed/Multi-SWE-RL/resolve/main/data_20240601_20250331/c/OpenMathLib__OpenBLAS_dataset.jsonl | JSONL | `patch_id`, `language`, `source_code`, `test_result` | Provides additional C++ patches and varied dynamic behaviours. |

Both datasets are openly downloadable via `datasets.load_dataset(..., streaming=True)`. The pipeline will stream each file to stay within the 7 GB RAM limit, only materializing per‑patch JSON graphs and feature rows.

### Variable Fit Check
- **Predictors**: node degree statistics, path length, recursion depth, external‑call count (derived from static graphs).  
- **Outcome**: `test_result` (binary `pass` / `fail`).  
All required variables are present; no missing predictor columns have been observed in a quick schema inspection.

## Methodology

### 1. Static Graph Generation
- **Python patches** → `pycg` (v0.2.0) to emit CFG and CG in JSON.  
- **C++ patches** → `clang-query` (LLVM 16) with custom AST matcher scripts to emit equivalent JSON structures.  
- Unparsable patches (syntax errors, missing includes) are logged and excluded.

### 2. Feature Extraction
From each graph we compute a 7‑dimensional vector:
1. `node_count`  
2. `edge_count`  
3. `mean_degree`  
4. `max_degree`  
5. `avg_shortest_path`  
6. `recursion_depth`  
7. `external_call_count`  

All features are numeric and normalized (z‑score) before model training.

### 3. Predictive Modeling
- **Primary model**: Random Forest (200 trees, `n_jobs=2`).  
- **Baseline**: Logistic Regression (liblinear).  
- **Evaluation**: Stratified 80/20 split, compute AUC, Precision, Recall, Confusion Matrix.  
- **Multiple‑comparison correction**: Not needed for primary metrics; Wald test p‑values are Bonferroni‑adjusted.

### 4. Statistical Significance
- Fit a Logistic Regression on the full feature set.  
- Extract Wald z‑statistics and corresponding p‑values.  
- Apply Bonferroni correction across the 7 coefficients.  
- Report significance at α = 0.05 (SC‑005).

### 5. Divergence Analysis
- Identify False Positives (FP) and False Negatives (FN).  
- Apply rule‑based pattern matching on the static graphs to label each error case with one of the taxonomy items:
  - `dynamic_dispatch`
  - `external_api`
  - `concurrency_race`
  - `mocked_io`
  - `other`
- Compute the frequency distribution (SC‑003) and overall divergence rate (FP + FN / total parsable patches) (SC‑002).

### 6. Performance Monitoring
- Each pipeline stage is timed; peak RAM recorded via `psutil`.  
- Abort if total runtime > 6 h or RAM > 7 GB (SC‑004).  

## Decision / Rationale
- **CPU‑first**: All tools (`pycg`, `clang-query`, scikit‑learn) have fully functional CPU implementations. No GPU is required, satisfying the free‑tier runner constraints.  
- **Streaming data**: To respect the disk/ RAM limits, we stream the parquet/jsonl datasets and write per‑patch artifacts incrementally.  
- **Sample fallback**: If memory profiling indicates > 7 GB usage during graph extraction, the pipeline will automatically switch to a stratified 10 % sample (seed = 42) and note the power limitation in the final report.

## Expected Deliverables
- JSON CFG/CG files for each parsable patch.  
- `features/static_features.csv` containing one row per patch.  
- Trained model files (`models/rf.pkl`, `models/lr.pkl`).  
- Evaluation report (`reports/evaluation.csv`, `reports/roc_curve.png`).  
- Wald test table (`reports/wald_test.csv`).  
- Error‑case taxonomy table and distribution plot.  
- Performance summary (`reports/performance.yaml`).  
- Final markdown synthesis (`reports/final_report.md`).

All artifacts will be reproducible on a fresh GitHub Actions runner, adhering to the project constitution.

---
