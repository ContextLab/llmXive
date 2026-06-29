---
action_items:
- id: b3b2d67bfc33
  severity: science
  text: Report standard deviations or confidence intervals for all benchmark scores
    (Table 1, Appendix Tables) to establish statistical significance of improvements
    over baselines.
- id: 4981b898ff70
  severity: science
  text: Include error bars or variance metrics for ablation studies (Figures 2-5,
    Table 2) to distinguish signal from training noise.
- id: 63c1e2d4154e
  severity: science
  text: Specify training random seeds and clarify Model FLOPS Utilization (MFU) assumptions
    for the compute efficiency claim to ensure reproducibility.
artifact_hash: ee50a22651a80bef159316dc0dc914d3939b89b46e64d966972efb2307431ada
artifact_path: projects/PROJ-624-lens-rethinking-training-efficiency-for/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T04:10:53.311605Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents compelling empirical results but lacks rigorous statistical reporting required to validate the significance of the efficiency and performance claims. Specifically, the statistical analysis is insufficient in four key areas:

1. **Benchmark Variance:** Table 1 and Appendix Tables (e.g., `tab:main_geneval`) report single-point scores (e.g., GenEval 0.930) without standard deviations or confidence intervals. In deep learning, performance varies significantly across random seeds. Without error bars or multiple run averages, it is impossible to determine if the improvements over baselines (e.g., Z-Image 0.840) are statistically significant or attributable to initialization variance.

2. **Ablation Uncertainty:** Figures 2-5 and Table 2 (RL ablation) display performance curves and comparisons but omit error bars. For instance, the GenEval score difference between the 1/4 and Full RL sets (0.916 vs 0.930) is marginal. Statistical testing (e.g., t-tests) or variance reporting is needed to confirm this improvement is not noise. Similarly, the VAE and Language Encoder ablations (Figures 2b, 4) lack uncertainty quantification.

3. **Compute Efficiency:** The claim that Lens uses "19.3% of the training compute" (Section 1, lines 45-50) relies on peak TFLOPS. Actual Model FLOPS Utilization (MFU) varies significantly across hardware, batch sizes, and optimization steps. No uncertainty bounds or MFU measurements are provided for this efficiency metric, making the comparison an estimate rather than a precise statistical claim.

4. **Reproducibility:** Training random seeds are not specified in Section 3 or Appendix. This prevents independent verification of the reported point estimates.

To strengthen the statistical validity, the authors should report standard deviations over at least three random seeds for all benchmark and ablation results. Additionally, clarify the MFU assumptions for the compute comparison or provide measured utilization rates.
