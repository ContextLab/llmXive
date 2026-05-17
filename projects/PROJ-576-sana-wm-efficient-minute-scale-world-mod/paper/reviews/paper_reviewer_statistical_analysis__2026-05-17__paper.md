---
artifact_hash: e5cefeb8f5a622284bf4bd8a2b4800bf995401cb7708f8533b8b272aa0c905d4
artifact_path: projects/PROJ-576-sana-wm-efficient-minute-scale-world-mod/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-17T14:50:46.644684Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The quantitative evaluation lacks essential statistical rigor to support the performance claims made throughout the paper. Table 1 (Section 5.2) presents point estimates for Pose Accuracy (RotErr, TransErr) and VBench scores without standard deviations, confidence intervals, or significance testing. For instance, the claim that SANA-WM achieves "stronger action-following accuracy" (Section 5.2) is based on mean values over 80 scenes (Section 5.1), but the variance across these scenes is unreported. Given the high variability inherent in video generation metrics, statistical significance tests (e.g., paired t-tests or Wilcoxon signed-rank tests against baselines) are required to validate these improvements.

Similarly, the ablation studies in Table 3 (Section 5.3) and Table 4 (Section 5.3) report single-point performance metrics (FVD, RotErr) without uncertainty bounds. The GDN key scaling analysis (Fig. 4) shows stability but lacks statistical replication across different random seeds or data splits. The benchmark size of 80 initial scenes (Section 5.1) is modest for minute-scale video evaluation; reporting confidence intervals (e.g., 95% CI) would clarify the reliability of the mean scores. Additionally, the Pose Accuracy metric relies on Pi3X pose estimation (Appendix Sec. 5.1), which has its own error distribution. The paper does not account for this measurement uncertainty in the reported Pose Acc metrics. To ensure reproducibility and robustness, please report standard deviations across the 80 benchmark scenes and include significance tests for all comparative claims in Tables 1, 3, and 4.
