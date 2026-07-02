---
action_items:
- id: 770f7cc7f056
  severity: science
  text: "Report confidence intervals or standard errors for the primary benchmark\
    \ metrics (Consensus Gain, Timeliness, Effectiveness) in Table 1 and Table 3.\
    \ Currently, only point estimates are provided, making it impossible to assess\
    \ the statistical significance of the reported differences between mediators (e.g.,\
    \ the 1.1\u20132.5 point gap between proprietary and open-source models)."
- id: 2ca657700869
  severity: science
  text: Clarify the statistical test used to validate the 'doubling' claim for the
    evaluator's Pearson correlation (r=0.82 vs r=0.37). A simple comparison of correlation
    coefficients is insufficient; a Fisher's z-transformation or a permutation test
    is required to demonstrate that the improvement is statistically significant and
    not due to sampling variance.
- id: aff4b5313c9c
  severity: science
  text: "Address the multiple comparisons problem in the socio-cognitive probing analysis.\
    \ With 15 conditions and 8 mediators, numerous pairwise comparisons are made.\
    \ The paper reports specific drops (e.g., '18.9\u201364.1') without indicating\
    \ if these were corrected for family-wise error rate (e.g., Bonferroni) or false\
    \ discovery rate (FDR)."
- id: 7cc6f515b81c
  severity: science
  text: "The stability analysis reports Kendall's W = 0.929 for rankings across three\
    \ runs. However, the raw variance (half-range) for Consensus Gain in Table 5 is\
    \ substantial for some models (e.g., Nemotron-3-120B: \xB16.8). Provide a formal\
    \ test (e.g., ANOVA or mixed-effects model) to determine if the observed performance\
    \ differences between mediators are robust against this run-to-run variance."
artifact_hash: 85696f027c2296857479727071f7c34ef0cc40db782dc072c038e2773b79f464
artifact_path: projects/PROJ-680-socrates-towards-reliable-automated-eval/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T17:20:12.721327Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in the SoCRATES paper is generally well-structured in its design, particularly the independent variation of socio-cognitive axes to isolate failure modes. However, the reporting of results lacks the necessary statistical rigor to fully support the quantitative claims made.

First, the primary benchmark results presented in Table 1 (Performance by Conflict Domain) and Table 3 (Stability Analysis) rely exclusively on point estimates (means or medians). While the authors mention running simulations multiple times (e.g., "three independent runs" in Appendix E004), the main results tables do not display confidence intervals, standard errors, or standard deviations. Without these measures of dispersion, it is impossible to determine if the reported differences between mediators (e.g., the 1.1–2.5 point advantage of proprietary models) are statistically significant or merely artifacts of stochastic variance. The large half-range reported for Nemotron-3-120B (±6.8) in Table 5 suggests that some performance gaps might not be robust.

Second, the claim that the topic-localized evaluator "more than doubles" the performance of baselines (Section 3.2, Table 2) is based on a comparison of Pearson correlation coefficients ($r=0.823$ vs $r=0.372$). The paper does not state whether a statistical test (such as Fisher's z-transformation) was performed to confirm that this difference is significant. Given the sample size ($N=1,844$ snippets), the difference is likely significant, but the absence of a p-value or confidence interval for the difference in correlations weakens the claim.

Third, the analysis of socio-cognitive axes involves multiple comparisons across 15 conditions and 8 mediators. The text highlights specific performance drops (e.g., "18.9–64.1" for Competing posture) but does not mention any correction for multiple testing (e.g., Bonferroni or Benjamini-Hochberg). Without such corrections, the risk of Type I errors (false positives) in identifying specific failure modes is elevated.

Finally, while the authors report Kendall's W = 0.929 to demonstrate ranking stability across runs, this metric only assesses rank agreement, not the magnitude of score variance. A more robust statistical approach would involve a mixed-effects model or ANOVA to partition the variance attributable to the mediator, the condition, and the random run effect, thereby providing a formal test of the mediator's main effect.

To improve the paper, the authors should supplement the point estimates with confidence intervals, perform and report significance tests for the correlation improvements and performance gaps, and address the multiple comparisons issue in the socio-cognitive analysis.
