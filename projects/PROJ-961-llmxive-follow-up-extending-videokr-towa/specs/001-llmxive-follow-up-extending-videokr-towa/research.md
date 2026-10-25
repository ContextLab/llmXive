# Research: Video Reasoning Threshold Analysis

## 1. Problem Definition
We investigate whether increasing structural complexity—measured as the shortest‑path hop count between entities in a knowledge graph—produces a non‑linear “reasoning cliff” in video‑question‑answering (Video‑QA) accuracy. The hypothesis: beyond a certain hop count, accuracy drops sharply rather than following a smooth logistic decline.

## 2. Dataset Strategy

### Open‑Access TVQA Dataset (Verified & Reproducible)
The proprietary VideoKR‑SFT dataset is not publicly reachable. To answer the research question we use the **TVQA** dataset, which is openly available via the HuggingFace `datasets` library (`datasets.load_dataset("tvqa")`). TVQA provides:

- `question_text`, `answer_text`, `answer_id`, `answer` (multiple‑choice), `correct_answer_idx` (binary correctness), `video_id`.
- Video metadata (duration) is supplied in the accompanying `metadata/video_lengths.csv` file (publicly hosted on the TVQA GitHub repository).
- Difficulty proxy: we compute a **question difficulty score** as the normalized length of the question (longer questions tend be harder) and store it in `question_difficulty` (0–1).

### Public Knowledge Graph: ConceptNet
We download the **ConceptNet** knowledge graph (English subset) from its public URL (`https://conceptnet.io/downloads/2016/english/conceptnet-english-5.7.tar.gz`). ConceptNet is a large, open graph of common‑sense relations between concepts. It serves as the static KG for hop‑count computation.

### Variable Fit Assurance
Both TVQA and ConceptNet together provide **all required variables**:

- `question_text`, `answer_text`, `correctness` (observed from TVQA), `difficulty_score` (computed proxy), `answer_format` (derived as `"multiple_choice"`), `video_id`, plus the KG for hop counting.
- Covariates (`question_difficulty`, `video_length_seconds`, `answer_type`) are extracted as described in FR‑012.

### Observational Correctness Labels
Correctness labels are **observed outcomes** from TVQA (the ground‑truth answer index). They are **not** generated from hop count, avoiding circularity. This ensures the downstream “reasoning cliff” detection tests an empirical association between hop count (derived from ConceptNet) and actual model performance.

## 3. Methodology

### 3.1 Structural Annotation (FR‑001, FR‑002, FR‑012)
1. **Deterministic Entity Linking** (`code/utils/entity_linker.py`):  
   - Normalize strings (lower‑case, strip punctuation).  
   - Perform **exact match** to ConceptNet node names; if none, apply **Levenshtein distance ≤ 2** as the only fuzzy fallback.  
2. **Linking Validation**: A curated validation set of hand‑checked TVQA questions is processed; linking accuracy is logged in `annotation_coverage.json`. The pipeline aborts if accuracy < 95 % (ensuring structural annotation integrity, Constitution VI).  
3. **Hop Counting** (`networkx` BFS) computes the shortest path length (`chain_length`) between the linked question entity and answer entity. Unlinkable pairs receive `chain_length = -1` and `status = "mapping_failure"`.  
4. **Covariate Extraction** (`annotate_graph.py`):  
   - `question_difficulty` ← normalized question length (0–1).  
   - `video_length_seconds` ← from `metadata/video_lengths.csv`.  
   - `answer_type` ← `"multiple_choice"` (TVQA is MCQ).  
5. **Outputs**: `annotated_videokr.csv` (see `contracts/annotated_questions.schema.yaml`) and `chain_bins.csv` (derived binning).

### 3.2 Power Analysis (FR‑011)
Implemented in `code/analysis/power_analysis.py`. Writes `power_analysis.json` with `min_samples_per_bin = 100` (rounded up from analytical result) and uses it to validate bin adequacy (FR‑003).

### 3.3 Accuracy Stratification (FR‑003)
`code/analysis/stratify_accuracy.py` groups by `hop_bin` (`'1'`, `'2'`, `'3+'`), computes mean correctness, and flags any bin with < 100 samples for merging. Generates `accuracy_binned.png` (bar chart) and `accuracy_binned.csv`.

### 3.4 Threshold Detection (FR‑004) – Permutation Test & LRT
`code/analysis/detect_threshold.py` performs:
- **Null Model**: Logistic regression of `correctness` on `chain_length` + covariates.  
- **Alternative Models**: Piecewise logistic with a knot at each *k* ∈ {1,2,3,4,5}.  
- **Likelihood‑Ratio Test** (Δ log‑likelihood) for each knot.  
- **Covariate‑Adjusted Permutation Procedure**:  
  1. Regress `correctness` on the covariates, obtain residuals.  
  2. Permute residuals repeatedly., add them back to the fitted covariate component, and recompute the maximal Δ log‑likelihood across knots.  
  3. Build a null distribution from the permuted maxima.  
- **Bonferroni Correction** across the five tests (α_adj = 0.01).  
- **Significance**: Cliff declared if corrected *p* < 0.01.  
- **Disconnection Rates**: For each hop bin, compute the proportion of records with `status="disconnected"` or `"mapping_failure"` and store in `threshold_results.json`.  
- **Outputs**: `threshold_results.json` (per‑knot *p*‑values, effect sizes, selected knot, `is_significant`, `disconnection_rates`).

### 3.5 Continuous Visualization (FR‑005)
Scatter plot of binary `correctness` vs. `chain_length` with a LOESS smooth line. Outputs: `accuracy_vs_hop_raw.png` and `accuracy_vs_hop_raw.csv`.

### 3.6 Sensitivity & Confound Analysis (FR‑008, SC‑003, SC‑006)
Three **explicitly defined** binning schemes are evaluated:

| Scheme | Definition |
|--------|------------|
| S1 | `hop_bin` values `'1'`, `'2'`, `'3+'` (all hop counts ≥ 3 aggregated) |
| S2 | `hop_bin` values `'1'`, `'2'`, `'3'`, `'4+'` (≥ 4 aggregated) |
| S3 | `hop_bin` values `'1'`, `'2'`, `'3'`, `'4'`, `'5+'` (≥ 5 aggregated) |

For each scheme the full permutation‑LRT pipeline runs with covariates included. Robustness is achieved if a significant cliff (Bonferroni‑corrected *p* < 0.01) appears in **≥ 2 of 3** schemes (SC‑003). A **bias flag** is set if `disconnection_rates` correlate with hop count. Results are stored in `sensitivity_analysis.json` and the consolidated `threshold_results.json` (fields `robustness_status`, `bias_flag`).

### 3.7 Predictive Model & LRT (FR‑010, SC‑006)
1. **Baseline Model**: TF‑IDF of `question_text` + `answer_text`, logistic regression (`solver='lbfgs'`).  
2. **Extended Model**: Same features plus `chain_length` (continuous).  
3. **Regularization**: L2 penalty tuned via 5‑fold CV.  
4. **LRT**: Compare baseline vs. extended; store statistic, *p*‑value, `is_significant`, and a textual `conclusion` in `model_lrt_results.json`.  
5. **Confound‑Adjusted LRT**: Repeat LRT while also including the three covariates; write results to `confound_adjusted_lrt.json` (fulfills SC‑006).  
6. **Prediction Injection**: Model probabilities are written to the `predicted_correctness` column of `annotated_videokr.csv` (fulfilling the schema).

### 3.8 Runtime & Memory Logging (FR‑006, FR‑009)
`code/main.py` records total wall‑clock time → `runtime_log.json` (`total_seconds`, `limit_exceeded`). `code/utils/memory_tracker.py` records peak RAM → `memory_log.json` (`peak_gb`, `limit_exceeded`).

## 4. Statistical Rigor (SC‑002, SC‑003, SC‑006)
- **Model Choice**: Binomial logistic GLM for binary outcomes.  
- **Multiple Comparisons**: Bonferroni correction across the five knot tests; decision rule α_adj = 0.01.  
- **Power Assurance**: Minimum 100 samples per bin (≥ 80 % power for effect size *h* = 0.12).  
- **Observational Caveat**: Findings are reported as **associational**; no causal claims are made.  
- **Collinearity Diagnostics**: VIF for all predictors; Hosmer‑Lemeshow goodness‑of‑fit test; Pearson correlations between `chain_length` and each covariate are reported (no orthogonality assumption).  

## 5. Compute Feasibility
- **CPU‑only**: All libraries (pandas, numpy, scikit‑learn, statsmodels, networkx, datasets) run on the CI runner.  
- **Memory**: TVQA and ConceptNet together stay well below the 7 GB limit.  
- **Runtime**: Estimated ≤ 1.5 h (including 500 permutations). Meets the required CI limit..

## 6. Risk Management
| Risk | Mitigation |
|------|------------|
| No open VideoKR‑SFT source | Use TVQA (open) and ConceptNet (open) as proxies; clearly note external‑validity limitation. |
| Embedding‑based linking (T102) | `entity_linker.py` limited to exact match + Levenshtein ≤ 2; unit tests enforce. |
| Insufficient high‑hop samples | Power analysis guarantees ≥ 100 per bin; if a bin still lacks samples, it is merged and flagged. |
| Out‑of‑memory on large graph | ConceptNet subgraph is trimmed to entities appearing in TVQA; streaming fallback available. |
| Permutation test exceeds CI time | `NUM_PERMUTATIONS` fixed at 500; configurable via `config.py`. |
| Previous download failure (T103) | Download steps use robust `datasets` library for TVQA and a verified URL for ConceptNet; failures abort with clear logs. |
