---
action_items:
- id: f48c5e306de6
  severity: science
  text: 'Section 4.2 (Human Evaluation): The paper reports Spearman correlations (0.81
    vs 0.58) but omits confidence intervals or significance tests (e.g., Fisher''s
    r-to-z transformation) to determine if the difference between Intern-Atlas and
    the LLM baseline is statistically significant. Add 95% CIs and p-values for the
    correlation differences.'
- id: 0c1b916e0bce
  severity: science
  text: 'Section 4.3 (Idea Generation): Table 3 reports mean scores and win rates
    (e.g., 88.0%) without reporting standard deviations, standard errors, or results
    of statistical tests (e.g., paired t-tests or Wilcoxon signed-rank tests) to validate
    that the observed improvements over baselines are not due to random variation.'
- id: eb31f286d135
  severity: science
  text: 'Section 4.1 (Lineage Reconstruction): Table 1 presents point estimates for
    NR, ER, and CAS. Given the stochastic nature of MCTS and the baselines, the authors
    must report the variance (e.g., standard deviation over multiple runs) and statistical
    significance of the improvements to ensure the results are robust.'
artifact_hash: 8cf472ae2a887b5d12e0bb466a1ee80bacbf411e923611b73e3a5325c617cf94
artifact_path: projects/PROJ-569-intern-atlas-a-methodological-evolution/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:31:26.214851Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis presented in the manuscript is currently insufficient to support the strong claims of superiority for the Intern-Atlas system. While the scale of the dataset (1M+ papers) is impressive, the evaluation of the downstream operators (lineage reconstruction, idea evaluation, and idea generation) relies heavily on point estimates without measures of uncertainty or statistical significance testing.

In Section 4.2, the authors claim that Intern-Atlas is "more closely correlated with expert ratings" than the pure LLM baseline, citing Spearman correlations of 0.81 versus 0.58. However, the manuscript fails to provide confidence intervals for these correlations or a statistical test (such as Fisher's r-to-z transformation) to confirm that the difference is statistically significant. Without this, the claim of superior alignment remains anecdotal. Similarly, in Section 4.3, the reported win rates (e.g., 88.0% against No-KB) and mean scores in Table 3 lack standard deviations or standard errors. Given that the evaluation involves human experts and LLM judges, which introduce inherent variance, the absence of error bars or significance tests (e.g., paired t-tests or Wilcoxon signed-rank tests) makes it impossible to assess the robustness of the reported gains.

Furthermore, in Section 4.1, the performance of the SGT-MCTS algorithm is compared against baselines using Node Recall, Edge Recall, and Chain Alignment Score. Table 1 presents single point values. Since MCTS and random walk baselines are stochastic algorithms, the results should be averaged over multiple independent runs with reported standard deviations. The current presentation does not allow the reader to determine if the observed improvements are consistent or potentially artifacts of a specific random seed.

To meet the standards of rigorous statistical analysis, the authors must: (1) report 95% confidence intervals for all correlation coefficients and mean scores; (2) perform and report the results of appropriate statistical significance tests for all comparative claims; and (3) include measures of variance (standard deviation or standard error) for all algorithmic performance metrics derived from stochastic processes.
