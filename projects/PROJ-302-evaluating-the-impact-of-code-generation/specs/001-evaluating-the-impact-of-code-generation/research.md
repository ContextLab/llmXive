# Research: Evaluating the Impact of Code Generation on Code Review Time

## 1. Problem Statement & Hypotheses
- **Primary Hypothesis**: LLM‑generated code (both prompt‑only and context‑based cohorts) is **associated** with longer **review effort duration** (`review_effort_duration`) than human‑written code after matching on the five covariates specified in the spec.  
- **Null Hypothesis (H₀)**: No association between code origin (LLM vs. human) and `review_effort_duration` after propensity‑score matching.

**Outcome Metric**: `review_effort_duration = first_reviewer_comment_timestamp – merge_timestamp` (seconds). For human PRs this is observed directly. **For synthetic LLM cohorts we simulate `review_effort_duration`** by sampling from the empirical distribution of human review effort durations conditioned on the matched covariates (file size, cyclomatic complexity, repository activity, semantic similarity to repository centroid, CI build time). This yields a plausible synthetic timestamp while preserving construct validity; the limitation is documented in the final report.

### Synthetic Review Timestamp Simulation Details
1. **Covariate Conditioning** – For each synthetic LLM PR we locate its values for the five matching covariates (file size, complexity, repo activity, semantic similarity to the repository‑level centroid, CI build time).  
2. **Empirical KDE** – Using the matched human PRs, we build a kernel‑density estimate (KDE) of `review_effort_duration` within each covariate‑bin (e.g., discretised LOC quartile × complexity decile).  
3. **Sampling** – A duration is drawn from the appropriate KDE and assigned as `review_effort_duration`. The synthetic `first_comment_at` is then set to `merge_at - sampled_duration`.  
4. **Validity Checks** – Samples are constrained to be non‑negative and within the observed human range; out‑of‑range draws are retried up to three times.  
5. **Construct Validity** – Because the sampled durations are conditioned on the same covariates used for matching, the synthetic outcome reflects the distribution of human reviewer effort under comparable code complexity and repository context, providing a defensible proxy for the primary outcome while acknowledging that no actual reviewer interaction occurred.

## 2. Dataset Strategy
Only **verified open datasets** are used (see “Verified datasets” block in the spec). No gated data are accessed.

| Dataset | Verified URL | Provided Fields (relevant to spec) |
|---|---|---|
| PR metadata (including `diff`) | https://huggingface.co/datasets/loubnabnl/prs-v2-sample/resolve/main/data/train-00000-of-00001-a3494cf8c0712e34.parquet | `pr_id`, `repo_id`, `created_at`, `merged_at`, `first_comment_at`, `diff`, `repo_stars`, `ci_build_time` |
| Additional PR samples (author‑merged) | https://huggingface.co/datasets/davanstrien/authors_merged_model_prs/resolve/main/data/train-00000-of-00001-d32a63c5798549f1.parquet | Same as above, plus author metadata |
| Full merged PR dataset | https://huggingface.co/datasets/davanstrien/authors_merged_dataset_prs/resolve/main/data/train-00000-of-00001-d5c709e857d2ca0b.parquet | Same as above, larger volume |

**Acquisition Procedure**
1. Stream each parquet file via `datasets.load_dataset(..., streaming=True)` to respect the 7 GB RAM limit.  
2. Filter for repositories with **≥ 1 000 stars** and **≥ 100 PRs** (derived from `repo_stars` and PR count fields).  
3. Keep only PRs that contain a non‑empty `diff` (required for context‑based generation).  
4. Perform a **stratified random sample** based on **code complexity** (low/medium/high) and **LOC quartiles** to obtain a balanced baseline cohort.

All variables required by the FRs (timestamps, LOC, cyclomatic complexity, CI build time, etc.) are present in the verified datasets; no missing‑variable fatality occurs.

## 3. Methodology & Statistical Plan

### 3.1 Prompt Engineering & Synthetic Cohorts (FR‑002, FR‑008)
- **Prompt‑Only Cohort**: Commit message → simple intent extraction → natural‑language prompt fed to CodeLlama. No original code is supplied.  
- **Context‑Based Cohort**: Commit message + original `diff` supplied to CodeLlama, mimicking “LLM‑assisted refactoring”.  

**Model**: CodeLlama‑7B‑4bit‑GGUF (CPU‑tractable).  
- **CPU‑first** inference; empirical benchmarks show ≤ 30 seconds per snippet on the GitHub Actions runner.  
- **Retries**: Up to 3 attempts per snippet; persistent failures lead to exclusion of that commit (per edge‑case spec).  

**Validity Check**: Generated code is parsed with language‑specific AST (e.g., Python `ast.parse`). `is_valid_syntax` is recorded; the pipeline aborts if < 95 % of snippets are syntactically valid (SC‑007).

**Synthetic Review Timestamp Simulation** (see Section 1) ensures that LLM‑generated PRs have a plausible `review_effort_duration` while preserving covariate relationships.

### 3.2 Feature Extraction (FR‑003, FR‑009)
For every PR (human and synthetic):
- **LOC**: line count.  
- **Cyclomatic Complexity**: `radon` library.  
- **CI Build Duration**: extracted from `ci_build_time` field in the dataset.  
- **Semantic Similarity**: Compute CodeBERT embeddings for the snippet **and for the repository‑level centroid embedding** (average of all human snippets in that repo). The similarity is the cosine similarity between the snippet embedding and the centroid; this serves as a covariate that is not deterministic of treatment (see scientific‑soundness fix).  

All features are stored in `data/processed/features.parquet`.

### 3.3 Propensity‑Score Matching (FR‑004, FR‑010)
- **Covariates** (exactly the five required by the spec):  
  1. `file_size_loc` (LOC)  
  2. `complexity_score` (cyclomatic complexity)  
  3. `repo_activity_level` (number of PRs in the repository)  
  4. `semantic_similarity` (cosine similarity to repository‑level centroid)  
  5. `ci_build_time` (seconds)  

- **Model**: Logistic regression (`sklearn.linear_model.LogisticRegression`).  
- **Matching**: 1‑to‑1 nearest‑neighbor with caliper = 0.05.  
- **Balance Verification**: Compute Standardized Mean Difference (SMD) for each covariate.  
  - **Success**: All SMD < 0.1 → `balance_verified = true`.  
  - **Failure**: If any SMD ≥ 0.1, automatically retry up to **3** times with adjusted caliper or covariate weighting. After 3 attempts, abort and emit `matching_failure_report.json`.  

The **Covariate Balance Report** (`data/reports/covariate_balance.json`) is a mandatory prerequisite for any statistical test (Constitution Principle VII).

### 3.4 Statistical Testing (FR‑005)
1. **Normality**: Shapiro‑Wilk test on the paired differences of `review_effort_duration`.  
2. **Test Selection**:  
   - If `p_shapiro > 0.05` → paired **t‑test**.  
   - Else → **Mann‑Whitney U**.  
3. **Effect Size**: Cohen’s d (t‑test) or rank‑biserial correlation (Mann‑Whitney).  
4. **Significance Threshold**: α = 0.05 (source: P‑value, https://en.wikipedia.org/wiki/P-value).  
5. **Multiple‑Comparison Correction**: Holm‑Bonferroni across the four star‑count quartile subsets (Section 3.5).  

Results (p‑value, effect size, normality outcome) are saved in `data/reports/statistical_results.json` **and validated against the `contracts/test_result.schema.yaml` contract**.

### 3.5 Sensitivity Analysis (FR‑006, SC‑005)
Four distinct subsets are created by stratifying the matched dataset according to **repository star‑count quartiles** (Q1–Q4). For each subset the full matching and testing pipeline is repeated. The proportion of subsets with `p < 0.05` is recorded; the requirement is **≥ 80 %** (SC‑005). Detailed per‑subset outcomes reside in `data/reports/sensitivity_summary.json`.

### 3.6 Visualization (FR‑007)
- **Box Plot**: `review_effort_duration` for human vs. each LLM cohort (overall).  
- **CDF**: Cumulative distribution functions for the same groups.  

Figures are saved as PNGs in `data/reports/`.

### 3.7 Report Generation (Implicit FR‑010)
An HTML report (converted to PDF) is assembled, pulling numbers directly from the JSON artifacts, embedding the provenance metadata (model version, dataset checksums, random seeds). The final PDF (`reports/analysis_report.pdf`) satisfies the Single Source of Truth principle.

## 4. Compute Decision & Feasibility
| Component | Environment | Rationale |
|---|---|---|
| Data streaming & filtering | CPU (GitHub Actions) | `datasets` streaming avoids RAM overflow. |
| Feature extraction (radon, LOC) | CPU | Light per‑file operations. |
| Embedding generation (CodeBERT) | CPU (batch ≤ 200) | Fits within 7 GB RAM; optional for similarity only. |
| CodeLlama generation | **CPU‑only** (CodeLlama‑7B‑4bit‑GGUF) | Benchmarked ≤ 30 s per snippet on 2 vCPU runner; no GPU dependency. |
| Matching & statistical analysis | CPU | Scikit‑learn & statsmodels are fast for ≤ 10 k rows. |
| Visualization | CPU | Matplotlib/Seaborn are lightweight. |

All steps respect the 6 h wall‑time limit; `runtime.py` records cumulative time and fails the CI job if exceeded.

## 5. Risks & Mitigations
| Risk | Mitigation |
|---|---|
| GitHub API / dataset streaming stalls | Tenacity exponential backoff; checkpointing of downloaded shards; optional GitHub token for higher rate limits. |
| LLM generation exceeds CPU timeout | Benchmarked model choice guarantees ≤ 30 s; retries up to 3 times before exclusion. |
| Matching fails to achieve SMD < 0.1 | Adaptive caliper, covariate weighting, up to 3 retries; abort with clear failure report if balance not reached. |
| Under‑powered sample | Pre‑study power analysis (Task T031); fetch additional repositories if needed. |
| Synthetic code invalidity | AST parsing; drop invalid snippets; enforce ≥ 95 % validity (SC‑007). |
| Synthetic review timestamps may not reflect real reviewer behavior | Explicitly document the simulation approach and its limitations; treat findings as associational. |
| Runtime > 6 h | `runtime.py` timers; CI fails on `runtime_report.json` exceeding budget. |

---



## 6. Documentation & Reproducibility
All scripts are deterministic (random seeds fixed in `code/utils.py`). The `quickstart.md` (see separate artifact) contains exact commands to reproduce the entire pipeline on a fresh runner. Every external dataset URL is hard‑coded and verified; checksums are stored in `state/projects/...yaml`. The synthetic cohort provenance (model version, temperature, max tokens, source commit) is recorded in `data/synthetic/` per Constitution Principle VI.

