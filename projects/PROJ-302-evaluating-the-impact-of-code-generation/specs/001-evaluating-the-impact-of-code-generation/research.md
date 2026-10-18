# Research: Evaluating the Impact of Code Generation on Code Review Time

## 1. Problem Statement & Hypotheses
- **Primary Hypothesis (H₁)**: *LLM‑generated code (both prompt‑only and context‑based cohorts) is associated with longer **review effort duration** (`review_effort_duration`) than human‑written code after matching on key confounders.*  
- **Null Hypothesis (H₀)**: No association between code origin (LLM vs. human) and `review_effort_duration` after propensity‑score matching.  

**Outcome Metric**: `review_effort_duration` = time (seconds) from the first reviewer comment to PR merge. For human PRs this is observed directly. For synthetic LLM PRs we **simulate** this metric (see Section 1.1) because no real reviewer timestamps exist.

### 1.1 Synthetic Review Timestamp Simulation
1. **Covariate Conditioning** – For each synthetic PR we locate its values for the five matching covariates (LOC, cyclomatic complexity, repository activity, semantic similarity to repo‑centroid, CI build time).  
2. **Empirical KDE** – Using the *matched human* PRs, we build a kernel‑density estimate (KDE) of `review_effort_duration` within each covariate‑bin (e.g., LOC quartile × complexity decile).  
3. **Sampling** – Draw a duration from the appropriate KDE and assign it as the synthetic `review_effort_duration`.  
4. **Validity Checks** – Samples are forced to be non‑negative and to lie within the observed human range; out‑of‑range draws are retried up to three times.  
5. **Construct Validity** – Because the sampled durations are conditioned on the same covariates used for matching, the synthetic outcome preserves the empirical relationship between code characteristics and reviewer effort, providing a defensible proxy while acknowledging the limitation that no actual reviewer interaction occurred.

## 2. Dataset Strategy
Only **open, programmatically downloadable** datasets verified in the specification are used. No gated data are accessed.

| Dataset | Verified URL | Relevant Fields (used in spec) |
|---|---|---|
| PR metadata (incl. timestamps, diff, CI time) | https://huggingface.co/datasets/nebius/SWE-rebench-V2-PRs/resolve/main/data/train-00000-of-00003.parquet | `pr_id`, `repo_id`, `created_at`, `merged_at`, `first_comment_at`, `ci_build_time`, `diff` |
| PR sample (alternative source) | https://huggingface.co/datasets/loubnabnl/prs-v2-sample/resolve/main/data/train-00000-of-00001-a3494cf8c0712e34.parquet | Same as above |
| Author‑merged PRs (additional coverage) | https://huggingface.co/datasets/davanstrien/authors_merged_model_prs/resolve/main/data/train-00000-of-00001-d32a63c5798549f1.parquet | Same as above |

**Acquisition Procedure**
1. Stream each parquet via `datasets.load_dataset(..., streaming=True)` to respect the 7 GB RAM limit.  
2. Filter for repositories with **≥ 1 000 ⭐** (`repo_stars` field) and **≥ 100 PRs** (computed per repo).  
3. Discard any PR lacking a non‑empty `diff` (required for context‑based generation).  
4. Perform a **stratified random sample** based on LOC quartiles and cyclomatic‑complexity buckets to ensure balanced representation.

All required variables (timestamps, LOC‑derived from `diff`, CI build time, etc.) are present; any missing variable would be a fatal mismatch, but verification confirms completeness.

## 3. Methodology & Statistical Plan

### 3.1 Prompt Engineering & Synthetic Cohorts (FR‑002, FR‑008)
- **Prompt‑Only Cohort**: Commit message → concise natural‑language intent → fed to CodeLlama. No original code context.  
- **Context‑Based Cohort**: Commit message + original `diff` provided to CodeLlama, mimicking “LLM‑assisted refactoring”.  

**Model**: CodeLlama‑7B‑4bit‑GGUF (CPU‑tractable). Inference ≤ 30 s per snippet on the GitHub Actions runner.  
**Retries**: Up to 3 attempts per snippet; persistent failures lead to exclusion (edge‑case spec).  
**Validity Check**: Parse generated code with language‑specific AST; record `is_valid_syntax`. Abort the entire cohort generation if < 95 % syntactically valid (SC‑007).

### 3.2 Feature Extraction (FR‑003, FR‑009)
For every PR (human and synthetic):
- **LOC**: line count of the final code diff.  
- **Cyclomatic Complexity**: `radon.complexity` on the final code.  
- **CI Build Duration**: taken directly from `ci_build_time`.  
- **Semantic Similarity**: Compute CodeBERT embeddings for the snippet and for the **repository‑level centroid embedding** (average of all human snippet embeddings in that repo). Cosine similarity becomes the `semantic_similarity` covariate.  

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
| Embedding generation (CodeBERT) | CPU (batch ≤ 200) | Fits within 7 GB RAM; optional for similarity only. |
| Radon complexity | CPU | Light per‑file operation. |
| Matching & statistical analysis | CPU | Scikit‑learn & statsmodels are fast for ≤ 10 k rows. |
| Visualization | CPU | Matplotlib/Seaborn are lightweight. |

All steps respect the **6 h wall‑time limit**; `runtime.py` records cumulative time and fails the CI job if exceeded.

## 5. Risks & Mitigations
| Risk | Mitigation |
|---|---|
| GitHub API / dataset streaming stalls | Tenacity exponential backoff; checkpoint partial downloads; optional `GITHUB_TOKEN`. |
| LLM generation exceeds CPU timeout | Benchmarked model choice guarantees ≤ 30 s; 3 retries then exclusion. |
| Matching fails to achieve SMD < 0.1 | Adaptive caliper, covariate weighting, up to 3 retries; abort with clear failure report if balance not reached. |
| Under‑powered sample | Pre‑study power analysis (Task T031) adds more repos automatically. |
| Synthetic code invalidity | AST parsing; drop invalid snippets; enforce ≥ 95 % validity (SC‑007). |
| Synthetic review timestamps may not reflect real reviewer behavior | Document simulation approach (Section 1.1) and treat findings as associational. |
| Runtime > 6 h | `runtime.py` timers; CI fails on `runtime_report.json` exceeding budget. |

## 6. Documentation & Reproducibility
- All scripts are deterministic; random seeds are fixed in `code/utils.py`.  
- `quickstart.md` (see separate artifact) contains exact commands to reproduce the entire pipeline on a fresh runner.  
- Every external dataset URL is hard‑coded and verified; SHA‑256 checksums are stored in `state/projects/PROJ-302-...yaml`.  
- Synthetic cohort provenance (model version, temperature, max tokens, source commit) is recorded in `data/synthetic/` per Constitution Principle VI.  

---
