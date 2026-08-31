# Research: Evaluating the Statistical Validity of Common Ranking Metrics

## Research Question

**Revised**: What is the empirical distribution of NDCG@10 and MAP scores under the null hypothesis of random relevance labels (i.e., no relationship between ranking order and relevance), and how do the observed scores from TREC benchmarks compare to this distribution?

*Note: The original phrasing "Are metrics statistically distinguishable from random chance?" is tautological because metrics are designed to be. This revised question focuses on characterizing the null distribution and quantifying the observed signal's position within it, validating the metric's discriminative power.*

## Methodology Overview

The research employs a **permutation test** framework.
1.  **Null Hypothesis (H0)**: The specific ranking order of documents for a query is unrelated to their relevance labels.
2.  **Procedure**: For each query, relevance labels are randomly shuffled (permuted) N times (N ≥ 1000) to simulate the null distribution of metric scores.
3.  **Comparison**: The observed metric score (from the original ranking) is compared against the null distribution to calculate a p-value: `p = (rank +) / (N + 1)`.
4.  **Interpretation**: A low p-value indicates the observed ranking is significantly better than random chance, validating the metric's sensitivity to the relevance signal. This is a "sanity check" for the metric, not a test of the ranking's scientific significance against a meaningful baseline.

## Verified Datasets

The following datasets are used, verified for public accessibility via `ir-datasets`:

- **TREC Robust 2004**: `trec-robust04` (ir-datasets). Contains a set of queries with relevance judgments.
  - Source: `ir-datasets` library (verified via `ir_datasets.load("trec-robust04")`).
  - Access: Programmatic, no authentication.
- **TREC Web Track 2009-2012**: `trec-web-2009`, `trec-web-2010`, `trec-web-2011`, `trec-web-2012` (ir-datasets).
  - Source: `ir-datasets` library (verified via `ir_datasets.load("trec-web-2009")`, etc.).
  - Access: Programmatic, no authentication.

*Note: The spec mentions downloading from `trec.nist.gov` directly, but `ir-datasets` is the verified, programmatic wrapper that ensures reproducibility and handles checksums, aligning with Constitution Principle I.*

## Dataset Strategy

| Dataset | Source URL | Loader Method | Variables Needed | Status |
|---------|------------|---------------|------------------|--------|
| TREC Robust 2004 | `ir-datasets` | `ir_datasets.load("trec-robust04").qrels_iter()` | query_id, doc_id, relevance | ✅ Verified |
| TREC Web 2009 | `ir-datasets` | `ir_datasets.load("trec-web-2009").qrels_iter()` | query_id, doc_id, relevance | ✅ Verified |
| TREC Web 2010 | `ir-datasets` | `ir_datasets.load("trec-web-2010").qrels_iter()` | query_id, doc_id, relevance | ✅ Verified |
| TREC Web 2011 | `ir-datasets` | `ir_datasets.load("trec-web-2011").qrels_iter()` | query_id, doc_id, relevance | ✅ Verified |
| TREC Web 2012 | `ir-datasets` | `ir_datasets.load("trec-web-2012").qrels_iter()` | query_id, doc_id, relevance | ✅ Verified |

**Data Hygiene**: Raw qrels files will be downloaded once, checksummed (SHA-256), and stored in `data/raw/`. No modifications will be made to raw files. Derived metrics will be stored in `data/processed/`. Subsample logs will record any dropped queries.

## Statistical Rigor

- **Multiple Comparison Correction**: Benjamini-Hochberg (BH) procedure will be applied to p-values across queries for each metric independently to control False Discovery Rate (FDR) at α=0.05.
  - *Limitation*: TREC queries are not strictly independent (shared documents). BH is applied as a robust approximation (Benjamini & Yekutieli 2001), but FDR control is considered "conservative" or "approximate" due to this dependence.
- **Power Analysis**: MDES will be calculated via bootstrap resampling (500 resamples) to determine the smallest effect size detectable with [deferred] power (target power = 0.80, source: Wikipedia "Power (statistics)").
 - **Alternative Hypothesis Simulation**: To simulate an effect size, we will **swap the top-k positions** in the ranking (e.g., swap the top 1 relevant document with the top 1 non-relevant document) while keeping relevance labels fixed. This simulates a "worse" system. A binary search over k (0 to N) will find the smallest k that is detectable with [deferred] power. This correctly measures the ability to detect a *ranking shift*, not a change in ground truth.
- **Causal Framing**: All findings will be explicitly framed as evidence of statistical *association* between metric scores and relevance judgments, not causal algorithmic improvement. The final report will include a dedicated "Statistical Interpretation" section stating this.
- **Collinearity**: Not applicable (metrics are computed on the same relevance judgments; no predictors are being regressed against each other).
- **Measurement Validity**: NDCG@10 and MAP are standard, validated IR metrics. Relevance judgments are from official TREC campaigns.
- **Permutation Count**: N ≥ 1000 permutations per query to ensure p-value stability for α=0.05. If runtime constraints force query subsampling, N=1000 is maintained per query to ensure individual test validity, even if the total number of queries (and thus FDR power) is reduced.

## Compute Feasibility

- **CPU-First**: All computations (permutation, bootstrap, metric calculation) are CPU-tractable. No GPU required.
- **Memory Management**: Queries processed in batches. If memory > 6 GB, subsampling (n=100 queries) is triggered.
- **Runtime**: Target ≤ 6 hours. Subsampling ensures completion within limit.
- **Strategy**:
  1. Load TREC data via `ir-datasets` (Robust 2004 + Web 2009-2012).
  2. For each query, generate N=1000 permutations of relevance labels.
  3. Compute NDCG@10 and MAP for each permutation.
  4. Calculate p-value as (rank + 1) / (N + 1).
  5. Apply BH correction.
  6. Perform bootstrap MDES analysis (using top-k swap method).
  7. Generate sensitivity analysis (alpha sweep).
  8. Output CSVs and PNGs, including explicit "associational" framing text.

## Decision/Rationale

- **Why `ir-datasets`?** It provides verified, checksummed access to TREC data without manual download, ensuring reproducibility (Constitution Principle I).
- **Why Permutation Test?** Non-parametric, distribution-free method suitable for complex metrics like NDCG where analytical null distributions are unknown.
- **Why BH Correction?** Standard for exploratory studies with many tests (queries); more powerful than Bonferroni. Acknowledged as approximate due to query dependence.
- **Why Bootstrap for MDES?** Analytical power calculations are intractable for ranking metrics; bootstrap empirically estimates power under alternative hypotheses.
- **Why Top-K Swap for MDES?** Correctly simulates a ranking shift (system performance change) without altering the ground truth (relevance labels), avoiding methodological confounds.
