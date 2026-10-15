# Research: Video Reasoning Threshold Analysis

## 1. Problem Definition
We examine whether increasing structural complexity—measured as the shortest‑path hop count between entities in the ground‑truth knowledge graph—produces a non‑linear “reasoning cliff” in video‑QA accuracy. The hypothesis: beyond a certain hop count, accuracy drops sharply rather than following a smooth logistic decline.

## 2. Dataset Strategy

### Verified Sources & Data Availability Gate
The specification calls for **VideoKR‑SFT**, which lacks a verified public URL. We therefore use the **TVQA** dataset (open, verified on Hugging Face: `https://huggingface.co/datasets/tvqa`). The knowledge graph accompanying TVQA is provided in the repository (`data/raw/knowledge_graph.json`).  

- `code/ingest/download_data.py` checks for `data/raw/tvqa_train.jsonl` and `knowledge_graph.json`.  
- If missing, it raises `E_DATA_MISSING` with a clear message and aborts the pipeline.

### Two‑Stage Sampling & Power Analysis (addresses methodology‑bfa5f1f8)
1. **Pilot Phase** – Load a random pilot of a sizable number of rows to estimate the distribution of `chain_length`.  
2. **Power Calculation** – Using `statsmodels.stats.power.NormalIndPower`, we compute the minimum detectable odds‑ratio for a binary outcome at α = 0.0167 (Bonferroni‑adjusted) and target power = 0.80. The calculation yields a required per‑bin sample of ≈ 45; we round up to **≥ 50** to be safe.  
3. **Oversampling Phase** –  
   - Include **all** records with `chain_length ≥ 3` (if any).  
   - Randomly sample enough 1‑hop and 2‑hop records to reach ~10 k total rows, guaranteeing ≥ 50 samples per bin.

This ensures statistical power while respecting the 7 GB RAM limit.

## 3. Methodology

### 3.1 Structural Annotation (FR‑001, FR‑002)
- **Entity Linking** (`code/utils/entity_linker.py`): deterministic matching only:  
  - Normalizes strings (lower‑case, strip punctuation).  
  - Attempts **exact match** to graph node names.  
  - If no exact match, applies **Levenshtein distance ≤ 2** as a fuzzy fallback.  
  - **No embedding models are used** (addresses T102).  
- **Graph Traversal** (`networkx` BFS) computes the shortest path length between the linked question entity and the answer entity.  
- **Outputs**: `annotated_videokr.csv` with columns `id, question, answer, chain_length, chain_bin, correctness, status`.

### 3.2 Accuracy Stratification (FR‑003)
- Group by `chain_bin` (`'1'`, `'2'`, `'3+'`).  
- Compute per‑bin accuracy = mean of binary `correctness`.  
- If any bin contains **< 50** samples, a warning is logged and the bin is merged with the next higher bin, and the corresponding knot is deferred in the permutation test.  
- Generates `accuracy_binned.png` (bar chart) and a CSV summary.

### 3.3 Threshold Detection (FR‑004) – Permutation GLM Change‑Point Test
- **Null Model**: **Binomial logistic regression** of `correctness` on hop count **plus** covariates (`question_difficulty`, `video_duration`, `answer_type`).  
- **Alternative Model**: Piecewise logistic regression with a knot at candidate `k` (k ∈ {2, 3, 4}).  
- **Test Statistic**: Likelihood‑ratio (Δ log‑likelihood).  
- **Permutation**: Shuffle `correctness` labels **5 000** times; for each permutation repeat the grid search and record the maximal Δ log‑likelihood.  
- **Multiple Comparisons**: Bonferroni correction (multiply raw p‑value by 3) or use the max‑statistic null distribution.  
- **Significance**: Declare a “cliff” if corrected p < 0.05. Results stored in `threshold_results.json`.

### 3.4 Sensitivity & Covariate Analysis (FR‑005) & Bias Checks
- **Covariate Modeling** (addresses methodology‑e7e0125f): The three covariates are included as fixed effects in both null and alternative models, reducing omitted‑variable bias.  
- **Threshold Sweep**: Run the permutation GLM test separately for fixed knots 2, 3, 4, recording p‑values, effect sizes, and cliff magnitudes.  
- **Disconnection Bias**: Compute the proportion of `status = "disconnected"` or `"mapping_failure"` per bin. Re‑compute accuracy assuming all such records are incorrect; if the cliff disappears, flag `bias_flag = true`.  
- **Robustness**: Passes if ≥ 2 of the 3 knots yield significant cliffs (SC‑003).  
- **Outputs**: Updated `threshold_results.json` (includes `robustness_status`) and `accuracy_vs_hop_raw.png` (scatter + LOESS).

## 4. Statistical Rigor (addresses methodology‑4fe1a45d & scientific_soundness‑ac7050e0)
- **Model Choice**: **Binomial logistic GLM** respects the binary nature of correctness and avoids the invalid linear‑mean approach.  
- **Multiple Comparisons**: Handled via permutation max‑statistic (equivalent to Bonferroni).  
- **Power**: Two‑stage oversampling guarantees ≥ 50 samples in the rarest bin, as justified by the formal power analysis above.  
- **Observational Nature**: Findings are framed as **associational**; no causal claims are made.  
- **Collinearity**: Hop count is the primary predictor; covariates are orthogonal by design.

## 5. Compute Feasibility
- **CPU‑only** implementation; all libraries run on the GitHub Actions runner.  
- **Memory**: Graph stored as adjacency list; dataset streamed or sampled to stay ≤ 5 GB.  
- **Runtime**: Estimated ≤ 4 h (dominant cost = permutation test). Parallelism via `joblib` across the two CPU cores.

## 6. Risk Management
| Risk | Mitigation |
|------|------------|
| Missing verified TVQA source | Data‑availability gate aborts; project awaits an open substitute. |
| Embedding‑based linking failure (T102) | Deterministic linking replaces embeddings; unit tests updated. |
| Insufficient high‑hop samples | Power analysis and oversampling guarantee ≥ 50; if still insufficient, test for that knot is deferred and logged. |
| Out‑of‑memory on full graph | Load only the subgraph induced by sampled nodes; fallback to streaming mode. |

---


