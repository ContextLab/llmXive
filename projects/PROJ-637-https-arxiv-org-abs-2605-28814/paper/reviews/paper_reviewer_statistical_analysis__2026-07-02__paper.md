---
action_items:
- id: 5f92a4a3465c
  severity: science
  text: Report standard errors or confidence intervals for all accuracy metrics in
    Table 1 (MuSiQue) and Table 2 (Open Problem Solving). Single-run point estimates
    (e.g., 7.0%, 10.4%) are insufficient to claim statistical significance over baselines
    like Tree-GRPO.
- id: 0fd67e6679ac
  severity: science
  text: Clarify the statistical unit of analysis for the evolutionary search results.
    Are the reported 'Avg' and 'Best' values in Table 2 aggregated over multiple independent
    seeds, or are they from a single long run? If single runs, variance estimates
    are missing.
- id: c2ff7dd5eb22
  severity: science
  text: The cost analysis in Table 3 compares wall-clock times (64s vs 309s) without
    normalizing for the number of function evaluations or tokens generated. A statistical
    comparison of efficiency (accuracy per unit cost) is required to support the claim
    of 'modest additional overhead'.
- id: 5c102a6a44a2
  severity: science
  text: The ablation study (Figure 3) lacks statistical validation. The claim that
    removing components 'reduces performance' needs to be backed by significance tests
    (e.g., paired t-tests or bootstrap CIs) rather than visual inspection of smoothed
    curves.
artifact_hash: d74e7ce3cbfe7aea4f0dad766af5b0e41093c35f05a067517ae8e48026ef85b2
artifact_path: projects/PROJ-637-https-arxiv-org-abs-2605-28814/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T16:56:53.453327Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: full_revision
---

The manuscript presents a novel search framework but lacks the statistical rigor required to validate its empirical claims. The primary concern is the absence of uncertainty quantification. In Table 1 (MuSiQue), accuracy improvements are reported as single point estimates (e.g., +3.0% over Tree-GRPO) without standard errors, confidence intervals, or p-values. Given the stochastic nature of LLM generation and evolutionary search, it is impossible to determine if these gains are statistically significant or due to random variance.

Similarly, Table 2 reports "Avg" and "Best" scores for open problem solving but does not specify the number of independent seeds used to compute these averages. The standard deviations provided (e.g., $\pm$ .014) appear to be calculated from a single run's internal variance or a very small sample size, which is insufficient for robust comparison. The claim that \ours\ has "lower variance" than baselines cannot be substantiated without reporting the variance of the mean across multiple independent experimental seeds.

Furthermore, the cost analysis in Table 3 compares raw wall-clock times. A proper statistical analysis should normalize these costs by the number of valid search actions or tokens generated to establish a statistically significant difference in efficiency. The ablation study (Figure 3) relies on visual inspection of EMA-smoothed curves; without statistical testing (e.g., bootstrapping the final performance metrics), the necessity of specific components remains an unproven assertion. The authors must re-run experiments with multiple seeds (n $\ge$ 5) and report mean $\pm$ standard error, along with appropriate significance tests, to support their conclusions.
