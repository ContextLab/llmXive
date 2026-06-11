---
action_items:
- id: 591006ab0b4d
  severity: science
  text: Compute 95% confidence intervals for all metrics in Table 2 (SAA, Recall,
    etc.) using bootstrap or analytical methods given N=1897. Perform pairwise significance
    testing (e.g., bootstrap t-test) for top model comparisons to substantiate 'best'
    claims.
- id: aa5450bd8869
  severity: science
  text: Address multiple-comparisons handling when highlighting 'best' and 'second-best'
    across 20 models. Explicitly state if corrections (e.g., Bonferroni, FDR) were
    applied to avoid false positives in ranking.
artifact_hash: 343bba3cbfbb16bee3f79c8a33c3a51555292623f2cdbd016ca7ae51e6fbc39c
artifact_path: projects/PROJ-601-https-arxiv-org-abs-2605-12882/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-11T04:46:25.754880Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

This re-review confirms that the statistical rigor requirements identified in the prior review remain unaddressed. While the manuscript provides a comprehensive benchmark and detailed results, the statistical claims regarding model superiority lack the necessary inferential support.

First, **Table 2** (`tab:main_results`, lines 430–480) reports point estimates for SAA, Recall, Relevance, and Answer Correctness (e.g., Gemini-3.1-Pro SAA=76.0, Gemini-3-Flash SAA=65.4) without associated uncertainty metrics. Given the sample size of N=1,897, it is feasible to compute 95% confidence intervals via bootstrapping. The absence of these intervals prevents readers from assessing whether the observed differences between top-tier models are statistically significant or potentially due to sampling variance. The current presentation implies a precision that is not statistically justified.

Second, the paper highlights the "best" and "second-best" models across 20 candidates and multiple metrics without addressing **multiple-comparisons error**. Selecting top performers from 20 models involves 190 pairwise comparisons per metric. Without corrections such as Bonferroni or False Discovery Rate (FDR) adjustments, the highlighted rankings risk inflated Type I error rates. The text does not mention any correction method, leaving the "best" claims vulnerable to statistical overfitting on the test set.

Third, while **Appendix: Analysis of Different Judges** (lines 850–880) validates the consistency of the LLM judge against human experts using a Friedman test, this validates the *scoring mechanism*, not the *model performance metrics*. The judge validation p-values (0.14–0.53) do not substitute for confidence intervals on the primary SAA and Recall scores reported in the main results.

To substantiate the "Attribution Hallucination" phenomenon and the performance hierarchy, the authors must provide confidence intervals for the key metrics and clarify the statistical significance of the reported rankings. Until these analyses are performed and reported, the quantitative claims regarding model superiority remain descriptive rather than inferential.
