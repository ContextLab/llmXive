---
action_items:
- id: d3af76d9b3e2
  severity: science
  text: Report standard deviations or 95% confidence intervals for all success rate
    metrics in Tables 1-3 and Figures 3-5. Point estimates alone are insufficient
    to claim 'significant' improvements.
- id: 7627ceaa4b6a
  severity: science
  text: Explicitly state the number of random seeds used for training and evaluation.
    The current text implies single-run results, which undermines reproducibility
    and statistical validity.
- id: 1b06fbd12871
  severity: science
  text: Perform and report statistical significance tests (e.g., bootstrap or paired
    t-tests) for key comparisons (ICWM vs. MV) to substantiate the claim of 'significant
    outperformance' in the Abstract and Section 4.2.
- id: 1cf99003c2de
  severity: writing
  text: Clarify the total episode count calculation in Section 4.1. The expression
    '$500 \times 15 \times 4$' is ambiguous (30,000 total? per suite?). Define the
    denominator for success rates clearly.
artifact_hash: 1607b7a56c94fa04d6447f07acdf09cff37e83d8d846355c78db174b7f1d3ac9
artifact_path: projects/PROJ-796-in-context-world-modeling-for-robotic-co/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-28T05:48:39.357255Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: full_revision
---

The statistical rigor of the empirical evaluation is insufficient to support the paper's central claims. While the experimental design (cross-view protocol, real-robot validation) is sound, the reporting of results lacks necessary uncertainty quantification.

First, the Abstract and Section 4.2 claim that ICWM "significantly outperforms" baselines. In scientific literature, "significantly" implies statistical significance. However, Tables 1 and 2 (Appendix) and Figures 3-5 report only point estimates (success rates) without standard deviations, confidence intervals, or p-values. Without variance metrics, it is impossible to determine if the observed 13.0% improvement (Section 4.2) is robust or due to random fluctuation.

Second, the number of random seeds is not specified. Section 4.1 mentions training on 8 GPUs but does not state if results are averaged over multiple seeds (e.g., 3-5 runs). If results are from a single seed, the statistical power is negligible. This is critical for the ablation study in Table 3, where small differences (e.g., 25.0% vs 21.6%) are interpreted as meaningful.

Third, the episode count calculation in Section 4.1 is ambiguous. The text states "$500 \times 15 \times 4$ total episodes." If this means 30,000 episodes per suite, it is unusually high for LIBERO; if it means 30,000 total across all suites, the per-viewpoint sample size is small. The denominator for success rates must be explicitly defined to ensure reproducibility.

Finally, multiple comparisons are made across 6 OOD viewpoints, 4 task suites, and 2 platforms without correction. While the trend is consistent, the lack of error bars makes it difficult to assess the reliability of the gains on specific viewpoints (e.g., 135° where performance is low for all methods).

To proceed, the authors must re-run experiments with multiple seeds, report variance, and conduct formal significance testing.
