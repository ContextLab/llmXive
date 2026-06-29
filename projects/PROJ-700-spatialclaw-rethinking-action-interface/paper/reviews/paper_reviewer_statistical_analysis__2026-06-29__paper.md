---
action_items:
- id: 8d958485b3a1
  severity: science
  text: The paper reports aggregate accuracy across 20 heterogeneous benchmarks (Tab.
    1, Tab. 2) without addressing the statistical validity of averaging metrics with
    different distributions (binary Acc vs. continuous MRA). A weighted average or
    a unified statistical test (e.g., Friedman test with Nemenyi post-hoc) is required
    to support the claim of 'consistent gains' across the board, as simple arithmetic
    means may be biased by benchmarks with different sample sizes or difficulty distributions.
- id: 6f905221da96
  severity: science
  text: The ablation study in Tab. 3 (ablation_components.tex) uses a subsample of
    500 examples per benchmark for the 'No utility functions' and 'No perception tools'
    variants, while the main results use up to 1,000. The paper fails to report confidence
    intervals or standard errors for these ablation results. Without variance estimates,
    it is impossible to determine if the reported differences (e.g., 56.4 vs 56.9)
    are statistically significant or within the noise floor of the sampling process.
- id: 3232862be751
  severity: science
  text: The 'LLM-as-Judge' analysis in the Supplementary Material (Fig. C.1, C.2)
    relies on a single proprietary model (Gemini-3.1-Pro) to categorize failure modes
    and attribute wins. The review must include inter-rater reliability metrics (e.g.,
    Cohen's Kappa) or a sensitivity analysis using multiple judge models to validate
    that these qualitative attributions are not artifacts of the specific judge model's
    biases.
artifact_hash: 03b4b7546f79862eef36a0d430e3a6b82062f65b52d01a2c8d4c65b5c5b34086
artifact_path: projects/PROJ-700-spatialclaw-rethinking-action-interface/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T21:11:41.943972Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in the paper is extensive in terms of the number of benchmarks and models tested, but lacks rigor in the aggregation and significance testing of the results.

First, the primary claim of "consistent gains" relies on the unweighted arithmetic mean of accuracy scores across 20 benchmarks (Tab. 1, Tab. 2). These benchmarks utilize mixed evaluation metrics: some use binary accuracy (Acc), while others use Mean Relative Accuracy (MRA) or composite scores (e.g., SPAR-Bench). Averaging these heterogeneous metrics without normalization or weighting by sample size or difficulty is statistically unsound. The paper should either provide a unified metric (e.g., normalized z-scores per benchmark) or employ a non-parametric statistical test (such as the Friedman test followed by Nemenyi post-hoc) to demonstrate that the performance difference between SpatialClaw and baselines is statistically significant across the set of benchmarks, rather than just showing a higher average.

Second, the ablation study presented in `tables/ablation_components.tex` introduces a significant source of variance. The main results are computed on up to 1,000 samples per benchmark, whereas the ablation variants (I and II) are evaluated on a subsample of 500. The paper reports point estimates (e.g., 56.4% vs 56.9%) but omits confidence intervals or standard errors. Given the stochastic nature of LLM inference and the reduced sample size, the observed differences in the ablation study may not be statistically distinguishable from random noise. The authors must report the standard error of the mean or 95% confidence intervals for all ablation results to validate the claim that "performance degradation is minimal."

Finally, the qualitative analysis of failure modes and win attribution (Supplementary Material, Figs. C.1 and C.2) relies entirely on a single LLM judge (Gemini-3.1-Pro). The paper does not report inter-rater reliability (e.g., Cohen's Kappa) or perform a sensitivity analysis using alternative judges. Without this, the attribution of "code composition" as the driver of 50% of wins is anecdotal and potentially biased by the specific prompting or biases of the chosen judge model. A robust statistical validation of these qualitative claims is necessary.
