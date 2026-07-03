---
action_items:
- id: 8c76cf55dd77
  severity: science
  text: Table 1 and Table 2 mark improvements with '*' for p<0.05, but the manuscript
    lacks a 'Statistical Significance' subsection detailing the test used (e.g., paired
    t-test, Wilcoxon), the number of random seeds (n), and the correction method for
    multiple comparisons across 3 datasets and 4 metrics. Without this, the significance
    claims are unverifiable.
- id: 6b7985ee52ad
  severity: science
  text: The 'Advantage Variance' metric in Table 3 is reported as a relative multiplier
    (e.g., 0.06x) without defining the baseline denominator or providing the absolute
    variance values. To validate the claim of reduced variance, report the mean and
    standard deviation of the advantage estimates over the same number of seeds used
    for performance metrics.
- id: ccff8220b214
  severity: science
  text: The ablation study in Table 4 (w/o SRC) shows a massive drop in IoI/IoR but
    a spike in CTR. The statistical significance of this trade-off is not addressed.
    Are these differences significant? A formal test comparing the full model against
    ablated variants is required to support the conclusion that SRC is 'essential'
    rather than just 'influential'.
artifact_hash: 59e5ed22cd4a5270f33af7ca1a0149493d75bf5066fd8fe56191e1e437bc5c6a
artifact_path: projects/PROJ-640-https-arxiv-org-abs-2605-28293/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T11:01:46.997263Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript proposes ProRL to address length bias and high variance in policy gradients for proactive recommendation. While the theoretical motivation is sound, the statistical reporting in the experimental section is insufficient to rigorously support the claims of superiority and stability.

First, the manuscript frequently marks results with an asterisk (*) to denote statistical significance ($p < 0.05$) in Tables 1, 2, and the cross-evaluator tables. However, the "Experimental Setup" and "Results" sections do not specify the statistical test employed (e.g., paired t-test, Wilcoxon signed-rank test), the number of independent runs (random seeds) used to generate the mean and standard deviation, or the method for handling multiple comparisons. Given that results are reported across three datasets and four metrics, a correction for multiple testing (e.g., Bonferroni or Holm-Bonferroni) is necessary to avoid inflating Type I errors. Without this information, the claim of "statistically significant" improvement is not reproducible.

Second, Table 3 presents "Advantage Variance" as a relative multiplier (e.g., $0.06\times$) compared to a baseline. The absolute values of the variance, along with the standard error of these variance estimates, are missing. To substantiate the claim that Position-Specific Advantage Estimation (PSAE) reduces variance, the authors should report the mean and standard deviation of the advantage estimates across seeds. Furthermore, the baseline for the multiplier (likely the REINFORCE estimator) should be explicitly defined in the table caption or text.

Third, the ablation study in Table 4 demonstrates that removing Stepwise Reward Centering (SRC) leads to a collapse in IoI/IoR but an increase in CTR. While the trend is clear, the statistical significance of these specific trade-offs is not tested. The authors should perform pairwise statistical tests between the full ProRL model and the "w/o SRC" variant to confirm that the observed differences in IoI/IoR are not due to random fluctuation, especially given the high variance often seen in RL training.

Finally, the "Stability Under Varying Intervention Intensities" section (Appendix) makes qualitative claims about minimal fluctuation. Quantitative support, such as the standard deviation of performance metrics across different intervention ratios, would strengthen these assertions. The current reliance on visual inspection of figures (which are not fully visible in the text source) and qualitative descriptions is insufficient for a rigorous statistical review.
