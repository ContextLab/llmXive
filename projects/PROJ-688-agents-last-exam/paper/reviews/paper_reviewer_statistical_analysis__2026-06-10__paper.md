---
action_items:
- id: 26a9f526d947
  severity: science
  text: Report 95% confidence intervals for all mean pass rates and scores in Table
    1, not just the subset with repeated runs.
- id: 53520924336b
  severity: science
  text: Apply multiple-comparison correction (e.g., Bonferroni) when ranking harness-model
    configurations to control Type I error.
- id: 2ec9f535acfc
  severity: science
  text: Validate public subset representativeness using multiple agent configurations,
    not just a single correlation coefficient.
artifact_hash: f7c4cdebe7449d4f51e2127cea7b868f7e8092d99e5958aa9629c6a9a2cf1332
artifact_path: projects/PROJ-688-agents-last-exam/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-10T19:28:26.874951Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript lacks rigorous statistical validation for its primary claims regarding agent performance. Table~\ref{tab:main-results} (`tables/main_results.tex`) reports mean pass rates and scores but omits confidence intervals for the majority of configurations. The caption notes that standard deviations ($\pm$ values) are estimated from three runs for only a "subset of configurations." This inconsistency prevents valid statistical comparison between the full set of agents. For instance, the difference between Codex (26.2\%) and ALE-Claw (24.2\%) is not statistically testable without variance estimates for both.

Furthermore, the paper makes broad claims about model superiority without correcting for multiple comparisons. With over 14 harness-model configurations tested, the risk of Type I errors is high, yet no adjustment (e.g., Bonferroni, False Discovery Rate) is mentioned in Section~\ref{sec:experiment}. The observed performance gaps may not be significant after correction.

In Appendix~\ref{app:fullpool} (`appendix/fullpool-evaluation.tex`), the representativeness of the public subset is validated using a Pearson correlation ($r=0.89$) derived from *one* agent configuration (Claude Code + Opus 4.7). This is insufficient to generalize representativeness to the entire benchmark, as different models may exhibit different difficulty distributions across tasks. A multi-agent validation or stratified sampling analysis is required to support the claim that the public set is representative of the full pool for all agents.

Finally, for the 6.8\% of tasks using LLM-as-judge (Appendix~\ref{app:eval-judge-stats}), the inter-rater reliability or calibration of these judges is not reported. Given the reliance on deterministic checks, the statistical uncertainty introduced by the non-deterministic subset should be quantified to ensure the aggregate scores are robust.
