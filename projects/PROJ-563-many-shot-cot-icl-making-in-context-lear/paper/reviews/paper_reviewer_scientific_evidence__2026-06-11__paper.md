---
action_items:
- id: c54fa3804f74
  severity: science
  text: Report standard deviation or confidence intervals for CDS results in Tables
    3 and 4 to establish statistical significance of reported gains.
- id: a8696b97ce33
  severity: science
  text: Increase the number of random seeds for variance analysis beyond 5, or provide
    statistical justification for the current sample size given observed variance.
- id: d1ad89a71ed0
  severity: science
  text: Clarify potential circularity in embedding model selection (Qwen3 target vs.
    Qwen3-Embedding) for the primary curvature analysis.
artifact_hash: da80d19d18126d829231e022c90784234c941daee73db4750a219950884e0e6f
artifact_path: projects/PROJ-563-many-shot-cot-icl-making-in-context-lear/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-11T10:42:45.611510Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents compelling empirical evidence that many-shot CoT-ICL behaves differently from traditional ICL, supported by strong experimental controls like the procedural corruption ablation (Table `tab:procedure_corruption_main`, Section `sec:factor`). This control effectively isolates the impact of reasoning steps from surface patterns, strengthening the claim that models absorb procedures. However, the scientific evidence supporting the proposed Curvilinear Demonstration Selection (CDS) method lacks sufficient statistical rigor for a definitive conclusion. Tables 3 and 4 (`tab:CDS_robustness`, `tab:high_curvature_ablation`) report single accuracy points without standard deviations or confidence intervals. Given the variance observed in the seed analysis (Appendix Table 1 shows $\sigma \approx 0.8$ for Qwen3-14B), it is difficult to determine if the reported gains (e.g., 3.75 pp on geometry) are statistically significant or within the noise margin.

Furthermore, the variance analysis relies on only five random demonstration-ordering seeds (Appendix `sec:statistical_robustness`). While this captures some variance, it may be insufficient for robust claims about order sensitivity, especially when standard deviations are high (e.g., $\sigma \approx 8.08$ for Llama at 32 shots in Appendix Table 2). The current sample size limits the power of statistical tests for the CDS method's efficacy. Finally, the curvature analysis uses Qwen3-Embedding-4B for the target Qwen3 models, introducing potential circularity where the embedding space aligns with the model's own representations. While bge-m3 is tested as a robustness check, the primary results should explicitly address this dependency. Addressing these statistical reporting gaps—specifically adding error bars to main tables and justifying the seed count—is necessary to validate the claimed efficacy of CDS against alternative explanations like random fluctuation.
