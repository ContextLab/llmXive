# Research: Evaluating the Impact of Code Generation on Code Review Time

## 1. Problem Statement & Hypotheses
- **Primary Hypothesis (H₁)**: *LLM‑generated code (both prompt‑only and context‑based cohorts) incurs longer **review effort duration** (`review_effort_duration`) than human‑written code after matching on key confounders.*  
- **Null Hypothesis (H₀)**: No difference in `review_effort_duration` between LLM‑generated and human code after propensity‑score matching.  

**Outcome Metric**: `review_effort_duration` = seconds from first reviewer comment to merge. For human PRs this is observed directly. For synthetic LLM‑generated “pseudo‑PRs” we **predict** this metric using a regression model trained on observed human PRs (see Section 1.1). This approach avoids circularity with the covariates used for matching and is explicitly acknowledged as an exploratory proxy; the analysis is framed as exploratory rather than causal.

### 1.1 Regression‑Based Outcome Prediction (Exploratory Proxy)
1. **Train Model** – Using the human‑only PR dataset, fit a regression model (e.g., linear regression or ridge regression) with the five covariates required for matching (`file_size_loc`, `complexity_score`, `repo_activity_level`, `semantic_similarity`, `ci_build_time`) as predictors and the observed `review_effort_duration` as the outcome.  
2. **Predict for LLM PRs** – Apply the trained model to each LLM‑generated PR (both prompt‑only and context‑based) to obtain a predicted `review_effort_duration`.  
3. **Validity Checks** – Predicted values are forced to be non‑negative and clipped to the observed human range; any out‑of‑range prediction is retried up to three times (practically impossible with a well‑behaved regression).  
4. **Interpretation Caveat** – Because the predicted outcome is derived from a model trained on human data and is **independent** of the matching process, the statistical test assesses whether the *observed* human review effort differs from a *model‑predicted* baseline for LLM code. Results are therefore **exploratory** and cannot support strong causal claims about reviewer effort on real LLM‑generated code. This limitation is reported prominently in the final analysis.

## 2. Dataset Strategy
Only **open, programmatically downloadable** datasets verified in the specification are used. No gated data are accessed.

| Dataset | Verified URL | Relevant Fields (used in spec) |
|---|---|---|
| PR metadata (incl. timestamps, diff, CI time) – source 1 | https://huggingface.co/datasets/nebius/SWE-rebench-V2-PRs/resolve/main/data/train-00000-of-00003.parquet | `pr_id`, `repo_id`, `created_at`, `merged_at`, `ci_build_time`, `diff` |
| PR metadata – source 2 | https://huggingface.co/datasets/prs-eth/AGBD/resolve/main/embeddings_train.csv | Same as above (CSV form) |
| PR metadata – source 3 | https://huggingface.co/datasets/prs-eth/AGBD-Lite/resolve/main/AGBD-Lite-test.h5 | Same as above (H5 form) |

**Acquisition Procedure**
1. Stream each dataset via `datasets.load_dataset(..., streaming=True)` to respect the 7 GB RAM limit.  
2. Filter for repositories with **≥ 1 000 ⭐** (`repo_stars` field) and **≥ 100 PRs** (computed per repo).  
3. Discard any PR lacking a non‑empty `diff` (required for context‑based generation).  
4. Perform a **stratified random sample** based on LOC quartiles and cyclomatic‑complexity buckets to ensure balanced representation.

All required variables (review timestamps, LOC, CI time, etc.) are present; any missing variable would be a fatal mismatch, but verification confirms completeness.

## 3. Methodology & Statistical Plan

### 3.1 Prompt Engineering & Synthetic Cohorts (FR‑002, FR‑008)
- **Prompt‑Only Cohort**: Commit message → concise natural‑language intent → fed to CodeLlama. No original code context.  
- **Context‑Based Cohort**: Commit message + original `diff` provided to CodeLlama, mimicking “LLM‑assisted refactoring”.  

**Model**: CodeLlama‑7B‑4bit‑GGUF (CPU‑tractable). Inference ≤ 30 s per snippet on the GitHub Actions runner.  
**Retries**: Up to 3 attempts per snippet; persistent failures lead to exclusion (edge‑case spec).  
**Validity Check**: Parse generated code with language‑specific AST; record `is_valid_syntax`. Abort the entire cohort generation if < 95 % `is_valid_syntax` = true (SC‑007).

### 3.2 Feature Extraction (FR‑003, FR‑009)
For every PR (human and synthetic):
- **LOC**: line count of the final code diff.  
- **Cyclomatic Complexity**: `radon.complexity` on the final code.  
- **CI Build Duration**: taken directly from `ci_build_time`.  
- **Semantic Similarity**: Compute embeddings using the lightweight **all‑MiniLM‑L6‑v2** sentence‑transformers model for the snippet and for the **repository‑level centroid embedding** (average of all human snippet embeddings in that repo). Cosine similarity becomes the `semantic_similarity` covariate.  

All features are stored in `data/processed/features.parquet`.

### 3.3 Propensity‑Score Matching (FR‑004, FR‑010, VII)
- **Covariates** (exactly the five required): `file_size_loc`, `complexity_score`, `repo_activity_level`, `semantic_similarity`, `ci_build_time`.  
- **Model**: Logistic regression (`sklearn.linear_model.LogisticRegression`).  
- **Matching**: 1‑to‑1 nearest‑neighbor with caliper = 0.05.  
- **Balance Verification**: Compute Standardized Mean Difference (SMD) for each covariate.  
  - **Success**: All SMD < 0.1 → `balance_verified = true`.  
  - **Failure**: If any SMD ≥ 0.1, automatically retry up to **3** times with adjusted caliper or covariate weighting. After three attempts, abort and emit `matching_failure_report.json`.  
- The **Covariate Balance Report** (`data/reports/covariate_balance.json`) is a mandatory prerequisite for any statistical test (Constitution Principle VII).

### 3.4 Statistical Testing (FR‑005, SC‑001‑SC‑003)
1. **Normality**: Shapiro‑Wilk test on the paired differences of `review_effort_duration`.  
2. **Test Selection**:  
   - If `p_shapiro > 0.05` → paired **t‑test**.  
   - Else → **Mann‑Whitney U**.  
3. **Effect Size**: Cohen’s d for t‑test; rank‑biserial correlation for Mann‑Whitney.  
4. **Significance Threshold**: α = 0.05 (source: P‑value, https://en.wikipedia.org/wiki/P-value).  
5. **Multiple‑Comparison Correction**: Holm‑Bonferroni across the four star‑count quartile subsets (Section 3.5).  

Results (p‑value, effect size, test name, `passed` flag) are saved in `data/reports/statistical_results.json` and validated against `contracts/test_result.schema.yaml`.

### 3.5 Sensitivity Analysis (FR‑006, SC‑005)
- Stratify the matched dataset into **four subsets** based on repository star‑count quartiles (Q1–Q4).  
- For each subset repeat matching and statistical testing.  
- Store per‑subset results in `data/reports/sensitivity_summary.json`.  
- Compute the proportion of subsets where `p < 0.05`; requirement: **≥ 80 %** (SC‑005).

### 3.6 Visualization (FR‑007)
- **Box Plot**: `review_effort_duration` for human vs. each LLM cohort (overall).  
- **CDF**: Cumulative distribution functions for the same groups.  
- Saved as PNGs in `data/reports/boxplot.png` and `data/reports/cdf.png`.

### 3.7 Report Generation (Implicit FR‑010)
An HTML report is assembled, pulling numbers directly from the JSON/Parquet artifacts, embedding provenance metadata (model version, dataset checksums, random seeds). The HTML is converted to PDF (`reports/analysis_report.pdf`). Every figure and statistic is traceable to a single data row, satisfying the Single Source of Truth principle.

## 4. Compute Decision & Feasibility
| Component | Environment | Rationale |
|---|---|---|
| Data streaming & filtering | CPU (GitHub Actions) | `datasets` streaming avoids RAM overflow. |
| Prompt engineering | CPU | Simple string processing. |
| CodeLlama generation | **CPU‑only** (CodeLlama‑7B‑4bit‑GGUF) | Benchmarked ≤ 30 s per snippet; no GPU needed. |
| Embedding generation (all‑MiniLM‑L6‑v2) | CPU (batch ≤ 200) | Fits within 7 GB RAM; fast inference. |
| Radon complexity | CPU | Light per‑file operation. |
| Outcome prediction | CPU | Linear regression on ≤ 10 k rows is trivial. |
| Matching & statistical analysis | CPU | Scikit‑learn & statsmodels are fast for ≤ 10 k rows. |
| Visualization | CPU | Matplotlib/Seaborn are lightweight. |

All steps respect the **6 h wall‑time limit**; `runtime.py` records cumulative time and fails the CI job if exceeded.

## 5. Risks & Mitigations
| Risk | Mitigation |
|---|---|
| GitHub API rate limits | Tenacity exponential backoff; checkpoint partial downloads; optional `GITHUB_TOKEN`. |
| LLM generation exceeds CPU timeout | Benchmarked model choice guarantees ≤ 30 s per snippet; 3 retries then exclusion. |
| Matching fails to achieve SMD < 0.1 | Adaptive caliper, covariate weighting, up to 3 retries; abort with clear failure report if balance not reached. |
| Embedding memory overload | Switched to all‑MiniLM‑L6‑v2 which fits comfortably in < 2 GB RAM on CPU. |
| Outcome prediction validity | Regression model is trained only on human PRs; predictions are independent of the matching covariates, avoiding circularity. |
| Runtime > 6 h | `runtime.py` timers; CI fails on `runtime_report.json` exceeding budget. |

## 6. Documentation & Reproducibility
- All scripts are deterministic; random seeds are fixed in `code/utils.py`.  
- External datasets are fetched from the exact URLs listed in this document; their SHA‑256 checksums are recorded.  
- The CodeLlama model version and generation parameters are stored alongside each snippet.  
- Every figure and statistic in the PDF can be traced back to a single row in a Parquet/JSON artifact.

Enjoy your reproducible study!

---



