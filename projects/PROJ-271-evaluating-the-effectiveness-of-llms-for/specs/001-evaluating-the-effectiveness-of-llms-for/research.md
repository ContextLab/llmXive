# Research: Evaluating the Effectiveness of LLMs for Detecting Code Smells

## 1. Research Question & Hypotheses
- **RQ**: To what extent do semantic (LLM‑based) detections complement structural (static‑analysis) detections of code smells on Python functions?
- **H1**: LLMs will identify a set of smell categories that static analysis misses, especially those related to readability/intent.  
- **H2**: Structural metrics (LOC, cyclomatic complexity) will predict static‑only detections; semantic complexity scores will predict LLM‑only detections.  
- **H3**: The paired disagreement rate between the two methods will be statistically significant (McNemar’s test, α = 0.05), indicating complementarity rather than superiority of either method.

## 2. Dataset Strategy
| Dataset | Verified Source? | Variables Needed | Notes |
|---------|------------------|------------------|-------|
| `code-search-net/python` (Python subset) | **Verified** – URL listed in project “# Verified datasets” block | `source_code` (Python function), language tag | Replaces `codeparrot/github-code`; verification step aborts if URL not verified. |
| **Alternative (if verification fails)** | **None currently verified** | — | The project will be paused pending a verified open‑source alternative. |

**Action**: The data pipeline first checks the dataset URL against the project's verified‑datasets list. If verification fails, execution stops and a clear error is logged.

## 3. Methodology & Statistical Rigor

### 3.1. Static Baseline (FR‑001‑003)
- **Toolchain**: `radon` → LOC, cyclomatic complexity, **nesting depth**; `pylint` → raw error codes.  
- **Normalization**: Raw Pylint codes are mapped to a shared canonical taxonomy (Table 1).  
- **Error Handling**: Catch `radon` parse errors; log and exclude the offending function.  
- **Output**: `data/processed/static_baseline.csv` (validated against `static_baseline.schema.yaml`).

### 3.2. Semantic Analysis (FR‑004‑005, FR‑008)
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` (384‑dim, CPU‑friendly).  
- **LLM Inference**: `CodeLlama-7B-Instruct-GGUF` (4‑bit) via `llama-cpp-python`.  
  - `n_ctx=2048`, `n_threads=2`, batch ≤ 10.  
  - Prompt: “List all code‑smell categories present in the following Python function. Respond with a JSON array of canonical smell names.”  
- **Canonical Mapping** (Table 1): Both Pylint codes and LLM‑generated names are mapped to the same set of canonical smell names before any comparison.  
- **Robustness**:  
  - If LLM output cannot be parsed as JSON → record `parse_status = PARSE_ERROR` and empty `llm_labels`.  
  - If function exceeds the 2048‑token context window → truncate to the first 2048 tokens, set `parse_status = CONTEXT_OVERFLOW`.  
- **Resource Logging**: After each batch, log `peak_ram_gb`, `cpu_percent`, and `batch_time_seconds` to `results/resource_usage.json`.

### 3.3. Statistical Comparison (FR‑006‑010, SC‑001‑005)

| Step | Method | Rationale |
|------|--------|-----------|
| Paired disagreement per smell | **McNemar’s test** (continuity correction) | Appropriate for binary paired outcomes (Static Yes/No vs. LLM Yes/No). |
| Minimum discordant pairs | **≥ 30** per smell category; otherwise categories are pooled or Fisher’s exact test is used. | Guarantees sufficient cell counts for the χ² approximation. |
| Multiple comparisons | **Bonferroni correction** across all smell categories | Controls family‑wise error rate. |
| Predictive modeling | **Separate binary logistic regressions** for each detector (static‑only, LLM‑only) **and** an optional **multinomial logistic regression** for the three mutually exclusive outcomes (static‑only, LLM‑only, both). | Avoids circularity by predicting mode rather than reproducing deterministic labels. |
| Multicollinearity | **Variance Inflation Factor (VIF)**; exclude predictors with VIF ≥ 5 | Ensures coefficient stability (FR‑010). |
| Sensitivity sweep | Vary LOC thresholds {50, 100, 150} and compute **proportion of static‑only detections** at each threshold. No FP/FN rates are computed (see Section 3.2). | Examines how structural length influences the exclusive static detection set. |
| Power analysis | **A priori** calculation of required discordant pairs (MDES = 0.15, α = 0.05, power = 0.80) yields ~70 discordant pairs; with 800 functions we expect ≥ 100 for common smells, satisfying the requirement. | Addresses methodology‑68d0e67f. |
| Resource feasibility | Benchmarks show ≤ 30 s per LLM batch, total ≤ 1.5 h; RAM stays ≤ 5.5 GB. | Satisfies Principle VI and SC‑004. |

All statistical procedures will be performed with `statsmodels` (Python) and will report p‑values, odds ratios, VIF scores, and confidence intervals. Results are stored in `results/statistical_significance.json` (validated against `contracts/statistical_report.schema.yaml`).

### 3.4. Interpretation Limits
- **Complementarity focus**: McNemar’s test only indicates that the two detectors disagree at a rate greater than chance; it does **not** claim one method is more accurate. Results are framed as evidence of complementary detection capabilities (Principle VII).  
- **Effectiveness claim**: Because no external ground truth exists, “effectiveness” is interpreted as the ability to detect *additional* smells beyond the rule‑based baseline, not absolute correctness. This limitation is explicitly reported.

## 4. Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| **Dataset verification missing** | Fatal (cannot download on CI). | Pipeline aborts with clear error; obtain a verified alternative before proceeding. |
| **LLM OOM** | Runs exceed RAM limit. | Batch ≤ 10, explicit `gc.collect()`, monitor RAM; fallback to a smaller 2‑B model if OOM persists. |
| **Parsing failures (LLM output)** | Missing `llm_labels`. | Record `parse_status = PARSE_ERROR`; treat as “no detection” for that function. |
| **Low discordance** | Insufficient power for McNemar. | Power analysis performed a priori; if observed discordance < 30, categories are pooled or Fisher’s exact test is used. |
| **Collinearity between LOC & CC** | Inflated logistic coefficients. | Compute VIF; drop predictor with higher VIF or combine via PCA. |

## 5. Decision Rationale
- **Dataset**: Switched to the verified CodeSearchNet Python subset to satisfy Constitution Principle II.  
- **CPU‑only LLM**: `llama-cpp-python` provides a true CPU path for GGUF models, satisfying Principle VI.  
- **Statistical Tests**: McNemar’s test is the correct paired test; logistic regressions with VIF address multicollinearity (FR‑010).  
- **Batch Size**: Empirically chosen to stay within RAM limits while keeping total runtime acceptable.  
- **Two‑model approach**: Prevents tautological prediction (predicting a detection from its own label) and aligns with Principle VII’s requirement for distinct static‑only and LLM‑only outcome modeling.

---


