---
action_items:
- id: 73cd60f88223
  severity: writing
  text: "Section 4.1 and Table 1 report aggregate metrics (e.g., '9.9M tokens', '231\
    \ episodes') to two decimal places or as exact integers without reporting variance\
    \ (SD/SE) or the number of seeds/runs. Given the stochastic nature of LLM agents,\
    \ these point estimates imply false precision. Report mean \xB1 SD across the\
    \ reported runs or explicitly state if these are single-run results."
- id: c0d56d5afbb1
  severity: writing
  text: Section 4.2 claims GPT-5.5 is 'the strongest reported model' based on a single
    pass rate (15.2%) without reporting confidence intervals or variance across seeds.
    To support a ranking claim, report the standard deviation of pass rates across
    multiple seeds (e.g., 5 seeds) or provide a confidence interval for the pass rate
    estimate.
- id: 51dd828ea614
  severity: writing
  text: "Section 4.3 reports a Spearman correlation (\u03C1 = 0.56) between pass rate\
    \ and mean reward but omits the p-value or confidence interval for this correlation.\
    \ With N=15 models, the statistical significance of this correlation is not guaranteed;\
    \ report the p-value to validate the claim of a 'moderate' relationship."
artifact_hash: cc7c0e6ae7734f70b56231d9c1d0f0ceba3e329a735b96205779c45c3e7a7439
artifact_path: projects/PROJ-1049-long-horizon-terminal-bench-testing-the/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-14T03:06:41.990723Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical reporting in this benchmark paper is generally descriptive but lacks the necessary uncertainty quantification to support comparative claims. While the paper correctly identifies the limitations of binary grading, the presentation of the new dense-reward metrics suffers from "false precision" and missing variance estimates.

Specifically, in Section 4.1 (Main Results) and Table 1, aggregate statistics such as "9.9M tokens per task" and "231 episodes" are reported as exact point estimates. In the context of LLM agent evaluation, where performance is highly stochastic, reporting a single number without a standard deviation (SD), standard error (SE), or range across multiple seeds (runs) is misleading. It implies a level of stability that is rarely present in these systems. The authors should either report these as mean ± SD (e.g., "9.9M ± 1.2M tokens") or explicitly state that these figures represent a single run, adjusting the text to avoid implying these are fixed properties of the models.

Furthermore, the claim that GPT-5.5 is the "strongest" model based on a 15.2% pass rate (Section 4.2) lacks statistical backing. Without reporting the variance across seeds or a confidence interval for the pass rate, it is impossible to determine if this lead over the next best model (6.5%) is statistically significant or within the margin of error of the evaluation process. Standard practice in this field requires reporting performance over at least 3-5 seeds to establish stability.

Finally, in Section 4.3, the authors report a Spearman correlation coefficient of ρ = 0.56 between pass rate and mean reward. However, no p-value or confidence interval is provided. With a sample size of only 15 models, a correlation of 0.56 is not automatically significant (p ≈ 0.05 is the threshold). The authors must report the p-value to validate the assertion that these metrics are "positively but only moderately correlated." Without this, the statistical inference is incomplete.
