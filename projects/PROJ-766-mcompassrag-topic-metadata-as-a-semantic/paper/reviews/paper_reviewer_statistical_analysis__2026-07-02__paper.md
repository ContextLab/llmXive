---
action_items:
- id: 44cf0a225a11
  severity: science
  text: Report statistical significance (e.g., paired t-tests or bootstrap CIs) for
    the claimed 8.24% average IE improvement and latency reductions across the six
    benchmarks. Point estimates alone are insufficient to support the claim of consistent
    outperformance.
- id: 50e29e4d961f
  severity: science
  text: Clarify the experimental design for the 'LLM + 10 Topics' oracle baseline.
    Is this a single run or an average? If single, the comparison against the student
    model (which likely has variance) is statistically invalid without error bars
    or significance testing.
- id: d0c703075ff7
  severity: science
  text: The ablation study (Table 3) shows small absolute differences (e.g., IE 38.97
    vs 38.03). Without reported standard deviations or p-values, it is unclear if
    the 'Abstraction' and 'Selection' components provide statistically significant
    gains over the noise floor.
artifact_hash: 5e7163c1713464843d620f2c37705ca96ededa7c235cfa3e5a0986f0a19b0aa7
artifact_path: projects/PROJ-766-mcompassrag-topic-metadata-as-a-semantic/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T23:53:26.681726Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents a novel retrieval framework, MCompassRAG, but the statistical rigor supporting its central claims is currently insufficient. While the authors report substantial improvements in Information Efficiency (IE) and latency, the analysis relies almost exclusively on point estimates without measures of variance or statistical significance testing.

Specifically, the claim that the method "consistently outperforms all baselines" (Section 4.2) is not statistically substantiated. For instance, Table 1 reports an average IE improvement of 8.24% over the strongest non-LLM baseline. However, there is no indication of whether this difference is statistically significant across the six benchmarks. Given the variability inherent in retrieval tasks and the specific dataset splits used, a paired t-test or bootstrap confidence intervals (e.g., 95% CI) are required to validate that these gains are not due to random chance.

Furthermore, the comparison against the "LLM + 10 Topics" oracle (Table 1 and Table 2) lacks context regarding variance. If the oracle results are single-point measurements (common in LLM-based baselines due to cost), comparing them against a student model without error bars creates an unfair or misleading statistical comparison. The ablation study in Table 3 (Section 5) also presents marginal gains (e.g., IE dropping from 38.97 to 38.03 when removing abstraction) without reporting standard deviations. It is impossible to determine if these component contributions are statistically distinguishable from zero.

Finally, the hyperparameter sensitivity analysis (Section 5, Figure 4) notes that performance "peaks at 12–15 topics" (text) but Table 4 shows $K=100$ as the optimal setting. This discrepancy in the reported optimal topic count ($K$) needs clarification, and the performance drop at higher $K$ values should be accompanied by significance tests to confirm the degradation is real and not noise. The authors must provide statistical validation (p-values, CIs, or standard deviations) for all comparative claims to support the paper's conclusions.
