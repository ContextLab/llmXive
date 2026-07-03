---
action_items:
- id: 404f3d3f35f1
  severity: science
  text: Report confidence intervals or standard errors for all primary metrics (AbsRec@K,
    SPL) in Tables 1 and 2. The current point estimates (e.g., 57.4% timely recall)
    lack measures of variance, making it impossible to assess the statistical significance
    of the reported improvements or the stability of the results across the 101 held-out
    examples.
- id: e13a9ff70c15
  severity: science
  text: Clarify the statistical test used to compare models (e.g., Llama-3.3-70B vs.
    Qwen3-235B) and scaffolds. The paper claims significant differences (e.g., scaffold
    effects) but does not specify if paired tests (e.g., McNemar's or Wilcoxon signed-rank)
    were applied to the episode-level outcomes, nor does it report p-values.
- id: 75649095e758
  severity: science
  text: Address the multiple-comparisons problem. With 13 models, 2 scaffolds, 3 environments,
    and 5+ abstention categories, the number of pairwise comparisons is large. The
    paper does not mention any correction method (e.g., Bonferroni, Holm-Bonferroni,
    or FDR) to control for Type I errors when interpreting the 'best' performing models.
- id: cd2b086ec52d
  severity: writing
  text: Provide the exact sample size (N) for each specific sub-category analysis
    (e.g., 'Missing Target' in WebShop). While total counts are given (e.g., 251 tasks),
    the breakdown of solvable vs. unsolvable per specific sub-category in the results
    section is sometimes ambiguous, which affects the denominator for recall calculations.
artifact_hash: 38d0e8e4fb458c680aadb1d4bcdffd2c4f641f3bec33db525a174585bed1f06b
artifact_path: projects/PROJ-808-agentic-abstention-do-agents-know-when-t/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T01:30:19.752777Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in this paper is comprehensive in scope but lacks necessary rigor in reporting uncertainty and significance testing. While the definitions of metrics like AbsRec@K and SPL are mathematically sound (Appendix C), the presentation of results relies almost exclusively on point estimates without measures of variance.

Specifically, in Table 1 (WebShop results) and Table 2 (AbstentionBench/TerminalBench), the authors report precise percentages (e.g., 57.4%, 68.9%) derived from a held-out set of 101 examples. For a sample size of N=101, the standard error for a proportion near 0.5 is approximately 5%. Without reporting confidence intervals (e.g., 95% CI) or standard deviations, it is impossible to determine if the observed differences between models (e.g., the jump from 26.7% to 57.4% with \method) are statistically significant or if the "best" model is merely a result of random variance in the test set.

Furthermore, the paper makes strong comparative claims (e.g., "Codex CLI consistently achieves higher abstention recall than Terminus 2") without citing the results of statistical hypothesis tests. Given the binary nature of the outcome (abstain vs. not abstain) at the episode level, appropriate tests such as McNemar's test for paired comparisons or a generalized linear mixed model (GLMM) with random effects for the task instance should be employed. The absence of p-values or effect sizes with confidence bounds weakens the empirical support for the conclusion that specific scaffolds or model scales are definitively superior.

Finally, the study involves a large number of comparisons across 13 models, multiple environments, and various abstention categories. The manuscript does not address the multiple-comparisons problem. Without a correction method (e.g., False Discovery Rate control), the risk of false positives in identifying "hardest" categories or "best" models is non-negligible. The authors should either apply a correction and report adjusted p-values or explicitly frame their findings as exploratory rather than confirmatory.
