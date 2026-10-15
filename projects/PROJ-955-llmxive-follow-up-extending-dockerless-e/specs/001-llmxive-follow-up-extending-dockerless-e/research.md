# Research: 001-static-dynamic-gap-analysis

## Background & Motivation
Prior work on “Dockerless: Environment‑Free Program Verifier” showed that static analyses can approximate program correctness without execution. However, the fidelity of static structural features (Control‑Flow Graphs, Call Graphs) to the **semantic** outcome of LLM‑generated patches remains unclear. This study quantifies that fidelity and isolates concrete code behaviours that cause static‑dynamic divergence.

## Dataset Strategy
| Dataset | Source URL (verified) | Format | Relevant Fields | Notes |
|---------|----------------------|--------|-----------------|-------|
| SWE‑Gym (code‑search) | https://huggingface.co/datasets/OpenHands/SWE-Gym-code-search/resolve/main/data/train-00000-of-00001.parquet | Parquet | `patch_id`, `language`, `source_code`, `test_result` | Contains Python & C++ patches with sandboxed test logs (`pass`/`fail`). |
| Multi‑SWE‑RL (OpenMathLib) | https://huggingface.co/datasets/ByteDance-Seed/Multi-SWE-RL/resolve/main/data_20240601_20250331/c/OpenMathLib__OpenBLAS_dataset.jsonl | JSONL | `patch_id`, `language`, `source_code`, `test_result` | Provides additional C++ patches and varied dynamic behaviours. |

Both datasets are openly downloadable via `datasets.load_dataset(..., streaming=True)`. The pipeline streams each file to stay within the available RAM budget, only materializing per‑patch JSON graphs and feature rows.

### Variable Fit Check
- **Predictors**: node degree statistics, path length, recursion depth, external‑call count (derived from static graphs).  
- **Outcome**: `test_result` (binary `pass` / `fail`).  
All required variables are present; a quick schema inspection found no missing predictor columns.

### Label Distribution & Class Balance
After ingestion we compute the pass/fail counts per dataset and overall. If one class exceeds 80 % of the total, we will enable class‑weighting in model training to mitigate imbalance effects. The distribution is logged in `reports/label_distribution.csv` and discussed in the final report.

## Methodology

### 1. Static Graph Generation
- **Python patches** → `pycg` (v0.2.0) to emit CFG and CG JSON.  
- **C++ patches** → `clang-query` (LLVM 16) with custom AST matcher scripts to emit equivalent JSON structures.  
- Unparsable patches (syntax errors, missing includes) are logged, skipped, and the **skip rate** is recorded for bias assessment (see Phase 2).

### 2. Feature Extraction
From each graph we compute a 7‑dimensional vector:
1. `node_count` – size of the graph, a proxy for program size.  
2. `edge_count` – connectivity, reflecting control‑flow complexity.  
3. `mean_degree` – average branching factor.  
4. `max_degree` – worst‑case branching, often linked to complex conditionals.  
5. `avg_shortest_path` – overall path compactness, related to deep nesting.  
6. `recursion_depth` – presence of recursive structures, known to affect runtime behaviour.  
7. `external_call_count` – number of calls to symbols not defined locally, a direct indicator of dynamic dispatch or external API usage.  

These metrics have been used in prior static‑analysis studies as interpretable proxies for program complexity and external interaction, making them suitable for assessing semantic correctness. All features are z‑score normalized before model training.

### 3. Predictive Modeling
- **Primary model**: Random Forest (200 trees, `n_jobs=2`).  
- **Baseline**: Logistic Regression (liblinear).  
- **Stratified split**: 80/20 split stratified jointly on `language` (python/cpp) and `dataset_origin` (SWE‑Gym / Multi‑SWE‑RL) to control for confounding effects. Language and dataset are also added as one‑hot covariates to the feature matrix; optional per‑language models are trained for secondary analysis.  
- **Evaluation**: Compute AUC, Precision, Recall, Confusion Matrix.  
- **Multiple‑comparison correction**: Not needed for primary metrics; Wald test p‑values are Bonferroni‑adjusted.

### 4. Statistical Significance
- Fit a Logistic Regression on the full feature set (including language and dataset covariates).  
- Extract Wald z‑statistics and corresponding p‑values.  
- Apply Bonferroni correction across the 9 coefficients.  
- Report significance at α = 0.05 (SC‑005).

### 5. Divergence Analysis
- Identify False Positives (FP) and False Negatives (FN).  
- Apply rule‑based pattern matching on the static graphs to label each error case with one of the taxonomy items:  
  - `dynamic_dispatch` (function‑pointer or virtual‑method calls)  
  - `external_api` (calls to symbols not defined locally)  
  - `concurrency_race` (presence of `std::thread`, `async`, `multiprocessing`)  
  - `mocked_io` (file/DB access nodes flagged as mocks)  
  - `other`  
- Compute frequency distribution (SC‑003) and overall divergence rate (FP + FN / total parsable patches) (SC‑002).

### 6. Performance Monitoring
- Each pipeline stage is timed; peak RAM recorded via `psutil`.  
- Abort if total runtime > 6 h or RAM > 7 GB (SC‑004).  
- Include the **skip‑rate bias metric** from Phase 2 in `reports/performance.yaml`.

## Decision / Rationale
- **CPU‑first**: All tools (`pycg`, `clang-query`, scikit‑learn) have fully functional CPU implementations. No GPU is required, satisfying the free‑tier runner constraints.  
- **Streaming data**: To respect disk/RAM limits, we stream the parquet/JSONL datasets and write per‑patch artifacts incrementally.  
- **Sample fallback**: If memory profiling indicates > 7 GB usage during graph extraction, the pipeline will automatically switch to a stratified [deferred] sample (seed = 42) and note the reduced statistical power in the final report.

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

