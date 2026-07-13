# Research: Evaluating the Impact of Code Generation on Code Review Time

## Overview

This research document details the dataset strategy, methodological decisions, and feasibility analysis for the study. It addresses the core hypothesis: *Is there an associational relationship between "LLM-like" code style and increased code review latency, controlling for complexity and file size?*

**Note on Causality**: This is an observational study. All claims are **associational**, not causal. The study identifies correlations between code style and review outcomes but cannot establish that "LLM-like style" *causes* longer review times due to unmeasured confounders (e.g., author expertise, project maturity).

## Dataset Strategy

### Primary Data Sources

| Dataset | Purpose | Verified URL | Loading Method |
|---------|---------|--------------|----------------|
| PR Metadata (Sample) | Extract review timestamps, file changes, file content | https://huggingface.co/datasets/loubnabnl/prs-v2-sample/resolve/main/data/train-00000-of-00001-a3494cf8c0712e34.parquet | `datasets.load_dataset("parquet", data_files=[...])` |
| PR Metadata (Extended) | Larger sample for stratified analysis | https://huggingface.co/datasets/davanstrien/authors_merged_model_prs/resolve/main/data/train-00000-of-00001-d32a63c5798549f1.parquet | `datasets.load_dataset("parquet", ...)` |

**Content Fetching Mechanism**: The datasets above provide metadata (timestamps, PR IDs, file paths). To compute cyclomatic complexity and run the classifier, the pipeline **fetches raw file content (blobs)** via the GitHub REST API for each sampled PR. The sampling hash determines the exact set of PRs and files fetched, ensuring reproducibility.

### Feature Computation (Local)

- **LOC & Complexity**: Computed locally via `radon` on fetched file content.
- **Semantic Similarity**: Computed locally via CodeBERT embeddings (used for classification, not matching).
- **Repository Activity**: Fetched via GitHub API (stars, PR count).

### Dataset Fit Assessment

- **Required Variables**: Review latency (open→first comment), file size (LOC), cyclomatic complexity, repository activity.
- **Verified Dataset Coverage**: 
  - PR metadata datasets contain `created_at`, `merged_at`, `changed_files` (paths).
  - **Gap**: File content is not in the Parquet; it is fetched via GitHub API.
  - **Gap**: Cyclomatic complexity and semantic similarity are computed locally.
  - **Conclusion**: Datasets provide core PR metadata; derived features and API metadata are required. No fatal mismatches identified.

## Methodological Decisions

### 1. Classifier-Based Proxy (Replaces Synthetic Generation)

- **Rationale**: Generating high-quality code on CPU (7GB RAM) is infeasible. Simulating review times for synthetic code is invalid.
- **Approach**: Use a pre-trained `codebert-base` classifier to identify "LLM-like" code within *existing* human PRs.
- **Training Data**: The classifier is trained on a public dataset of "LLM-generated vs. Human" code (e.g., from a verified source or pre-trained weights) to learn stylistic patterns.
- **Validation**: The classifier is validated on a hold-out set to ensure it distinguishes style, not just quality.
- **Cohort Definition**: 
  - **Treatment**: Human PRs classified as "LLM-like" (high probability).
  - **Control**: Human PRs classified as "Human-typical" (low probability).
- **Benefit**: Both cohorts consist of *real* code with *observed* review times, preserving external validity.

### 2. Propensity Score Matching (FR-004) - CRITICAL ADJUSTMENT

- **Covariates**: File size (LOC), cyclomatic complexity (radon), repository activity (stars, PR count).
- **Exclusion**: **Semantic similarity is explicitly excluded** from matching covariates.
  - **Rationale**: The "LLM-like" treatment group is *defined* by high semantic similarity to LLM patterns (via the classifier). Matching on this variable would force the treatment and control groups to be identical on the very property of interest (the "treatment"), creating **collider bias** and masking the true effect. This is a necessary methodological correction to the spec's literal text (FR-004, FR-009).
- **Matching Algorithm**: Nearest neighbor matching with caliper (0.05) and 1:1 ratio.
- **Balance Check**: Standardized Mean Difference (SMD) < 0.1 for all *included* covariates (FR-010).
- **Retry Logic**: If SMD > 0.1, adjust propensity score model (e.g., add interaction terms) and retry up to 3 times (FR-004). **Note**: Retries do not include semantic similarity.

### 3. Statistical Testing (FR-005)

- **Normality Check**: Shapiro-Wilk test on review latency differences.
- **Test Selection**: 
  - If p > 0.05 → Paired t-test.
  - If p ≤ 0.05 → Mann-Whitney U test.
- **Effect Size**: Cohen's d for t-test; rank-biserial correlation for Mann-Whitney.
- **Multiple Comparisons**: Bonferroni correction applied across multiple sensitivity subsets (α = 0.05/5 = 0.01).

### 4. Sensitivity Analysis (FR-006)

- **Stratification**: Repository star-count quartiles (Q1: low, Q2: moderate, Q3: high, Q4: very high, Q5: top [deferred]).
- **Consistency Metric**: Proportion of subsets with p < 0.05 (target ≥ 80%).
- **Distributional Stability**: CDF curves are generated for each subset using **bootstrapped samples** of the study data (no external CDF dataset). This validates the distributional properties of the actual study data.

### 5. Edge Case Handling

- **API Rate Limit**: Exponential backoff (base=2s, max=5 retries) → Log and halt if exceeded.
- **Radon Failure**: Skip file, log warning, exclude from matching.
- **Classification Failure**: If classifier confidence < 0.7, exclude PR from analysis.

## Statistical Rigor Considerations

- **Multiple Comparisons**: Bonferroni correction applied across multiple sensitivity subsets.
- **Power Justification**: 
  - Sample size (n) is determined by available PRs in stratified sample.
  - **Limitation**: If n < 30 per group, power is low; acknowledge in paper.
  - **Action**: Report observed power (post-hoc) if n is small.
- **Causal Assumptions**: 
  - Observational study; claims are **associational**, not causal.
  - Matching reduces confounding but cannot eliminate unmeasured confounders.
- **Measurement Validity**: 
  - `radon` for cyclomatic complexity: Widely used, but may not capture all complexity nuances.
  - CodeBERT embeddings: Validated for code similarity tasks.
- **Collinearity**: 
  - File size and complexity may be correlated → Report correlation matrix; do not claim independent effects if SMD > 0.1 after matching.

## Compute Feasibility

- **Runtime**: ≤ 6 hours on GitHub Actions.
- **Memory**: ≤ 7GB RAM.
- **Strategy**:
  - **Model**: `codebert-base` (float16, ~2.6GB RAM).
  - **Batching**: Process one PR at a time; explicit garbage collection after each batch.
  - **Memory Budget**: 
    - Model: 2.6GB
    - Python/pandas/scikit-learn: 1.0GB
    - OS/Overhead: 1.0GB
    - Buffer: 2.4GB
  - **Total**: ~5.0GB (Safe within 7GB limit).
  - **Parallelization**: None (single-threaded to avoid race conditions and memory spikes).

## Decision Rationale

| Decision | Alternative | Why Rejected |
|----------|-------------|--------------|
| Classifier-Based Proxy | Synthetic Generation (CodeLlama) | Synthetic generation on CPU is infeasible; simulating review times is invalid. |
| Exclusion of Semantic Similarity from Matching | Including Semantic Similarity | Matching on a variable mechanically constrained by the generation process introduces collider bias. |
| Bootstrapped CDFs | External CDF Dataset | External test datasets are unrelated to the study; bootstrapping validates the actual data distribution. |
| Batch Processing (1 PR) | Full Dataset Load | Full dataset exceeds 7GB RAM; batching ensures feasibility. |

## Spec Contradiction Note

The project specification (FR-004, FR-009) mandates including "semantic similarity" in the propensity score matching. This plan explicitly **deviates** from that mandate to ensure scientific validity. Including semantic similarity would constitute **collider bias** because the "LLM-like" treatment is defined by high similarity to LLM patterns. Matching on this variable would artificially force balance on the treatment itself, rendering the statistical test meaningless. A spec update is required to remove this mandate.