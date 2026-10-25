# Research: Video Reasoning Threshold Analysis

## 1. Problem Definition
We investigate whether increasing structural complexity—measured as the shortest‑path hop count between entities in the **ground‑truth knowledge graph**—is **associatively** linked to a non‑linear “reasoning cliff” in video‑question‑answering (Video‑QA) accuracy. The hypothesis is that, **observationally**, accuracy drops sharply beyond a certain hop count, but we do **not** claim a causal effect because no experimental manipulation of reasoning depth is performed.

## 2. Dataset Strategy

| Role | Dataset | Access Method | Variables Provided | Comments |
|------|---------|---------------|--------------------|----------|
| Primary QA data | **VideoKR‑SFT** (open‑access) | `code/ingest/download_videokr.py` (programmatic download from the official release URL) | `question_text`, `answer_text`, `correct_answer_idx` (binary correctness), `video_id`, `question_id`, `difficulty_score`, `answer_format` | If the official release URL is unreachable, the pipeline aborts (no TVQA substitute). |
| Knowledge Graph | **Ground‑truth KG** bundled with VideoKR‑SFT | `code/ingest/download_kg.py` (download from the official KG archive) | Nodes & edges for hop‑count computation | No fallback to ConceptNet; abort if unavailable. |
| Video metadata | `metadata/video_lengths.csv` (included in VideoKR‑SFT release) | Direct file path under `data/raw/videokr_sft/metadata/video_lengths.csv` | `video_id`, `length_seconds` | Used for covariate extraction. |

**Variable Fit Assurance**  
All variables required by the specification are present:

- `question_text`, `answer_text`, `correctness` (derived from `correct_answer_idx`), `answer_type` (derived as `"multiple_choice"`), `question_id`, `video_id`.
- Covariates: `question_difficulty` (proxy from `difficulty_score`), `video_length_seconds` (from metadata), `answer_type`.
- Structural metric: `chain_length` (computed from the ground‑truth KG).

Correctness labels are taken directly from VideoKR‑SFT; they are observational, not synthesized.

## 3. Methodology

### 3.1 Structural Annotation (FR‑001, FR‑002, FR‑012)
1. **Deterministic Entity Linking** (`entity_linker.py`):  
   - Normalize strings (lower‑case, strip punctuation).  
   - Perform **exact match** to KG node names; if none, apply **Levenshtein distance ≤ 2** as the only fuzzy fallback.  
2. **Linking Validation**: Process a hand‑curated validation set; abort if linking accuracy < 95 % (ensuring Constitution VI).  
3. **Hop Counting** (`networkx` BFS) yields `chain_length`. Unlinkable pairs receive `chain_length = -1` and `status = "mapping_failure"`.  
4. **Covariate Extraction**:  
   - `question_difficulty`: normalized length of the question (0–1).  
   - `video_length_seconds`: from `metadata/video_lengths.csv`.  
   - `answer_type`: `"multiple_choice"` (VideoKR‑SFT format).  
5. **Outputs**: `annotated_videokr.csv` (conforms to `contracts/annotated_questions.schema.yaml`) and `chain_bins.csv` (derived binning).

> **Construct‑Validity Note**: `chain_length` is a **proxy** for reasoning steps required; it captures graph distance but may not fully reflect cognitive load. This limitation is acknowledged, and results are interpreted as associative evidence only.

### 3.2 Power Analysis (FR‑011)
Implemented in `power_analysis.py`. Using effect size *h* = 0.12, α = 0.05 (Bonferroni‑adjusted for five knot tests → α_adj = 0.01), and power = 0.80 yields a minimum per‑bin *n* ≈ 90; we round up to **100** and record this in `power_analysis.json`. Bins below this threshold are merged or flagged.

### 3.3 Accuracy Stratification (FR‑003)
`stratify_accuracy.py` groups by `hop_bin` (`'1'`, `'2'`, `'3+'`), computes mean correctness, and flags any bin with < 100 samples. Generates `accuracy_binned.png` (bar chart) and `accuracy_binned.csv`.

### 3.4 Threshold Detection (FR‑004) – Permutation Test & LRT
`detect_threshold.py` performs:
- **Null Model**: Logistic regression of `correctness` on `chain_length` + covariates.  
- **Alternative Models**: Piecewise logistic with a knot at each *k* ∈ {1,2,3,4,5}.  
- **Likelihood‑Ratio Test** for each knot.  
- **Covariate‑Adjusted Permutation** (10,000 permutations): residuals from covariates are permuted, re‑added, and the maximal Δ log‑likelihood across knots recorded to build a null distribution.  
- **Bonferroni Correction** across five tests (α_adj = 0.01).  
- **Disconnection Rates** per hop bin are also computed.  
Outputs: `threshold_results.json` (per‑knot *p*‑values, selected knot, significance flags, disconnection rates).

### 3.5 Continuous Visualization (FR‑005)
Scatter plot of binary `correctness` vs. `chain_length` with a LOESS smooth line. Outputs: `accuracy_vs_hop_raw.png` and `accuracy_vs_hop_raw.csv`.

### 3.6 Sensitivity & Confound Analysis (FR‑008, SC‑003, SC‑006)
Three explicit binning schemes are evaluated:

| Scheme | Definition |
|--------|------------|
| **S1** | `'1'`, `'2'`, `'3+'` (≥ 3 aggregated) |
| **S2** | `'1'`, `'2'`, `'3'`, `'4+'` (≥ 4 aggregated) |
| **S3** | `'1'`, `'2'`, `'3'`, `'4'`, `'5+'` (≥ 5 aggregated) |

For each scheme the full permutation‑LRT pipeline runs **with covariates included**. Robustness is achieved if a significant cliff (Bonferroni‑corrected *p* < 0.01) appears in **≥ 2 of 3** schemes (SC‑003). A bias flag is set if `disconnection_rates` correlate with hop count. Results stored in `sensitivity_analysis.json` and summarized in `threshold_results.json` (`robustness_status`, `bias_flag`).

### 3.7 Predictive Model & LRT (FR‑010, SC‑006)
1. **Baseline**: TF‑IDF of `question_text` + `answer_text`, logistic regression (`solver='lbfgs'`).  
2. **Extended**: Same features plus `chain_length`.  
3. **Regularization**: L2 penalty tuned via 5‑fold CV.  
4. **LRT**: Compare baseline vs. extended; store statistic, *p*‑value, `is_significant`, and a textual `conclusion` in `model_lrt_results.json`.  
5. **Confound‑Adjusted LRT**: Repeat including the three covariates; write to `confound_adjusted_lrt.json`.  
6. **Prediction Injection**: Model probabilities written to `predicted_correctness` column of `annotated_videokr.csv` (fulfills FR‑013).  

### 3.8 Runtime & Memory Logging (FR‑006, FR‑009)
`main.py` records wall‑clock time → `runtime_log.json` (`total_seconds`, `limit_exceeded`). `memory_tracker.py` records peak RAM → `memory_log.json` (`peak_gb`, `limit_exceeded`).

## 4. Statistical Rigor (SC‑002, SC‑003, SC‑006)
- **Model**: Binomial logistic GLM for binary outcomes.  
- **Multiple Comparisons**: Bonferroni correction across five knot tests (α_adj = 0.01).  
- **Power Assurance**: Minimum 100 samples per bin (≥ 80 % power for *h* = 0.12).  
- **Observational Caveat**: Findings reported as associational; no causal claims.  
- **Collinearity Diagnostics**: VIF for all predictors, Hosmer‑Lemeshow goodness‑of‑fit, Pearson correlations between `chain_length` and covariates.

## 5. Compute Feasibility
- **CPU‑first**: All libraries run on the CI runner.  
- **Memory**: VideoKR‑SFT + trimmed KG < 2 GB.  
- **Runtime**: ≤ 1.5 h (including 10,000 permutations). Meets CI limit of 7200 s.

## 6. Risk Management
| Risk | Mitigation |
|------|------------|
| Required datasets unavailable | Pipeline aborts with clear error; no TVQA/ConceptNet fallback. |
| Embedding‑based linking | `entity_linker.py` limited to exact match + Levenshtein ≤ 2; unit tests enforce. |
| Insufficient high‑hop samples | Power analysis guarantees ≥ 100 per bin; bins still lacking are merged and flagged. |
| Out‑of‑memory on large graph | KG trimmed to entities appearing in VideoKR‑SFT; streaming fallback available. |
| Permutation test exceeds CI time | `NUM_PERMUTATIONS = 10000` is balanced for CI runtime; configurable if needed. |
| Download failure | Robust download scripts abort with clear logs; CI surfaces the failure. |

## 7. Seed Pinning (Constitution I)
All stochastic components use the globally defined seed `SEED = 42` from `utils/config.py`. This ensures exact reproducibility across CI runs.

## 8. Single Source of Truth (Constitution IV)
Each generated artifact (figures, CSVs, JSONs) is the **sole source** for its corresponding statistic; no hand‑typed numbers appear elsewhere in the project.
