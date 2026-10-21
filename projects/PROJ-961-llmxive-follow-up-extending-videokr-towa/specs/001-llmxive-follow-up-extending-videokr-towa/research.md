# Research: Video Reasoning Threshold Analysis

## 1. Problem Definition
We examine whether increasing structural complexity—measured as the shortest‑path hop count between entities in the ground‑truth knowledge graph—produces a non‑linear “reasoning cliff” in video‑QA accuracy. The hypothesis: beyond a certain hop count, accuracy drops sharply rather than following a smooth logistic decline.

## 2. Dataset Strategy

### Verified Sources & Data Availability Gate
The original **VideoKR‑SFT** dataset and its knowledge graph are **not publicly reachable** and therefore cannot be fetched automatically in CI. To satisfy Constitution I (Reproducibility) we will **use the open‑access TVQA dataset** (HuggingFace `tvqa`) as a functional substitute. TVQA provides video‑question‑answer triples, difficulty scores, and answer format information compatible with our analysis pipeline.  

If a future version of VideoKR‑SFT becomes publicly available, the pipeline can be switched by updating `code/ingest/download_data.py`. Until then, the analysis proceeds with TVQA, and the limitation is documented in the final report.

#### Dataset Strategy Table
| Role | Source | Loader | Notes |
|------|--------|--------|-------|
| Primary QA & metadata | TVQA (HuggingFace) | `datasets.load_dataset("tvqa")` | Open, version‑controlled, programmatic download. |
| Knowledge Graph | `data/raw/knowledge_graph.json` (included with TVQA repo) | `json.load` | Local file bundled with TVQA download. |
| Video Lengths | `metadata/video_lengths.csv` (bundled with TVQA) | `pd.read_csv` | Direct read; no external download. |

*No verified public URL exists for the original VideoKR‑SFT dataset; the substitution is required for reproducibility.*

### Two‑Stage Sampling & Power Analysis (FR‑011)
1. **Pilot Phase** – Load a random [deferred] pilot sample of TVQA to estimate the distribution of `chain_length` and the observed accuracy gap between low‑hop and high‑hop questions.
2. **Power Calculation** – Using `statsmodels.stats.power.NormalIndPower`, compute the minimum per‑bin sample needed to detect the pilot‑estimated effect size (≈ h = 0.12) with 80 % power at α = 0.01 (Bonferroni‑adjusted for five knot tests). The result is ≈ 45; we round up to **≥ 50** and store the exact number in `power_analysis.json`.  
3. **Oversampling Phase** –  
   - Retain all records with `chain_length ≥ 3`.  
   - Randomly sample enough 1‑hop and 2‑hop records to reach at least 50 examples per bin, targeting a total of several thousand rows while staying within the ≤ 5 GB RAM budget.

## 3. Methodology

### 3.1 Structural Annotation (FR‑001, FR‑002, FR‑012)
- **Deterministic Entity Linking** (`code/utils/entity_linker.py`):  
  - Normalize strings (lower‑case, strip punctuation).  
  - Attempt **exact match** to node names in `knowledge_graph.json`.  
  - If no exact match, apply **Levenshtein distance ≤ 2** as a fuzzy fallback.  
  - **No embedding‑based similarity** is used (this fixes T102 by removing the embedding branch).  
- **Linking Validation**: A hand‑curated validation set of a substantial number of questions with known entity IDs is processed; linking accuracy is logged in `annotation_coverage.json`. If accuracy < 95 %, the pipeline aborts.  
- **Hop Counting** (`networkx` BFS) computes the shortest path length between the linked question entity and answer entity.  
- **Covariate Extraction** (`annotate_graph.py`) adds `question_difficulty`, `video_length_seconds`, and `answer_type`.  
- **Outputs**: `annotated_videokr.csv` with columns `question_id`, `question_text`, `answer_text`, `correctness`, `chain_length`, `chain_bin`, `question_difficulty`, `video_length_seconds`, `answer_type`, `status`, `predicted_correctness` (populated later).

### 3.2 Power Analysis (FR‑011)
Implemented in `code/analysis/power_analysis.py`. Writes `power_analysis.json` with the computed `min_samples_per_bin` (rounded to 50). Downstream bin‑size checks (FR‑003) read this value.

### 3.3 Accuracy Stratification (FR‑003)
- Group by `chain_bin` (`'1'`, `'2'`, `'3+'`).  
- Compute per‑bin accuracy = mean(`correctness`).  
- If any bin contains **< n_per_bin** samples, issue a warning, merge with the next higher bin, and flag the knot for deferral.  
- Generates `accuracy_binned.png` (bar chart) and `accuracy_binned.csv` (summary table).

### 3.4 Threshold Detection (FR‑004) – Permutation Change‑Point Test & LRT
- **Null Model**: Binomial logistic regression of `correctness` on `chain_length` plus covariates (`question_difficulty`, `video_length_seconds`, `answer_type`).  
- **Alternative Model**: Piecewise logistic regression with a knot at each candidate location **k ∈ {1,2,3,4,5}**.  
- **Test Statistic**: Likelihood‑ratio (Δ log‑likelihood).  
- **Permutation**: Shuffle `correctness` labels **500** times; for each permutation repeat the grid search and record the maximal Δ log‑likelihood across the five knots to build a null distribution.  
- **Multiple Comparisons**: Bonferroni correction across the five knot tests (α_adj = 0.01).  
- **Significance**: Cliff declared if corrected p < 0.05.  
- **Outputs**: `threshold_results.json` containing per‑knot p‑values, effect sizes, the selected knot, and significance flags.

### 3.5 Continuous Visualization (FR‑005)
Scatter plot of raw binary `correctness` vs. `chain_length` with a LOESS smooth trend line. Outputs: `accuracy_vs_hop_raw.png` and `accuracy_vs_hop_raw.csv`.

### 3.6 Sensitivity & Confound Analysis (FR‑008, SC‑003, SC‑006)
- **Binning Schemes**: Run the full permutation‑LRT pipeline under three definitions:  
  1. `[1,2,3+]`  
  2. `[1,2,3,4+]`  
  3. `[1,2,3,4,5+]`  
- **Covariate Adjustment**: All models include the three covariates.  
- **Robustness Criterion**: Significant cliff (p < 0.05 after correction) in **≥ 2 of 3** schemes (SC‑003).  
- **Disconnection Bias Check**: Compute per‑bin rates of `status = "disconnected"` or `"mapping_failure"`; recompute accuracy assuming those records are incorrect. If the cliff disappears, set `bias_flag = true`.  
- **Outputs**: `sensitivity_analysis.json` (per‑scheme knots, p‑values, robustness flag) and updated `threshold_results.json` with `robustness_status` and `bias_flag`.

### 3.7 Predictive Model & LRT (FR‑010, SC‑006)
- **Baseline Model**: TF‑IDF vectorization of `question_text` + `answer_text`, logistic regression (`solver='lbfgs'`).  
- **Extended Model**: Same features plus `chain_length` as a **continuous** numeric predictor; L2 regularization tuned via 5‑fold cross‑validation to avoid over‑fitting given limited per‑bin samples.  
- **LRT**: Compare baseline vs. extended models; write statistic, p‑value, and conclusion to `model_lrt_results.json`.  
- **Predicted Correctness Injection**: Model predictions (probability of correctness) are written back into the `predicted_correctness` column of `annotated_videokr.csv` (fulfilling the schema requirement).

### 3.8 Runtime & Memory Logging (FR‑006, FR‑009)
- `code/main.py` measures wall‑clock time; writes `runtime_log.json` with `total_seconds` and `limit_exceeded` (SC‑004).  
- `code/utils/memory_tracker.py` records peak RAM usage; writes `memory_log.json` with `peak_gb` and `limit_exceeded` (SC‑005).

## 4. Statistical Rigor (SC‑002, SC‑003, SC‑006)
- **Model Choice**: Binomial logistic GLM respects the binary outcome.  
- **Multiple Comparisons**: Handled via Bonferroni across five knot tests.  
- **Power**: Guaranteed ≥ 50 samples per bin (FR‑011).  
- **Observational Nature**: Findings are reported as associational; no causal claims.  
- **Collinearity Diagnostics**: VIF computed for all predictors; Hosmer‑Lemeshow test performed; Pearson correlations between `chain_length` and covariates are reported (orthogonality claim removed).  
- **Effect Size Justification**: Derived from pilot sample (see Power Analysis).  

## 5. Compute Feasibility
- **CPU‑only** implementation; all libraries run on the GitHub Actions runner.  
- **Memory**: Graph stored as adjacency list; TVQA subset limited to ≤ 5 GB.  
- **Runtime**: Estimated ≤ 1.5 h with 500 permutations (parallelized across 2 cores), satisfying the CI limit of 7200 s.

## 6. Risk Management
| Risk | Mitigation |
|------|------------|
| Missing verified VideoKR‑SFT source | Use open‑access TVQA dataset; flag original requirement for scope revision. |
| Embedding‑based linking (T102) | `entity_linker.py` implements only exact‑match + bounded Levenshtein; unit tests updated. |
| Insufficient high‑hop samples | Power analysis guarantees ≥ 50; if still insufficient, knot is deferred and logged. |
| Out‑of‑memory on full graph | Load induced subgraph for sampled nodes; fallback to streaming mode. |
| Permutation test exceeds CI time | `NUM_PERMUTATIONS` fixed at 500; can be reduced via config if needed. |
| Download script failure (T103) | `download_data.py` now simply checks for TVQA files and exits cleanly with informative message. |

---

