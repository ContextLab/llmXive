# Research: Evaluating the Impact of Code Generation on Code Review Time

## 1. Problem Statement & Hypotheses
- **Primary Hypothesis (H₁)**: *LLM‑generated code (both prompt‑only and context‑based cohorts) incurs longer **review effort duration** (`review_effort_duration`) than human‑written code after matching on key confounders.*  
- **Null Hypothesis (H₀)**: No difference in `review_effort_duration` between LLM‑generated and human code after propensity‑score matching.  

**Outcome Metric**: `review_effort_duration` = seconds from first reviewer comment to merge. For human PRs this is observed directly from GitHub metadata. For LLM‑generated PRs the metric is **observed** by creating pull requests in a dedicated sandbox evaluation repository, inviting a controlled panel of human reviewers, and recording the actual timestamps (`first_comment_at` → `merge_at`). This yields a real, empirical measure of reviewer effort, avoiding the proxy regression approach previously proposed.

## 2. Dataset Strategy
We obtain **live PR metadata** from the GitHub REST API for a stratified sample of **5 high‑star (≥ 1 000 ⭐) repositories**, each contributing up to **200 pull requests** (≥ 100 PRs per repo). This ensures that every record contains the required timestamps:
- `created_at`
- `first_comment_at` (first reviewer comment)
- `merge_at`

The API also provides `ci_build_time`, file diffs, and commit messages, enabling full feature extraction. Because the data are fetched programmatically, the source is reproducible and open (no gated access). The sampling strategy guarantees sufficient variability for power analysis (see below) while staying within RAM limits (streamed JSON → Parquet).

## 3. Power Analysis (Task T001)
Using the `statsmodels.stats.power.TTestIndPower` routine, we compute the required sample size to detect a **[deferred] increase** in `review_effort_duration` with a **small effect size** (Cohen's d ≥ 0.2) at **α = 0.05** (source: P‑value, https://en.wikipedia.org/wiki/P-value) and **power = 0.8**. The calculation yields **≈ 210 matched pairs**; we target **≥ 250 pairs** to provide a safety margin and satisfy SC‑001. The power analysis is performed in `code/power_analysis.py` before data collection proceeds.

## 4. Synthetic Cohorts & Real‑World Evaluation
### 4.1 Prompt‑Only Cohort
- Commit messages → concise natural‑language intent → fed to CodeLlama‑7B‑4bit‑GGUF.
- No original code context is provided.

### 4.2 Context‑Based Cohort
- Commit messages + original `diff` are supplied to CodeLlama, mimicking “LLM‑assisted refactoring”.

Both cohorts are generated with **CPU‑only** inference (≤ 30 s per snippet, 3 retries) and validated for syntactic correctness (AST parsing). ≥ 95 % validity is required (FR‑011).

### 4.3 Evaluation Repository (Task T010)
A dedicated sandbox repository (`llm-code-review-eval`) is created via the GitHub API. For each generated snippet we:
1. Open a pull request against the sandbox repo.
2. Tag a pre‑registered reviewer panel (e.g., project collaborators).
3. Record the PR URL for later polling.

### 4.4 Timestamp Collection (Task T011)
A monitoring script polls each evaluation PR until either:
- A reviewer comment appears (`first_comment_at`) and the PR is merged (`merge_at`), or
- A substantial interval elapses without review..

Only PRs with both timestamps are retained; those exceeding 48 h are logged and excluded, satisfying FR‑013 and **SC‑008** (≥ 80 % success).

## 5. Feature Extraction (Task T030a)
For **all** PRs (human and LLM):
- **LOC**: line count of the final diff.
- **Cyclomatic Complexity**: via `radon.complexity`.
- **CI Build Duration**: from `ci_build_time`.
- **Semantic Similarity**: embeddings from **all‑MiniLM‑L6‑v2**; cosine similarity to the repository‑level centroid embedding.
- Additional covariates: `repo_activity_level` (number of PRs per repo) and `commit_message_length`.

All features are stored in `data/processed/features.parquet`.

## 6. Propensity‑Score Matching (Task T032)
- Logistic‑regression propensity scores on the five covariates.
- 1‑to‑1 nearest‑neighbor matching with caliper = 0.05.
- **Balance Verification**: compute Standardized Mean Difference (SMD) for each covariate; all must be **< 0.1**. If any exceed, the algorithm retries up to **3** times with adjusted caliper or weighting; failure aborts with `matching_failure_report.json`. The resulting `covariate_balance.json` is a prerequisite for any statistical test (Constitution VII).

## 7. Statistical Testing (Task T036)
1. **Normality Check**: Shapiro‑Wilk test on paired differences of `review_effort_duration`.
2. **Test Selection**:
   - If `p_shapiro > 0.05` → paired **t‑test**.
   - Else → **Mann‑Whitney U**.
3. **Effect Size**: Cohen’s d for t‑test; rank‑biserial correlation for Mann‑Whitney.
4. **Multiple‑Comparison Correction**: Holm‑Bonferroni correction across the four star‑count quartile subsets (Task T037).
5. **Significance Threshold**: α = 0.05 (source: P‑value, https://en.wikipedia.org/wiki/P-value).
6. **Schema Validation**: Output conforms to `contracts/test_result.schema.yaml`.

Results (`p_value`, `effect_size`, `passed`) are saved in `data/reports/statistical_results.json`.

## 8. Sensitivity Analysis (Task T037)
- Stratify matched pairs into **four repository‑star‑count quartiles**.
- Repeat matching and statistical testing per quartile.
- Aggregate results in `data/reports/sensitivity_summary.json`; require **≥ 80 %** of quartiles to show `p < 0.05` (SC‑005).

## 9. Visualization (Task T038)
- **Box Plot**: `review_effort_duration` for human vs. each LLM cohort.
- **CDF**: Cumulative distribution of the same metric.
- Saved as PNGs in `data/reports/boxplot.png` and `data/reports/cdf.png`.

## 10. Report Generation (Task T039)
An HTML report is assembled, pulling numbers directly from JSON/Parquet artifacts, embedding provenance metadata (model version, dataset checksums, random seeds). The HTML is converted to PDF (`reports/analysis_report.pdf`). Every figure and statistic traces back to a single data row, satisfying the Single Source of Truth principle.

## 11. Runtime Measurement (Task T040)
`runtime.py` records stage timings, writes `runtime_report.json`, and fails the CI job if total wall‑time exceeds **6 hours**.

## 12. Reproducibility Guarantees
- All random seeds are pinned (`utils.set_seed(42)`).
- External data are fetched from the GitHub API with a deterministic query list; SHA‑256 checksums are recorded.
- The CodeLlama model version and generation parameters are stored alongside each snippet.
- Every figure and statistic in the PDF can be traced back to a single row in a Parquet/JSON artifact.

Enjoy your reproducible study!

---


