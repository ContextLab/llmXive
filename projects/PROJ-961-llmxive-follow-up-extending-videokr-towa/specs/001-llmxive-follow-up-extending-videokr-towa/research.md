# Research: Video Reasoning Threshold Analysis

## 1. Problem Definition
We examine whether increasing structural complexity—measured as the shortest‑path hop count between entities in the ground‑truth knowledge graph—produces a non‑linear “reasoning cliff” in video‑QA accuracy. The hypothesis: beyond a certain hop count, accuracy drops sharply rather than following a smooth logistic decline.

## 2. Dataset Strategy

### Verified Sources & Data Availability Gate
The specification requires the **VideoKR‑SFT** dataset, which currently has **no verified public download URL**. Consequently the pipeline cannot fetch it automatically. Instead, the researcher must manually place the following files in `data/raw/`:

- `videokr_sft.jsonl` (question‑answer records, including a binary correctness label)  
- `knowledge_graph.json` (the static KG used for hop counting)

`code/ingest/download_data.py` checks for the presence of these files; if either is missing it aborts with error `E_DATA_MISSING` and a clear instruction to supply the data. This respects the CI sandbox constraints (no credentialed or gated sources).

### Two‑Stage Sampling & Power Analysis (addresses FR‑011)
1. **Pilot Phase** – Load a random pilot of a sufficiently large sample of records to estimate the distribution of `chain_length`.  
2. **Power Calculation** – Using `statsmodels.stats.power.NormalIndPower`, we compute the minimum detectable odds‑ratio for a binary outcome at α = 0.0167 (Bonferroni‑adjusted for up to 3 knot tests) and target power = 0.80. The result is a required per‑bin sample of ≈ 45; we round up to **≥ 50** and record the exact value in `power_analysis.json`.  
3. **Oversampling Phase** –  
   - All records with `chain_length ≥ 3` are retained (if any).  
   - Randomly sample enough 1‑hop and 2‑hop records to reach at least 50 examples per bin, aiming for a total of on the order of several thousand rows.  
   This guarantees statistical power while staying within the allocated RAM budget.

## 3. Methodology

### 3.1 Structural Annotation (FR‑001, FR‑002)
- **Deterministic Entity Linking** (`code/utils/entity_linker.py`):  
  - Normalizes strings (lower‑case, strip punctuation).  
  - Attempts **exact match** to node names in `knowledge_graph.json`.  
  - If no exact match, applies **Levenshtein distance ≤ 2** as a fuzzy fallback.  
  - **No embedding‑based similarity** is used (satisfies T102).  
- **Hop Counting** (`networkx` BFS) computes the shortest path length between the linked question entity and the answer entity.  
- **Outputs**: `annotated_videokr.csv` with columns `question_id`, `question_text`, `answer_text`, `correctness`, `predicted_correctness`, `chain_length`, `chain_bin`, `status` (FR‑001, FR‑002).

### 3.2 Power Analysis (FR‑011)
Implemented in `code/analysis/power_analysis.py`. The script writes `power_analysis.json` containing the computed minimum `n_per_bin` and the assumed effect size (Cohen’s h = 0.1). The downstream bin‑size check (FR‑003) reads this value.

### 3.3 Accuracy Stratification (FR‑003)
- Group by `chain_bin` (`'1'`, `'2'`, `'3+'`).  
- Compute per‑bin accuracy = mean(`correctness`).  
- If any bin contains **< n_per_bin** samples, issue a warning, merge the bin with the next higher bin, and flag the knot for deferral in the permutation test.  
- Generates `accuracy_binned.png` (bar chart) and `accuracy_binned.csv` (summary table).

### 3.4 Threshold Detection (FR‑004) – Permutation GLM Change‑Point Test & LRT
- **Null Model**: Binomial logistic regression of `correctness` on `chain_length` **plus** covariates (`question_difficulty`, `video_duration`, `answer_type`).  
- **Alternative Model**: Piecewise logistic regression with a knot at candidate `k` (k ∈ {2, 3, 4}).  
- **Test Statistic**: Likelihood‑ratio (Δ log‑likelihood).  
- **Permutation**: Shuffle `correctness` labels repeatedly (e.g., many thousands of times); for each permutation repeat the grid search and record the maximal Δ log‑likelihood.  
- **Multiple Comparisons**: Bonferroni correction (multiply raw p‑value by 3) or use the max‑statistic null distribution.  
- **Significance**: Cliff declared if corrected p < 0.05.  
- **Outputs**: `threshold_results.json` (FR‑004, SC‑002).

### 3.5 Continuous Visualization (FR‑005)
Scatter plot of raw binary `correctness` vs. `chain_length` with a LOESS smooth trend line. Outputs: `accuracy_vs_hop_raw.png` and `accuracy_vs_hop_raw.csv`.

### 3.6 Sensitivity & Confound Analysis (FR‑008, SC‑003, SC‑006)
- **Binning Schemes**: Run the full permutation‑LRT pipeline under three binning definitions:  
  1. `[1,2,3+]`  
  2. `[1,2,3,4+]`  
  3. `[1,2,3,4,5+]`  
- **Covariate Adjustment**: All models include the three covariates to guard against omitted‑variable bias.  
- **Robustness Criterion**: The “cliff” must be significant (p < 0.05 after correction) in **≥ 2 of 3** schemes (SC‑003).  
- **Disconnection Bias Check**: Compute per‑bin rates of `status = "disconnected"` or `"mapping_failure"`; recompute accuracy assuming those records are incorrect. If the cliff vanishes, set `bias_flag = true`.  
- **Outputs**: `sensitivity_analysis.json` (per‑scheme knots, p‑values, robustness flag) and updated `threshold_results.json` with `robustness_status` and `bias_flag`.

### 3.7 Predictive Model & LRT (FR‑010)
- **Baseline Model**: TF‑IDF vectorization of `question_text` + `answer_text`, logistic regression (`solver='lbfgs'`).  
- **Extended Model**: Same features plus `chain_length` as a numeric predictor.  
- **LRT**: Compare baseline vs. extended models; write statistic, p‑value, and conclusion to `model_lrt_results.json` (SC‑006).

### 3.8 Runtime & Memory Logging (FR‑006, FR‑009)
- `code/main.py` measures wall‑clock time; writes `runtime_log.json` with `total_seconds` and `limit_exceeded` (SC‑004).  
- `code/utils/memory_tracker.py` records peak RAM usage; writes `memory_log.json` with `peak_gb` and `limit_exceeded` (SC‑005).

## 4. Statistical Rigor (addresses SC‑002, SC‑003, SC‑006)
- **Model Choice**: Binomial logistic GLM respects the binary outcome.  
- **Multiple Comparisons**: Handled via Bonferroni or max‑statistic permutation null.  
- **Power**: Guaranteed ≥ 50 samples per bin by design; documented in `power_analysis.json`.  
- **Observational Nature**: Findings are framed as associational; no causal claims are made.  
- **Collinearity**: `chain_length` is the primary predictor; covariates are orthogonal by construction.

## 5. Compute Feasibility
- **CPU‑only** implementation; all libraries run on the GitHub Actions runner.  
- **Memory**: Graph stored as adjacency list; dataset streamed or sampled to stay ≤ 5 GB.  
- **Runtime**: Estimated ≤ 2 hours with **2 000** permutations (parallelized across two cores). This satisfies the CI runtime limit.

## 6. Risk Management
| Risk | Mitigation |
|------|------------|
| Missing verified VideoKR‑SFT source | Data‑availability gate aborts with clear message; user must supply the files manually. |
| Embedding‑based linking (T102) | Deterministic exact‑match + bounded Levenshtein replaces any embedding path; unit tests verify correct behavior. |
| Insufficient high‑hop samples | Power analysis guarantees ≥ 50; if still insufficient, the affected knot is deferred and logged. |
| Out‑of‑memory on full graph | Load only the induced subgraph for sampled nodes; fallback to streaming mode. |
| Permutation test exceeds CI time | `NUM_PERMUTATIONS` is configurable (default = 2 000); a logged warning appears if reduced. |

---

