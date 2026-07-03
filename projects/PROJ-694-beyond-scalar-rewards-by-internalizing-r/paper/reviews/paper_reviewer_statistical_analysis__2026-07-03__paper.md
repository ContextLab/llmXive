---
action_items:
- id: 211f684de49d
  severity: science
  text: The annotation workflow (Sec 3) states that ground-truth distributions are
    computed by dropping the highest and lowest scores. However, the statistical validity
    of this outlier removal is not justified with a sensitivity analysis or a test
    for normality. If the underlying distribution of human scores is bimodal or skewed,
    trimming extremes may bias the mean and variance estimates used for training.
    Please report the number of annotators per sample and justify the trimming rule
    statistically.
- id: 48a2921983d0
  severity: writing
  text: In Table 1, the 9B RewardDance row lists an SRCC of '6175' (likely a typo
    for 0.6175). While likely a formatting error, such precision issues in statistical
    reporting undermine confidence in the reported metrics. Please verify all decimal
    placements and ensure consistent significant figures across all tables.
- id: 4e00bd947098
  severity: science
  text: The human evaluation in Sec 6.3 reports a net GSB improvement of 41.3% based
    on 400 prompts. The paper does not provide a confidence interval (e.g., Wilson
    score interval) or a p-value for this difference against the SFT baseline. Given
    the binary nature of the 'Good' vs 'Bad' comparison, a statistical significance
    test (e.g., McNemar's test or a binomial test) is required to confirm the improvement
    is not due to chance.
- id: 4294b36d7875
  severity: science
  text: The ablation study in Fig 4 compares 'Parsing Text' vs 'Distribution Expectation'.
    The text claims the latter provides 'denser supervision,' but the statistical
    significance of the observed gains in HPA and Margin HPA is not quantified. Please
    include error bars (e.g., standard error over 3 random seeds) or report p-values
    to ensure the improvements are robust and not artifacts of random initialization.
artifact_hash: ea1d74fbe2af288d803689e081136bb19c2463edb4534b816711d1532122572b
artifact_path: projects/PROJ-694-beyond-scalar-rewards-by-internalizing-r/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T19:14:28.626404Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in the paper is generally sound in its conceptual approach, particularly the shift from scalar rewards to score distributions to capture human uncertainty. However, several specific statistical reporting and validation gaps need to be addressed to ensure the robustness of the claims.

First, regarding the annotation process described in Section 3, the authors state that the ground-truth score distribution is computed by "dropping the highest and lowest scores before aggregation." While this is a common heuristic to reduce outlier noise, the paper lacks a statistical justification for this specific trimming rule. Without reporting the number of annotators per sample or conducting a sensitivity analysis (e.g., comparing trimmed vs. untrimmed means/variances), it is unclear if this procedure introduces bias, especially if the human preference distribution is not symmetric. The authors should clarify the sample size per item and justify the trimming threshold statistically.

Second, the human evaluation results in Section 6.3 report a "net GSB improvement of 41.3%." This is a point estimate derived from 400 prompts. The manuscript fails to provide a confidence interval (e.g., 95% CI) or a p-value to assess the statistical significance of this improvement over the SFT baseline. Given the binary nature of the pairwise comparison (Good vs. Bad), a simple binomial test or McNemar's test should be performed to confirm that the observed gain is statistically significant and not a result of random variation.

Third, the ablation study in Figure 4 (and the accompanying text) claims that using the distribution expectation yields "consistently" better results than parsing text. However, the figures do not display error bars, and the text does not mention whether the experiments were repeated with multiple random seeds. To support the claim of "consistent" improvement, the authors must report the standard error or standard deviation across seeds and, ideally, the p-values of the differences. Without this, the observed gains could be attributed to variance in the training process rather than the method itself.

Finally, a minor but notable typo exists in Table 1 (9B RewardDance row), where the SRCC is listed as "6175" instead of "0.6175". While likely a formatting error, such inaccuracies in statistical reporting can erode trust in the precision of the results. All numerical values should be double-checked for decimal placement and consistent significant figures.

Addressing these points—specifically the statistical validation of the human evaluation and the robustness of the ablation results—will significantly strengthen the empirical claims of the paper.
