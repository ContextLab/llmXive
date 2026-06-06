---
action_items:
- id: 78d43f413103
  severity: science
  text: Report mean and standard deviation for all benchmark tables (e.g., Table 1,
    Table 2) instead of single point estimates to quantify variability.
- id: ba7c1dcccbaf
  severity: science
  text: Specify the sample size (n) for all percentile claims (e.g., p95 latency in
    Table 4) to ensure statistical validity of tail metrics.
- id: d5e9aae38187
  severity: science
  text: Add error bands (e.g., std or confidence intervals) to learning curves in
    Figure 3 to demonstrate stability across training runs.
artifact_hash: b4bbb587409bb8ce9fbc13953a4d6d307cbe54e41c3196b0506aac091594e206
artifact_path: projects/PROJ-566-mint-managed-infrastructure-for-training/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-06T12:58:13.902739Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

This re-review confirms that all three prior statistical analysis action items remain unaddressed in the current revision.

**Item 78d43f413103 (Unaddressed):** Tables 1 and 2 (tab:e1_handoff_paths, tab:e2_training_utilization) still report single point estimates without variance measures. For example, Table 1 shows "0.036 s" load time and "15.568/15.567 tok/s" sample speed without any indication of measurement variability (mean/std or confidence intervals). Table 2 reports wall times like "3081.2 s" and "1736.1 s" without standard deviations across the 3 GRPO policies tested.

**Item ba7c1dcccbaf (Unaddressed):** Percentile claims lack sample size specifications throughout. Table 4 (tab:e4_serving_summary) reports "p95 21.35 s" and "p95 199.81 s" without stating n (number of requests measured). Similarly, Section 5.1 states "cold-load p95 latency 199.81 s" without specifying how many cold requests were sampled. This prevents readers from assessing the statistical reliability of tail metric claims.

**Item d5e9aae38187 (Unaddressed):** Learning curves in Figure 3 (fig:e3_dense_curves, fig:e3_moe_curves) show single trace lines without error bands or confidence intervals. The caption describes "Dense-model learning traces" but does not mention whether multiple runs were averaged or if variability is shown. Without error bands, claims about training stability and improvement magnitudes cannot be statistically validated.

No new statistical issues were introduced in this revision. The same methodological gaps persist: point estimates without variance, percentile claims without sample sizes, and learning curves without uncertainty visualization. These issues undermine reproducibility and confidence in the reported performance improvements.
