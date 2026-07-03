---
action_items:
- id: 108f758164a8
  severity: science
  text: Report statistical significance (e.g., p-values, confidence intervals, or
    standard deviations) for the benchmark comparisons in Table 1. The marginal gains
    (e.g., 68.1 vs 67.9 on BrowseComp) are too small to claim superiority without
    variance estimates or significance testing across multiple runs.
- id: 6ee7064664e0
  severity: science
  text: Clarify the experimental protocol for the ablation study in Section 4.3. Specify
    if the 200-question subset was sampled randomly and if the base, tool-only, and
    full-harness models were evaluated on the exact same seed set to ensure the +10.0
    gain is not due to sampling variance.
- id: 1c35d3fea165
  severity: science
  text: The 'Generalization to Single-Agent' results (Section 4.5) lack a baseline
    comparison for the specific single-agent configuration. Clarify if the base model
    was also evaluated in a single-agent mode to isolate the effect of the fine-tuning
    versus the architectural change.
artifact_hash: 23164a835e9fc14f10b36f04bd2aeba4213e5a3b759192c46a449dbfe25b61f3
artifact_path: projects/PROJ-689-searchswarm-towards-delegation-intellige/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T17:14:32.747453Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents a compelling architecture for delegation intelligence, but the statistical rigor of the empirical evaluation requires strengthening to support the claims of state-of-the-art performance.

First, the primary results in Table 1 (Section 4.2) report point estimates for benchmark scores (e.g., 68.1 vs. 67.9 on BrowseComp) without any measure of variance. Given that the performance gaps between SearchSwarm and the closest competitors (MiroThinker-1.7-mini) are often less than 1.0 point, it is impossible to determine if these differences are statistically significant or within the noise of the evaluation process. The authors must report standard deviations (calculated over multiple random seeds or bootstrap samples) or perform significance testing (e.g., paired t-tests or Wilcoxon signed-rank tests) to validate that the observed improvements are not due to chance.

Second, the ablation study in Section 4.3 ("Effectiveness of the Harness") relies on a 200-question subset of BrowseComp. The text does not specify the sampling method (e.g., random stratified sampling) or whether the evaluation was repeated across multiple seeds. Without this information, the reported +10.0 gain could be an artifact of a favorable subset selection. The authors should clarify the sampling protocol and ideally report the variance of the gain across different subsets or seeds.

Finally, in Section 4.5, the paper claims generalization to a single-agent setting by disabling the `call_sub_agent` tool. However, it compares the fine-tuned model in this mode against the base model's standard performance. To properly isolate the effect of the fine-tuning on decomposition skills, the base model should also be evaluated in the same single-agent configuration (with the tool disabled) to provide a fair baseline. The current comparison conflates the effect of the architectural constraint with the effect of the training data.

Addressing these statistical gaps is essential to substantiate the claim that SearchSwarm achieves a genuine, reproducible improvement over existing methods.
