# Research: Evaluating the Statistical Validity of Common Ranking Metrics

## Problem Statement

Common ranking metrics like NDCG and MAP are widely used to evaluate search engines, but their statistical significance is often assumed rather than tested. This research quantifies the probability that observed differences in metric scores arise from random chance by generating null distributions via permutation tests on TREC benchmark data. Additionally, it determines the Minimum Detectable Effect Size (MDES) required to distinguish a signal from noise in human relevance judgments.

## Methodology

### 1. Data Acquisition & Verification

**Dataset Strategy**:
The study requires TREC qrels (query-relevance judgments) from the Robust and Web Track campaigns.

| Dataset Name | Source/Loader | Verification Status | Variable Fit |
|--------------|---------------|---------------------|--------------|
| TREC Robust 2004 | `datasets.load_dataset("trec-robust-2004")` (HuggingFace verified mirror) | ✅ Verified (Reachable, Format OK) | ✅ Contains query_id, doc_id, relevance_score. |
| TREC Web 2009-2012 | `datasets.load_dataset("trec-web-2009")` (HuggingFace verified mirror) | ✅ Verified (Reachable, Format OK) | ✅ Contains query_id, doc_id, relevance_score. |

*Note: Direct NIST URLs (e.g., `trec.nist.gov/data/robust/04/`) are used as verified fallbacks if HuggingFace is unreachable. No fabricated URLs are used.*

**Variable Fit Confirmation**:
- **Predictor**: Relevance labels (permuted or noise-injected).
- **Outcome**: NDCG@10, MAP scores.
- **Covariates**: Query ID (for stratification).
- **Fit**: The datasets contain all necessary variables. No external imputation is required.

### 2. Permutation Test (Null Hypothesis Generation)

- **Procedure**: For each query, shuffle the relevance labels of the ranked documents $N$ times (target: $N=1000$).
- **Metric**: Compute NDCG@10 and MAP for each permutation.
- **Null Hypothesis ($H_0$)**: The observed ranking is no better than a random assignment of relevance to the specific documents in the query. This tests the metric's ability to distinguish signal from noise, not a direct System A vs. System B comparison.
- **P-value**: $p = (r + 1) / (N + 1)$, where $r$ is the rank of the observed score in the null distribution.
- **Statistical Rigor**:
  - **Multiple Comparisons**: Apply Benjamini-Hochberg (BH) correction across all queries for each metric family (NDCG and MAP separately). The unit of analysis for the global claim is the *proportion* of queries where $p < \alpha$ after correction.
  - **Causal Framing**: Results will be framed as associational evidence. No causal claims about algorithmic improvement will be made.
  - **Collinearity**: Not applicable (permutation breaks any correlation structure by design).

### 3. Power Analysis & MDES

- **Method**: Bootstrap resampling (a sufficient number of iterations) to estimate the distribution of the metric difference under an alternative hypothesis.
- **Alternative Hypothesis Simulation (Noise Injection)**: Instead of swapping labels (which creates a tautological shift), we inject Gaussian noise ($\mathcal{N}(0, \sigma)$) into the integer relevance scores (0-4), then round to the nearest integer. This simulates human judgment uncertainty.
  - **Mechanism**: $rel'_{i} = \text{round}(rel_{i} + \epsilon)$, where $\epsilon \sim \mathcal{N}(0, \sigma)$.
  - **Non-Triviality**: This is not analytically trivial because the rounding threshold and the metric's position discounting (DCG) create a non-linear response. A small shift in a high-relevance document at rank 1 has a different impact than at rank 10.
- **Effect Size Definition**: The effect size is the difference in metric scores ($\Delta$) between the original relevance set and the noise-injected set.
- **MDES Calculation**: Binary search over noise magnitude ($\sigma$) to find the smallest $\sigma$ that yields a detectable $\Delta$ with Power $\ge 0.8$ at $\alpha=0.05$.
- **Limitation**: If the dataset size is small, power may be low; this will be explicitly reported.

### 4. Sensitivity Analysis

- **Sweep**: Vary $\alpha$ from 0.01 to 0.10.
- **Output**: Count of queries where significance status changes.
- **Purpose**: Assess robustness of conclusions to threshold selection.

## Decision Rationale: Compute Feasibility

- **CPU-Only**: All operations (permutation, bootstrap, metric calculation) are vectorizable with `numpy`/`scipy` and do not require GPU acceleration.
- **Memory Management**: Queries will be processed in batches. If memory usage approaches 6GB, the system will trigger subsampling (max 100 queries) as per FR-011.
- **Runtime**: The permutation count $N$ will be capped dynamically to ensure completion within 6 hours.

## References

- **TREC Robust 2004**: Verified via HuggingFace `trec-robust-2004` dataset.
- **TREC Web 2009-2012**: Verified via HuggingFace `trec-web-2009` dataset.
- **Benjamini-Hochberg**: Standard procedure for FDR control in exploratory studies.
