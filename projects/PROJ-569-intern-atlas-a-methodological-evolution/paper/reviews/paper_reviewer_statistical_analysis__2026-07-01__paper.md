---
action_items:
- id: da9c8aa0cb43
  severity: science
  text: 'The statistical analysis presented in the paper is insufficient to support
    the strong claims made regarding the performance of Intern-Atlas. While the system
    architecture is sophisticated, the empirical validation lacks rigorous statistical
    grounding. First, the results in Table 1 (Section 4.1) regarding the SGT-MCTS
    algorithm are highly suspicious. The reported Node Recall (NR) and Chain Alignment
    Score (CAS) are identical to one decimal place for every method (e.g., Beam@10:
    44.9 for both). Si'
artifact_hash: 8cf472ae2a887b5d12e0bb466a1ee80bacbf411e923611b73e3a5325c617cf94
artifact_path: projects/PROJ-569-intern-atlas-a-methodological-evolution/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T20:12:11.303883Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: full_revision
---

The statistical analysis presented in the paper is insufficient to support the strong claims made regarding the performance of Intern-Atlas. While the system architecture is sophisticated, the empirical validation lacks rigorous statistical grounding.

First, the results in Table 1 (Section 4.1) regarding the SGT-MCTS algorithm are highly suspicious. The reported Node Recall (NR) and Chain Alignment Score (CAS) are identical to one decimal place for every method (e.g., Beam@10: 44.9 for both). Since NR measures the fraction of nodes recovered and CAS measures the preservation of ordering, these metrics should theoretically diverge, especially for baselines like Random Walk which recover nodes but likely fail on ordering. This identity suggests a potential calculation error or a copy-paste mistake in the manuscript, rendering the claimed 39.9-point improvement over Beam@10 unverified.

Second, the human evaluation studies (Sections 4.2 and 4.3) rely on point estimates (means and correlations) without any measure of uncertainty. For the idea evaluation alignment (N=100), the paper reports Spearman correlations of 0.81 vs. 0.58 but provides no confidence intervals or p-values to test if the difference is statistically significant. Similarly, the idea generation scores in Table 3 are presented as means without standard deviations. Without error bars or significance testing (e.g., paired t-tests or Wilcoxon signed-rank tests), it is impossible to determine if the observed improvements are robust or artifacts of sampling noise.

Finally, the analysis of the 'Strata Dataset' (Table 2) asserts a monotonic trend across publication tiers but does not provide a statistical test for trend (such as the Jonckheere-Terpstra test) or an ANOVA to confirm that the variance between groups is significantly larger than the variance within groups. The lack of these standard statistical controls makes the conclusions about the system's ability to stratify quality premature. The authors must re-run the analyses to include confidence intervals, p-values, and effect sizes, and correct the apparent data reporting error in Table 1.
