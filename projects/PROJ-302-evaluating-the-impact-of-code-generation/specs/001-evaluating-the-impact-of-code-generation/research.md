# Research: Evaluating the Impact of Code Generation on Code Review Time

## 1. Problem Statement & Hypotheses
- **Primary Hypothesis**: LLM‑generated code (both prompt‑only and context‑based cohorts) is **associated** with longer **review latency** than human‑written code after matching on pre‑treatment confounders.  
- **Null Hypothesis (H₀)**: No association between code origin (LLM vs. human) and review latency after propensity‑score matching.  

**Outcome Metric**: `review_latency = merge_timestamp – created_timestamp` (seconds). This captures the full time from PR opening to merge, a more complete proxy for reviewer effort than the first‑comment timestamp.

## 2. Dataset Strategy
The study uses only **verified open datasets** (see “Verified datasets” block in the spec). No gated or synthetic external sources are required.

| Dataset | Verified URL | What it provides |
|---|---|---|
| PR metadata (including `diff`) | https://huggingface.co/datasets/loubnabnl/prs-v2-sample/resolve/main/data/train-00000-of-00001-a3494cf8c0712e34.parquet | Pull‑request IDs, timestamps, file diffs, repo metadata |
| Additional PR samples (author‑merged) | https://huggingface.co/datasets/davanstrien/authors_merged_model_prs/resolve/main/data/train-00000-of-00001-d32a63c5798549f1.parquet | Enriches author‑level information |
| PR samples (full merged dataset) | https://huggingface.co/datasets/davanstrien/authors_merged_dataset_prs/resolve/main/data/train-00000-of-00001-d5c709e857d2ca0b.parquet | Larger pool for stratified sampling |
| LOC reference (unused for acquisition) | https://huggingface.co/datasets/LocalLLaMA/typed-decisions/resolve/main/agent_trace_observability/test-00000-of-00001.parquet | Demonstrates that LOC data can be streamed if needed |
| CDF visualisation reference (example) | https://huggingface.co/datasets/autoevaluate/autoeval-staging-eval-project-318525f4-cdf7-4888-965c-d4d9dfeeca48-5250/resolve/main/predictions.parquet | Provides a template for CDF plotting |

**Acquisition Procedure**
1. Stream each parquet file via `datasets.load_dataset(..., streaming=True)` to stay within RAM limits.  
2. Filter for repositories with **≥ 1 000 stars** and **≥ 100 PRs** (derived from the metadata).  
3. Retain only PRs that contain a non‑empty `diff` field (required for context‑based generation).  
4. Perform a **stratified random sample** based on **code complexity** (low/medium/high) and **PR size** (LOC quartiles) to obtain a balanced baseline cohort.

## 3. Methodology & Statistical Plan

### 3.1 Prompt Engineering & Synthetic Cohorts (FR‑002, FR‑008)
- **Prompt‑Only Cohort**: Commit message → intent extraction (simple rule‑based classifier) → natural‑language prompt fed to CodeLlama. No original code is supplied.  
- **Context‑Based Cohort**: Commit message + original `diff` supplied to CodeLlama to simulate “LLM‑assisted refactoring”.  

**Model**: CodeLlama‑7B‑quantized (CPU‑tractable).  
- **CPU‑first** inference; if a single generation exceeds **30 seconds**, the pipeline automatically switches to the Kaggle GPU escape hatch (8‑bit quantized, same model).  
- **Retries**: Up to 3 attempts per snippet; on persistent failure the snippet is dropped and logged.  

**Validity Check**: Parse generated code with Python’s `ast` (or language‑appropriate parser). Record `is_valid_syntax`. Target ≥ 95 % valid snippets (SC‑007).

### 3.2 Feature Extraction (FR‑003, FR‑009)
For every PR (human and synthetic):
- **LOC** via simple line count.  
- **Cyclomatic Complexity** via `radon`.  
- **Semantic Similarity** (optional) using CodeBERT embeddings; cosine similarity to the original human snippet. This metric is **exploratory only** and **not used for matching** (Methodological Override).  

All features stored in `data/processed/features.parquet`.

### 3.3 Pre‑Study Power Analysis (New Task)
Before matching, compute the minimum number of matched pairs needed to detect a medium effect size (Cohen’s d ≈ 0.3) with α = 0.05 and power = 0.8. If the sampled dataset yields fewer pairs, additional repositories are fetched. This ensures the study is adequately powered (addressing methodology‑21acc90a).

### 3.4 Propensity‑Score Matching (FR‑004, FR‑010)
- **Covariates** (pre‑treatment only): `repo_activity_level`, `primary_language`, `commit_message_length`.  
- **Model**: Logistic regression (`sklearn.linear_model.LogisticRegression`).  
- **Matching**: 1‑to‑1 nearest‑neighbor with caliper = 0.05.  
- **Balance Check**: Compute Standardized Mean Difference (SMD) for each covariate.  
  - **Success**: All SMD < 0.1 → `balance_verified = true`.  
  - **Failure**: If any SMD ≥ 0.1, retry up to **3** times with adjusted caliper or covariate weighting. After 3 attempts, abort and emit `matching_failure_report.json`.  

### 3.5 Statistical Testing (FR‑005)
1. **Normality**: Shapiro‑Wilk test on the paired differences of review latency.  
2. **Test Selection**:  
   - If `p_shapiro > 0.05` → paired **t‑test**.  
   - Else → **Mann‑Whitney U**.  
3. **Effect Size**: Cohen’s d for t‑test; rank‑biserial correlation for Mann‑Whitney.  
4. **Significance Threshold**: `α = 0.05` (source: P‑value, https://en.wikipedia.org/wiki/P-value).  
5. **Power Reporting**: Report achieved power; if power < 0.8, note “under‑powered” but still present results.  
6. **Multiple‑Comparison Correction**: Apply Holm‑Bonferroni across the five sensitivity subsets (Section 3.6).  

All results written to `data/reports/statistical_results.json`.

### 3.6 Sensitivity Analysis (FR‑006, SC‑005)
Repeat the full matching + testing pipeline across **five** stratified subsets:
1. **Complexity Low** (bottom [deferred] of complexity).
2. **Complexity Medium** (40‑[deferred] percentile).
3. **Complexity High** (top [deferred]).
4. **PR Size Small** (LOC < 25 th percentile).  
5. **PR Size Large** (LOC > 75 th percentile).  

Report the proportion of subsets where `p < 0.05`. Requirement: ≥ 80 % (SC‑005). Store per‑subset results in `sensitivity_summary.json`.

### 3.7 Visualization (FR‑007)
- **Box Plot**: Review latency for human vs. each LLM cohort (overall).  
- **CDF**: Cumulative distribution of review latency for the same groups.  
- Saved as PNG files in `data/reports/`.

### 3.8 Report Generation (Implicit FR‑010)
Combine tables, balance report, statistical summary, and figures into an HTML and PDF report (`analysis_report.pdf`). The report includes provenance metadata (model version, seed commit IDs, dataset checksums).

## 4. Compute Decision & Feasibility
| Component | Execution Environment | Rationale |
|---|---|---|
| Data download & streaming | CPU (GitHub Actions) | `datasets` streaming avoids RAM blow‑up. |
| Feature extraction (radon, LOC) | CPU | Lightweight per‑file operations. |
| Embedding generation (CodeBERT) | CPU (batch ≤ 200) | Fits within 7 GB RAM; optional. |
| CodeLlama generation | **CPU‑first**; GPU escape if > 30 s | Guarantees completion within the 6 h budget; GPU fallback uses Kaggle free GPU (≤ 9 h wall‑time). |
| Matching & stats | CPU | Scikit‑learn & statsmodels are CPU‑native and fast for ≤ 10 k rows. |
| Visualization | CPU | Matplotlib/Seaborn are lightweight. |

## 5. Risks & Mitigations
| Risk | Mitigation |
|---|---|
| GitHub API / dataset streaming stalls | Tenacity exponential backoff; configurable max retries; checkpointing of downloaded shards. |
| LLM generation exceeds CPU timeout | GPU escape hatch; log “GPU‑Offloaded” flag. |
| Matching fails to achieve balance | Adaptive caliper, covariate weighting, and up‑to‑3 retry policy; abort with clear failure report if still unbalanced. |
| Under‑powered sample | Pre‑study power analysis; if still insufficient, collect more data. |
| Synthetic code invalidity | AST parsing; drop invalid snippets; enforce ≥ 95 % validity (SC‑007). |
| Runtime exceeds 6 h | `utils.timer` records each stage; `runtime_report.json` triggers CI failure if limit breached. |

---


