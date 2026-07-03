---
action_items:
- id: 04ef436a9dc0
  severity: writing
  text: "Table 1 and Appendix tables report single-point metrics (e.g., AbsRel 0.050)\
    \ for 41 models without any measure of variance (SD, SE, or range). In deep learning,\
    \ results vary by seed; reporting a single run as the definitive score implies\
    \ false precision. Report mean \xB1 SD over \u22653 seeds for all key comparisons,\
    \ or explicitly state results are from a single seed."
- id: 4b7e29493f49
  severity: writing
  text: The abstract and Section 5 claim the proposed method is '+47% / +59% depth
    gains' over DA3-Giant. These are point estimates with no confidence intervals
    or statistical tests (e.g., paired t-test or bootstrap) to determine if the improvement
    is significant or within run-to-run variance. Add a statistical test or report
    the variance across seeds to support the magnitude of the gain.
- id: 757e3af2be46
  severity: science
  text: Table 1 compares 41 models across 4 regimes and multiple metrics (effectively
    >100 pairwise comparisons). The paper highlights 'best' results with color coding
    but applies no correction for multiple comparisons (e.g., Bonferroni, Holm, or
    FDR). Without correction, the probability of false positives (highlighting a model
    as 'best' by chance) is high. Apply a correction or explicitly acknowledge the
    multiplicity risk.
artifact_hash: 306c5e78aff3c136de96c4c6956084c3af89239f10c2fba4682734d1809d3475
artifact_path: projects/PROJ-634-https-arxiv-org-abs-2605-27367/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T21:33:00.354898Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical reporting in this paper suffers from a lack of uncertainty quantification and multiple-comparison control, which undermines the reliability of the comparative claims.

First, the primary results tables (Table 1, and the extensive appendix tables) report performance metrics (AbsRel, AUC@30, ATE, etc.) as single point estimates for each model. In the context of deep learning, where training and inference can be stochastic, a single run does not represent the model's true performance distribution. Reporting a value like "0.050" without a standard deviation (SD), standard error (SE), or range across multiple random seeds creates an illusion of false precision. The reader cannot distinguish between a stable improvement and a lucky run. The authors should report mean ± SD over at least 3 seeds for all reported numbers, or explicitly state that results are from a single seed and treat the numbers as indicative rather than definitive.

Second, the paper makes strong comparative claims, such as the proposed method achieving "+47% / +59% depth gains" over the baseline (DA3-Giant). These are presented as facts without any statistical backing. There are no p-values, confidence intervals, or hypothesis tests (e.g., a paired t-test or bootstrap test) to verify if these gains are statistically significant or merely within the noise of the evaluation. Given the high stakes of benchmarking, a claim of "significant" improvement requires statistical evidence. The authors should either run the appropriate statistical tests on the per-seed results or rephrase the claims to reflect the observed point estimates without implying statistical significance.

Third, the benchmark evaluates 41 models across 4 input regimes and multiple metrics, resulting in a massive number of pairwise comparisons. The paper highlights "best" results using color coding (blue/orange/yellow) but does not apply any correction for multiple comparisons (e.g., Bonferroni, Holm, or Benjamini-Hochberg). When performing hundreds of tests, the family-wise error rate increases dramatically, meaning many of the highlighted "best" results are likely false positives. The authors should apply a multiple-comparison correction to the p-values (if tests are run) or explicitly acknowledge that the rankings are uncorrected and subject to chance. Without this, the claim that one model is definitively "better" than another in specific cells is statistically unsound.
