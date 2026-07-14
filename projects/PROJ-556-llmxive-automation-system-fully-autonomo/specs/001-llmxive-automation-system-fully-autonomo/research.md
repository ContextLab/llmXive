# Research: llmXive Automation System (001-gene-regulation)

## Summary

This research phase validates the dataset strategy, defines the literature corpus approach, and confirms the feasibility of the proposed CPU-only pipeline. The primary challenge is ensuring that the selected datasets contain the necessary variables for hypothesis generation and that the novelty scoring mechanism is robust against circular validation.

## Dataset Strategy

The system requires standardized datasets (CSV/Parquet) from UCI, OpenML, or HuggingFace. The following verified sources are used:

| Dataset Source | Verified URL | Type | Suitability |
|:--- |:--- |:--- |:--- |
| UCI HAR (CSV) | ` | Time-series activity | **High**. Contains sensor data, suitable for generating hypotheses about activity patterns. **Note**: Both train and test splits are fetched via HuggingFace loader to ensure full context. |
| UCI Shopper (Parquet) | ` | E-commerce behavior | **High**. Contains demographic and purchase data, suitable for correlation hypotheses. |
| APIs (Metadata) | ` | API metadata | **High**. Structured data, suitable for predicting API usage or performance. **Consolidated**: The three API datasets (new_vt_apis, cvecpe_apis, all_apis_for_multiapi) are treated as a single "API Metadata" source for clarity, though this limits domain diversity. |
| APIs (Metadata) | ` | API metadata | **High**. (Consolidated with above). |
| APIs (Metadata) | ` | API metadata | **High**. (Consolidated with above). |

**Excluded Datasets**:
- **UCI DROP**: Excluded. It is a reading comprehension dataset (text QA pairs) and lacks the tabular variables (predictors/outcomes) required for the statistical correlation hypotheses described in the plan.

**Variable Fit Check**:
- **UCI HAR**: Contains `activity_label`, `accelerometer`, `gyroscope`. Suitable for hypotheses like "Activity X correlates with sensor Y variance."
- **UCI Shopper**: Contains `age`, `gender`, `income`, `purchase_amount`. Suitable for hypotheses like "Income level predicts purchase amount."
- **APIs**: Contains `api_name`, `response_time`, `category`. Suitable for hypotheses like "API category X has lower response time than Y."

**Risk**: If a dataset lacks a required variable for a specific hypothesis (e.g., a hypothesis requires "post-task anxiety" but the dataset only has "trait anxiety"), the hypothesis generation agent must be constrained to use only available variables. This is enforced by passing the dataset schema to the LLM prompt.

## Literature Corpus Strategy

The novelty score is computed by comparing generated hypotheses against a local literature corpus.
- **Source**: The corpus must be derived from literature published *after* the LLM's training cutoff to avoid circular validation.
- **Construction**: Since no pre-existing verified corpus is provided, the system will generate a small, CPU-tractable index using `sentence-transformers` and a small set of recent scientific abstracts (e.g., from arXiv or PubMed, sampled to fit 2GB).
- **Date Filtering**: A specific step filters the corpus to ensure **all items have a publication date strictly after the LLM's training cutoff**. Pre-cutoff items are discarded.
- **Fallback**: If the corpus is empty or too small, novelty scores default to 0.5 (neutral) with a warning. Hypotheses with this score are flagged as 'non_novel' and retained in logs.

**Constraint**: The corpus must be constrained to a manageable size to fit within the 7GB RAM limit alongside the dataset and model.

## Statistical Rigor

- **Multiple Comparisons**: When testing >3 ArchConfig variations, **Benjamini-Hochberg False Discovery Rate (FDR)** correction is applied to control false discoveries while preserving power (superior to Bonferroni for N=100). (FR-007).
- **Sample Size**: 20 hypotheses per dataset (total 100 for 5 datasets) is the target. **Exploratory Nature**: The study is explicitly labeled as exploratory. Non-significant results cannot rule out the hypothesis due to limited power (N=100) and likely small effect sizes. (Assumption: Statistical Power).
- **Causal Claims**: The study is observational (correlational). No causal claims are made about LLM architecture causing novelty; claims are framed as associations.
- **Collinearity**: If predictors are definitionally related (e.g., "total score" and "sub-score"), independent effects are not claimed; relationships are reported descriptively.
- **Model Choice**: **Linear Mixed-Effects Models (LMM)** are used to account for dataset-level clustering (hypotheses from the same dataset are not independent). Random intercepts per dataset are included.
- **Normality Check**: A Shapiro-Wilk test is performed on novelty scores. If normality is violated, non-parametric methods (Kruskal-Wallis) are used.

## Decision Rationale

- **CPU-Only**: The GitHub Actions free tier (limited CPU and RAM resources) cannot support GPU training or large-LLM inference. The plan uses `all-MiniLM-L6-v2` (80MB) for embeddings and small distilled models for generation.
- **Sampling**: Data is sampled to fit RAM. If a `MemoryError` occurs, the system retries with a random sample (120s max).
- **Novelty Metric**: Semantic similarity (cosine distance) is used as a proxy for novelty. **Plausibility Check**: To address construct validity, a perplexity score is used to filter gibberish before correlation. **Frozen Index**: The index is pre-computed and frozen, independent of the ArchConfig being tested, to avoid tautology.
- **ArchConfig**: Defined to include **structural parameters** (context window, model size) to isolate specific structural limitations rather than general model quality, avoiding trivial correlations.

## Edge Cases

- **Empty Corpus**: Default novelty score to 0.5, log warning, flag as 'non_novel' and retain.
- **MemoryError**: Retry with sampled data, log `ResourceExceeded`.
- **Logical Impossibility**: Static analysis flags "correlate X with itself" before execution.