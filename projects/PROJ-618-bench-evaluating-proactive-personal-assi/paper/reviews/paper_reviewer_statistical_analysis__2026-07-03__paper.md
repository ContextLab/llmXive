---
action_items:
- id: b9a9d84d5afe
  severity: science
  text: The paper reports standard deviations for aggregate scores (e.g., Table 1)
    but does not specify the statistical test used to determine significance between
    model rankings. Given the small sample size (N=100 tasks, 3 runs), authors must
    clarify if differences are statistically significant or merely descriptive, and
    address multiple-comparisons correction if claiming superiority.
- id: d7b1e5dcf5c7
  severity: science
  text: The reliability audit (Table 2) reports disagreement rates but lacks confidence
    intervals or inter-rater reliability metrics (e.g., Cohen's Kappa). With only
    120 sampled trajectories, the precision of these estimates is unclear; please
    provide 95% CIs for the disagreement rates to support claims of 'strong agreement'.
- id: 4abef987d960
  severity: science
  text: The ablation study (Fig. 4) claims a 9.5-point drop in Proactivity but does
    not report the variance or statistical significance of this difference. Without
    error bars or a paired test (e.g., Wilcoxon signed-rank) across the dependency
    groups, the magnitude of the effect cannot be rigorously validated.
artifact_hash: b1a603c95e647ace07f81d632546efe6a0dc736020efd850e81aa8fbc6bf0d17
artifact_path: projects/PROJ-618-bench-evaluating-proactive-personal-assi/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T11:29:31.283019Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in this manuscript is generally descriptive, relying heavily on point estimates and standard deviations without rigorous hypothesis testing. While the separation of Proactivity (Proc) and Completeness (Comp) is conceptually sound, the statistical validation of the reported differences between models is insufficient for a benchmark paper making comparative claims.

First, Table 1 presents average scores with subscripts denoting standard deviations across three runs. However, the manuscript does not state whether the observed differences between models (e.g., GPT-5.4's 67.0 vs. Qwen3.6 Plus's 64.0) are statistically significant. With only 100 tasks and 3 repetitions, the effective sample size for model comparison is limited. The authors should perform appropriate statistical tests (e.g., paired t-tests or non-parametric equivalents like Wilcoxon signed-rank tests given the likely non-normal distribution of task scores) and report p-values. Furthermore, with 9 models and 2 metrics, multiple comparisons are inevitable; a correction method (e.g., Bonferroni or Benjamini-Hochberg) should be applied to avoid Type I errors when claiming one model "leads" or is "competitive."

Second, the reliability audit in Appendix E (Table 2) reports disagreement rates (e.g., 2.66% for human experts) but provides no measure of uncertainty. For a sample of 120 trajectories, the margin of error for a 2.66% rate is substantial. The authors should calculate and report 95% confidence intervals for these disagreement rates. Additionally, reporting an inter-rater reliability metric such as Cohen's Kappa or Krippendorff's Alpha would be more robust than simple disagreement percentages, as it accounts for chance agreement.

Third, the ablation study (Figure 4) claims that removing prior sessions reduces Proactivity by an average of 9.5 points. The text does not specify the variance of this difference or the statistical test used to confirm this drop is not due to random noise. Given the visual nature of the figure and the lack of error bars or significance markers, this claim remains anecdotal. A paired statistical test comparing the "with history" vs. "without history" conditions for the same tasks is required to substantiate the "markedly lowers" assertion.

Finally, the definition of Proactivity as a ratio of resolved intents assumes a uniform distribution of intent difficulty across tasks. If some tasks have significantly more hidden intents than others, the aggregate score could be biased. The authors should verify that the number of hidden intents per task is balanced across the 100 tasks or use a weighted average if the distribution is skewed.
