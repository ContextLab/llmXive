---
action_items:
- id: 0aa27af39b80
  severity: writing
  text: "Table 1 (MetaWorld) and Table 2 (LIBERO) report single-point success rates\
    \ (e.g., 64.35%) without any measure of uncertainty (SD, SE, or CI) or mention\
    \ of the number of random seeds used. In RL/robotics, performance variance across\
    \ seeds is high; reporting a single mean without spread implies false precision.\
    \ Report mean \xB1 SD over at least 3-5 seeds for all main results."
- id: 9cb107b184e5
  severity: writing
  text: "Table 3 (Real-World) reports '73.3 \xB1 6.5' as the average success rate\
    \ across 9 tasks, calculating the standard deviation of the *task means* rather\
    \ than the standard deviation of the *trials* or the standard error of the mean.\
    \ This conflates task difficulty variance with method stability. Report the standard\
    \ deviation of the 20 trials per task, or the standard error of the mean across\
    \ tasks, to correctly reflect the precision of the reported average."
- id: b50be2843ef6
  severity: writing
  text: Section 5.2 (Mechanism Analysis) claims OGG improves recovery with an 'average
    gain of 0.23' (Fig 5) but provides no statistical test (e.g., paired t-test or
    bootstrap) or confidence interval to support this magnitude. Given the binary
    nature of success/failure, report the 95% confidence interval for the difference
    in recovery rates or the p-value from a McNemar's test on the paired outcomes.
artifact_hash: d7358417426c747fa4ca8d918e3157dfcd577dc0f92cbf50c88254f4dca67f3f
artifact_path: projects/PROJ-994-vla-corrector-lightweight-detect-and-cor/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-07T03:35:54.330566Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical reporting in this paper is generally descriptive but lacks the necessary uncertainty quantification required to validate the magnitude of the reported improvements.

First, the main simulation results in **Table 1** (MetaWorld) and **Table 2** (LIBERO) present success rates as precise point estimates (e.g., "64.35%") without any accompanying measure of variance (standard deviation, standard error) or indication of the number of random seeds used. In reinforcement learning and robotics, performance is inherently stochastic due to initialization, environment dynamics, and policy sampling. Reporting a single number without a spread (e.g., mean ± SD over 5 seeds) creates an illusion of false precision and prevents readers from assessing the stability of the method. The authors should aggregate results over multiple seeds and report the mean and standard deviation for all primary comparisons.

Second, the real-world results in **Table 3** (Appendix) and the main text calculate the "Group Avg" and "Overall Avg" by taking the mean of the task-level success rates and then reporting the standard deviation of those *task means* (e.g., "73.3 ± 6.5"). This is a statistical misinterpretation for the purpose of claiming method performance. The standard deviation of task means reflects the *difficulty variance* of the benchmark tasks, not the *reliability* of the VLA-Corrector method. To correctly report the precision of the average success rate, the authors should either report the standard deviation of the 20 trials within each task (aggregated appropriately) or, more standardly, report the standard error of the mean (SEM) across the 9 tasks to indicate how precisely the 73.3% figure estimates the true population performance.

Finally, the claim in **Section 5.2** that OGG yields an "average gain of 0.23" in recovery rates (referencing Figure 5) is presented without statistical backing. While the visual trend is clear, a quantitative claim of "0.23" implies a specific effect size that should be accompanied by a confidence interval or a p-value from a paired test (e.g., McNemar's test for paired binary outcomes) to confirm the gain is not due to random fluctuation.

These are reporting gaps that can be fixed by re-aggregating existing data or adding standard error bars, rather than requiring new experiments, provided the raw per-seed or per-trial data exists.
