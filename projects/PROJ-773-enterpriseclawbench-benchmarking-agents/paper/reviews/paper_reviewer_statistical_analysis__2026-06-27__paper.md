---
action_items:
- id: 0ca69eb9c427
  severity: science
  text: Report confidence intervals or standard errors for all leaderboard scores
    (Figure 1, Table 1) to quantify uncertainty.
- id: 859ec6c4b9c4
  severity: science
  text: Address multiple comparisons correction for the 32 harness-model combinations
    tested.
- id: 5e2f929f9cde
  severity: science
  text: Provide variance estimates (SE/CI) for skill transfer deltas; n=5 held-out
    tasks is insufficient for robust claims without uncertainty metrics.
- id: baae7c317632
  severity: science
  text: Include significance testing or CIs for judge reliability correlations (Table
    2).
artifact_hash: 436f60fbb896e41d063ceb9811d2249a06e1b5eaa235430cfaccb20cf6596607
artifact_path: projects/PROJ-773-enterpriseclawbench-benchmarking-agents/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-27T00:55:35.161580Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: full_revision
---

The paper lacks rigorous statistical validation for its core claims, which undermines the reliability of the benchmark rankings. The main leaderboard (Figure 1) reports point estimates for 32 harness-model combinations without confidence intervals or standard errors. This omission makes it impossible to assess whether observed score differences (e.g., 0.663 vs 0.62) are statistically significant or due to random variance. With 32 comparisons, multiple testing correction (e.g., Bonferroni or FDR) is required to control the family-wise error rate, yet none is mentioned in the "Evaluation Setting" section (lines 230-250).

The skill evaluation section (lines 350-380) relies on only 5 held-out tasks per consumer to support claims about skill transfer. Reporting mean deltas (e.g., +0.0681 for GPT-5.5) without variance estimates, standard errors, or p-values renders the conclusion that "skill quality depends strongly on the creator model" statistically unsupported. A sample size of 5 is insufficient for stable inference; bootstrapping or Bayesian credible intervals should be used to quantify uncertainty.

Judge reliability (Table 2) reports Spearman correlations (0.790 text, -0.259 visual) but omits confidence intervals or significance tests. Given the visual route's negative correlation, a formal test is needed to confirm if this differs significantly from zero. Additionally, the score distribution (bounded 0-1) may violate normality assumptions for standard parametric tests; non-parametric alternatives should be justified.

Finally, the construction funnel (Figure 2) shows a reduction from 5,291 to 852 tasks. Statistical analysis of selection bias (e.g., comparing properties of rejected vs. accepted tasks) is missing. Without these statistical safeguards, the benchmark's reliability and the validity of model rankings remain uncertain. The authors must provide uncertainty quantification for all reported metrics to support their conclusions.
