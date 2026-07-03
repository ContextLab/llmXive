---
action_items:
- id: b35df25d9343
  severity: writing
  text: 'The manuscript presents compelling empirical results for the \textsc{RATs}
    framework, but the statistical rigor of the analysis requires strengthening to
    support the quantitative claims. First, the primary results tables (Table 1: LIBERO-PRO,
    Table 2: MolmoSpaces, Table 3: RoboSuite/Real-World) report success rates as single-point
    percentages (e.g., 43.8%, 38.0%). In experimental robotics and machine learning,
    reporting point estimates without measures of uncertainty (standard deviation,
    standar'
artifact_hash: 50abfa42bd37b77889e3563a6ea1bdb0e8be3fa0ecf45caffb5d23cfc888d2a4
artifact_path: projects/PROJ-749-playful-agentic-robot-learning/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T18:59:07.247181Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents compelling empirical results for the \textsc{RATs} framework, but the statistical rigor of the analysis requires strengthening to support the quantitative claims.

First, the primary results tables (Table 1: LIBERO-PRO, Table 2: MolmoSpaces, Table 3: RoboSuite/Real-World) report success rates as single-point percentages (e.g., 43.8%, 38.0%). In experimental robotics and machine learning, reporting point estimates without measures of uncertainty (standard deviation, standard error, or 95% confidence intervals) is insufficient. Given the stochastic nature of LLM-based agents and simulation environments, the variance across trials is critical. For instance, in Table 1, the improvement from 23.2% to 43.8% is substantial, but without error bars or confidence intervals, it is impossible to determine if this difference is statistically significant or if the observed gains could be attributed to random fluctuation in the specific random seeds used.

Second, the manuscript claims significant improvements across multiple sub-categories (Object, Goal, Spatial in LIBERO-PRO; Open, Close, Pick, PnP in MolmoSpaces) without addressing the issue of multiple comparisons. When testing multiple hypotheses (e.g., 6 sub-splits in LIBERO-PRO), the family-wise error rate increases. The authors should explicitly state whether they applied corrections (such as Bonferroni or Holm-Bonferroni) to the p-values or if they treated each sub-task as an independent experiment. If no correction was applied, the discussion should acknowledge the increased risk of Type I errors.

Third, the statistical methodology for the "compute-matched" comparison in Appendix Table \ref{tab:compute_matched_comparison} needs clarification. The comparison between a 10-turn baseline and a 15-turn baseline involves different computational budgets. While the authors attempt to match token costs, the statistical validity of comparing these distributions requires a clear statement on the test used (e.g., Mann-Whitney U test for non-normal distributions, or paired t-test if assumptions are met). The text mentions "modest gains" but does not provide a p-value or effect size (e.g., Cohen's d) to quantify the magnitude of the difference between the 23.2% and 26.0% results.

Finally, the definition of the experimental unit in Section \ref{subsec:exp-details} and Appendix \ref{sec:appendix_evaluation_benchmarks} states "ten initial-state trials per task." It is crucial to clarify if these 10 trials are independent runs with different random seeds or 10 runs with a fixed seed but different initial states. If the latter, the degrees of freedom for any statistical test must reflect the number of unique initial states, not the total number of rollouts, to avoid pseudoreplication. The current text implies 600 total rollouts for LIBERO-PRO, but the statistical power depends on the independence of these samples.

To improve the paper, the authors should re-run the analysis to include 95% confidence intervals (via bootstrapping or standard error propagation) for all mean success rates in the main tables. Additionally, a brief "Statistical Analysis" subsection should be added to the Experimental Results section detailing the specific tests used, the handling of multiple comparisons, and the justification for the chosen significance threshold.
