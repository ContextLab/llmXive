# Research: Evaluating the Impact of Code Generation on Code Review Quality Using LLMs

## Executive Summary

This research investigates whether LLM-generated code impacts code review quality, measured by comment density, resolution time, and complexity. The study utilizes an observational design, comparing PRs classified as "LLM-generated" (via bot signatures and statistical detectors) against "human-authored" PRs from high-profile open-source repositories. Due to the expected small sample size of LLM PRs, the primary statistical analysis will use non-parametric methods (Mann-Whitney U) to ensure robustness against non-normal distributions and low power.

## Dataset Strategy

### Primary Data Source
The study relies on **programmatic access to the GitHub API** to fetch real-time data from the prioritized repositories: `psf/requests`, `microsoft/vscode`, and `numpy/numpy`. This approach ensures data is obtained directly from the source, satisfying the requirement for open, downloadable data without credentials (API tokens are standard and do not require registration).

*Note: The "Verified datasets" block in the prompt contains URLs for LLM-bot leaderboards and sample PR datasets (e.g., `loubnabnl/prs-v2-sample`). While these are verified, they do not contain the specific metadata (comment counts, merge times, diffs) required for the *current* study's metrics (FR-003, FR-005) nor the specific repositories listed in the spec. Therefore, the research plan prioritizes **direct GitHub API acquisition** for the target repositories. The verified HuggingFace datasets will be used only if the API fails to yield sufficient LLM-classified PRs, serving as a fallback for training the secondary detector.*

### Secondary Detector Training (Fallback)
If the primary API acquisition yields insufficient LLM samples (<10), the secondary statistical detector (FR-007) will be trained on the verified HuggingFace dataset to avoid construct validity issues (training on the target data itself would be tautological):
* **URL**: `
* **Usage**: This dataset provides labeled PRs (author types) to train a lightweight n-gram or entropy-based classifier. The detector is trained on *external* data and then applied to the target repos to identify "LLM-like" patterns, ensuring the classification is not purely tautological.

### Data Feasibility Check
* **Variable Availability**: The GitHub API provides `comment_count`, `created_at`, `merged_at`, `user.login`, `diff_url`, `created_at` (for temporal analysis). This covers all required variables for FR-003 and FR-005.
* **Sample Size & Power**: The spec assumes a minimum of 10 LLM PRs. A power analysis indicates that for a medium effect size, a sufficient sample size per group is required for [deferred] power. With N~10, the study is severely underpowered for detecting small effects. **Therefore, the primary analysis uses Mann-Whitney U (non-parametric) to handle small N and non-normality, and results will be framed as "exploratory" with confidence intervals.**
* **Streaming**: Data will be streamed in batches to ensure memory usage remains within acceptable limits (Constitution Principle VI).

## Methodology

### Phase 1: Data Acquisition & Classification
1. **Fetch**: Retrieve up to 200 PRs from `psf/requests`. If LLM count < 10, proceed to `microsoft/vscode`, then `numpy/numpy`.
2. **Primary Labeling**:
 * **LLM**: Match commit message/bot name against known signatures (e.g., "Copilot", "github-copilot").
 * **Human**: Default label.
 * **Ambiguous**: If confidence < 0.6, label `human` but flag for audit.
3. **Secondary Validation (FR-007)**: Run a statistical detector (code entropy/n-gram anomaly) trained on **external HuggingFace data** on the `llm` cohort. If the score deviates significantly from the human baseline, the label is reinforced.
4. **Manual Audit (SC-004)**:
 * **Sample Size**: Select `max(10, of N_LLM)` PRs. If `N_LLM < 10`, audit [deferred].
 * **Ground Truth**: Human expert judgment of code origin (e.g., "Does this code exhibit LLM artifacts?").
 * **Validation Metric**: The secondary detector score is recorded and compared against the human label (as required by SC-004).
 * **Threshold**: Error rate must be < 5% to proceed.

### Phase 2: Metric Extraction
* **Comment Density**: `comment_count` / `lines_changed`.
* **Resolution Time**: `(merged_at - created_at)` in minutes.
* **Temporal Covariates**: Extract `hour_of_day` and `day_of_week` from `created_at` to control for maintainer availability (Methodology Concern: Temporal Confounds).
* **Complexity**: Calculate Cyclomatic Complexity (CC) and Lines of Code (LOC) for the diff.
 * *Fallback*: If memory > 6GB during analysis, revert to LOC + simple heuristic (Constitution Principle III).

### Phase 3: Statistical Analysis
* **Primary Test**: **Mann-Whitney U Test** (Non-parametric) for:
 1. Median Comment Density (`llm` vs `human`).
 2. Median Resolution Time (`llm` vs `human`).
 * *Rationale*: Robust to small N, skewness, and outliers common in software engineering data.
* **Sensitivity Analysis**:
 * **T-Test**: Independent two-sample t-tests (Welch's) are run as a sensitivity check only.
 * **FR-008**: Re-run primary tests using only PRs confirmed by the secondary detector.
* **Confounding Control**: Use robust regression or stratified Mann-Whitney tests to control for `hour_of_day` and `day_of_week`.
* **Effect Size**: Calculate Rank-biserial correlation (for Mann-Whitney) and Cohen's d (for t-test sensitivity).
* **Significance**: Alpha = 0.05.
* **Assumption**: Observational study; results are **associational**, not causal.

## Statistical Rigor & Limitations

### Multiple Comparison Correction
* **Plan**: Since the primary hypotheses are limited to two (comment density, time-to-merge), a Bonferroni correction is not strictly applied but acknowledged. If additional metrics are explored, a correction factor will be applied.
* **Rationale**: The spec limits the scope to 2-3 primary comparisons; however, the limitation is noted in the discussion.

### Power & Sample Size
* **Limitation**: The study relies on the natural occurrence of LLM PRs. If the total N < 30 (15 per group), the study is underpowered to detect small effect sizes.
* **Mitigation**: The plan explicitly checks for N >= 10 per group. If N is low, results are reported as "exploratory" with confidence intervals. The use of Mann-Whitney U mitigates the risk of Type I error from non-normality in small samples.

### Confounding Variables
* **Complexity**: Code complexity is a known confounder. The plan includes a correlation analysis (SC-003) between complexity and review metrics.
* **Temporal**: `hour_of_day` and `day_of_week` are extracted and used as covariates in robust regression or stratified analysis to isolate the code quality effect from maintainer availability.

### Causal Inference
* **Constraint**: As an observational study, no randomization exists. Claims will be framed as "LLM code is associated with..." rather than "LLM code causes...".

## Decision/Rationale: CPU vs. GPU

* **CPU-First**: All statistical tests (Mann-Whitney U, correlation), complexity metrics (cyclomatic complexity via `radon` or `networkx`), and data processing (pandas, statsmodels) are CPU-tractable and fit within the 7GB RAM / 6h limit.
* **No GPU Required**: The study does not require fine-tuning large language models or running diffusion models. The secondary detector uses lightweight statistical methods (entropy/n-grams) or a pre-trained BERT model (if memory allows) which can run on CPU for small datasets.
* **Fallback**: If a pre-trained model fails to load (memory > 6GB), the plan falls back to heuristic metrics (LOC + CC) as specified in FR-005.

## Verified Datasets (Cited)

* **Primary Source**: GitHub API (Direct Fetch).
* **Fallback for Detector Training**:
 * `
 * `
 * *Note*: These are used *only* if the primary API acquisition fails to provide sufficient labeled data for the secondary detector training.
