# Research: Evaluating the Impact of Code Generation Models on Code Review Efficiency

## Dataset Strategy

### Source Selection & GHTorrent Gate
The primary dataset MUST be the **Gerrit Chromium code-review dataset via GHTorrent** (FR-001). 
- **Gate**: If GHTorrent is inaccessible or the dump lacks required fields, the project halts and a Spec Amendment Request is generated to switch to the verified HuggingFace proxy.
- **Variables**: The dataset provides `title`, `diff/patch`, `created_at`, `updated_at`, `comment_count`. 
- **Limitation**: `review_time_seconds` and `perceived_difficulty` are often missing or unreliable in historical PR data.
  - **Primary Cohort (N≥1000)**: Analysis uses `comment_count` as a **Proxy Effort** metric.
  - **Validation Study (N≥50)**: Actual `review_time` and `perceived_difficulty` are collected via human survey to validate the proxy and test for bias.

| Dataset Name | Verified URL | Suitability |
| :--- | :--- | :--- |
| **Gerrit Chromium (GHTorrent)** | `http://ghtorrent.org/` | Primary source. Contains diffs, timestamps, comments. |
| **Verified Gerrit Source (HF)** | `https://huggingface.co/datasets/verified_gerrit_source` | Proxy source. Used if GHTorrent fails. |

**Variable Mapping & Proxy Outcome**

| Spec Requirement | Dataset Field | Handling |
| :--- | :--- | :--- |
| Code Snippet | `diff` / `patch` | Directly extracted. |
| Review Time | `created_at` / `updated_at` → `review_time_seconds` | **Unavailable for Primary Cohort**. Used only in Validation Study. |
| Comment Count | `comment_count` | **Primary Outcome** for large-scale analysis (Proxy Effort). |
| Perceived Difficulty | *Not in Dataset* | Collected via survey for Validation Study only. |

### Variable Risk Mitigation
- **Missing `review_time_seconds`**: Primary analysis uses `proxy_effort = comment_count`. Validation study provides ground truth.
- **Missing `perceived_difficulty`**: Not measured for historical data. Only measured for the Validation Study subset (FR-011).

## Model Strategy

### Model Selection & Memory Management
- **StarCoder‑1B** (CPU‑only, `float16`, ~4 GB RAM).
- **CodeGen‑350M** (CPU‑only, ~1.5 GB RAM).
- **Memory‑Check**: Script estimates RAM before loading. If >5 GB, fallback to CodeGen‑350M only.
- **Model Capability Benchmark**: Pre-run benchmark of CodeGen-350M to ensure it meets `Pearson r ≥ 0.7` and `[deferred] generation success`. If failed, fallback to CodeGen-2B or flag spec amendment.

### Prompt Template & Matched-Pair Design
To address confounding (methodology-0311797a), the prompt includes the **full reconstructed context**:
`"Context: [Extracted Imports + Function Signatures + Surrounding Code]\nTask: [PR Title]\nWrite a function in <language> that solves the task."`
This ensures the LLM attempts to solve the *exact same* problem instance as the human, creating a true matched pair.

## Statistical Methodology

### Primary Analysis (Mixed‑Effects Model)
- **Outcome**: `proxy_effort` (comment_count).
- **Fixed Effects**: `code_origin` (human vs generated), `cyclomatic_complexity`, `context_complexity` (derived from diff size/depth).
- **Interaction**: `code_origin * context_complexity` to isolate the origin effect from context complexity.
- **Random Effects**: `(1|project_id)` and `(1|problem_statement)` (true matched pair ID).
- **Formula**: `proxy_effort ~ code_origin * cyclomatic_complexity + (1|project_id) + (1|problem_statement)`.
- **Multiple Comparisons**: Bonferroni correction.
- **Collinearity**: VIF check; drop if >5.

### Proxy Attenuation Correction & Power Adjustment
- **Problem**: `comment_count` is a weak proxy for `review_time`, leading to attenuated effect sizes and reduced power.
- **Mitigation**: 
  1. Calculate Pearson correlation (r) between `comment_count` and `review_time` in the Validation Study.
  2. Apply a correction factor (1/r) to the observed effect sizes in the primary analysis to estimate the "true" effect size.
  3. Perform a post-hoc power calculation based on the observed r to determine if the sample size is sufficient given the attenuated signal. If power < 0.8, the report will explicitly state this limitation.

### Transfer Estimation (Statistical Bridge)
- **Goal**: Compare Human vs. LLM effort despite the lack of `review_time` in the primary Human cohort.
- **Mechanism**:
  1. **Train Human Effort Model**: Fit a model on the historical human cohort using `comment_count` (proxy) as the outcome to predict "Expected Effort" based on code metrics.
  2. **Predict Counterfactual**: Apply this model to the Generated cohort to predict their "Expected Effort" (what their effort would have been if they were human).
  3. **Compare**: Compare the "Actual Effort" (from Validation Study) of Generated code against the "Predicted Effort" of Human code (scaled by the proxy correlation) and the "Predicted Effort" of Generated code.
  4. **Result**: This creates a statistical bridge allowing for a direct group comparison of effort, even though the primary Human cohort lacks `review_time`.

### Sensitivity Analyses
- **LOC Threshold Sweep**: 15, 30, 50 LOC.
- **Transfer Assumption**: Compare residual distributions between origins.

### Validation Study (FR‑011, FR‑012)
- Sample ≥ 50 `valid` generated snippets and matched human snippets.
- **Human Review**: Collect `review_time`, `comment_count`, `difficulty` (5-point Likert).
- **Bias Analysis**: 
  1. Compute residuals of the primary model on the validation set.
  2. Test for **Systematic Bias**: Compare mean residuals between Human and LLM groups (t-test). This addresses the "validity trap" where high Pearson r masks systematic over/under-prediction.
  3. Compute Pearson r (target ≥ 0.7).
  4. Wilcoxon signed-rank test on paired differences.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Dataset Mismatch** | Fatal if GHTorrent unavailable. | **Hard Gate**: Project halts; Spec Amendment requested. |
| **Confounding by Context** | Spurious `code_origin` effect. | **Matched-Pair Design**: LLM uses full context; Random effect `(1|problem_statement)`. |
| **Proxy Effort Validity** | Weak correlation with true effort. | **Validation Study**: Measures actual effort; **Proxy Attenuation Correction** applied to primary analysis. |
| **Semantic Failure** | Trivial code skews results. | **Semantic Filter**: Excludes nonsensical/trivial generations from "valid" set. |
| **OOM on CPU** | Pipeline crash. | **Memory-Check**: Fallback to CodeGen‑350M. |
| **Insufficient Model Capability** | Fallback model fails quality targets. | **Model Capability Benchmark**: Pre-run check; fallback to CodeGen-2B or spec amendment. |
