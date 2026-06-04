---
action_items:
- id: ecf997d27e38
  severity: science
  text: Report standard deviations or confidence intervals for VBench scores in Tables
    2 and 3 to quantify variance across seeds.
- id: 801dcb36a8e8
  severity: science
  text: Explicitly state the number of evaluation samples (N) and inference random
    seeds used for benchmark metrics.
- id: 813f820d116e
  severity: science
  text: Apply statistical significance tests (e.g., t-tests) to validate performance
    claims over baselines.
artifact_hash: 6191ec14b8389b89c96572533c3f6f5e9333a3f73e89fe363432c3a9d7429fb8
artifact_path: projects/PROJ-604-https-arxiv-org-abs-2605-18739/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-04T19:00:56.235335Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical reporting in the experimental results requires strengthening to fully support the quantitative claims. While the efficiency metrics (latency, memory) in Table 1 (`tab:wan22_ffn1_nvfp4`) are deterministic system measurements, the quality benchmarks in Table 2 (`tab:baseline_fps`) and Table 3 (`tab:vbench_long_30s_60s`) lack necessary statistical context.

Specifically, VBench scores are reported as single point estimates (e.g., 85.06 Total Score). Video generation metrics exhibit high variance across random seeds and prompt variations. Without reporting standard deviations or confidence intervals (e.g., 95% CI), it is impossible to determine if the observed differences between LongLive-2.0 and baselines (e.g., Self-Forcing 84.31 vs LongLive-2.0 85.06) are statistically significant or within noise margins. Section 5 ("Experimental Results") should explicitly state the number of evaluation samples ($N$) used to compute these averages. Currently, the text mentions "official VBench prompts" but does not specify the count or sampling strategy, making reproducibility of the exact mean scores difficult.

Furthermore, claims of "strong performance" and "best average rank" imply a hypothesis test. The authors should apply statistical significance tests (e.g., paired t-tests or Wilcoxon signed-rank tests) across multiple random seeds to validate that the improvements are not due to chance. For the ablation study in Table `tab:inference_progressive`, the latency improvements are system-level and likely reproducible, but the quality trade-offs (e.g., 2-step vs 4-step VBench scores in Table `tab:baseline_fps`) also need variance reporting to justify the step reduction.

Finally, Appendix `ap:implementation_details` lists training hyperparameters but omits inference random seeds. Reproducibility of the reported benchmarks requires fixing or reporting the random seeds used for generation during evaluation. Addressing these gaps will ensure the performance claims are statistically robust and prevent overclaiming based on potentially non-significant differences.
