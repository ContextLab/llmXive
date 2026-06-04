---
action_items:
- id: d77d61dcd791
  severity: science
  text: Provide standard deviations for VBench scores (Tables 2, 3) to establish statistical
    significance of quality gains.
- id: ef5966277535
  severity: science
  text: Control for resolution differences in Table 2 (1280x720 vs 832x480) to isolate
    model performance from resolution effects.
- id: 85eca87e8137
  severity: science
  text: Quantify PTQ vs Pre-trained NVFP4 quality gap in Appendix with metrics like
    LPIPS/FID rather than qualitative descriptions.
artifact_hash: 6191ec14b8389b89c96572533c3f6f5e9333a3f73e89fe363432c3a9d7429fb8
artifact_path: projects/PROJ-604-https-arxiv-org-abs-2605-18739/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-04T18:59:32.150768Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The evidence for efficiency gains is robust, with clear ablations in Table 1 (Training Efficiency) and Table 2 (Inference Efficiency) demonstrating the impact of Balanced SP and NVFP4. The hardware specificity (GB200) is clearly stated in the Limitations section, supporting the claim that speedups are architecture-dependent. However, the evidence supporting quality claims requires strengthening to ensure robustness. In Table 2 (VBench), LongLive-2.0 is evaluated at 1280x720, while most baselines (Self-Forcing, Causal-Forcing, etc.) are at 832x480. Resolution differences confound the quality/speed trade-off analysis, as higher resolution typically impacts both inference time and metric scores. Please provide a controlled comparison at a fixed resolution or quantify the resolution impact on VBench scores to validate the SOTA claim. Additionally, VBench scores in Table 2 and Table 3 are reported as single values without standard deviations or multiple seed runs. Given the stochastic nature of diffusion models, statistical significance (e.g., mean ± std over 3 seeds) is needed to confirm that the reported gains (e.g., 85.06 vs 84.87 Total score) are not due to random variance. The dataset size (120K videos, Appendix) is sufficient, but the train/val/test split is not explicitly detailed in the main text. Finally, Appendix Table `tab:appendix_ll2_precision_settings` and Figure `fig:ptq_nvfp4_comparison` show PTQ vs Pre-trained NVFP4 but rely on qualitative claims ("blurred eyes") for degradation. Quantitative metrics (e.g., LPIPS, FID) for these ablations would strengthen the evidence for the NVFP4 training alignment claim over post-training quantization.
