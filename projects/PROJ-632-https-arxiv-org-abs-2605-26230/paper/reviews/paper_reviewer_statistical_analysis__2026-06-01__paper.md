---
action_items:
- id: 6265f47c3df8
  severity: science
  text: Report mean and standard deviation over at least 3 random seeds for all quantitative
    results (pose, reconstruction, image metrics) instead of single-point estimates
    to establish statistical robustness.
- id: ee26249e85a9
  severity: science
  text: Perform statistical significance testing (e.g., paired t-test) to validate
    that performance gains over baselines are statistically significant rather than
    due to random variance.
- id: d1ebc862401b
  severity: science
  text: Address the statistical implications of training with up to 4 views but evaluating
    with 10 views; provide analysis on generalization variance across view counts.
artifact_hash: 1b009a000ce5ea80de9107001816db5f680b271a1e700e1b78677c55727d55dc
artifact_path: projects/PROJ-632-https-arxiv-org-abs-2605-26230/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-01T07:57:21.668366Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents the GARD framework with extensive quantitative evaluations across pose estimation, 3D reconstruction, and image restoration tasks. However, from a statistical analysis perspective, the empirical claims lack necessary rigor regarding variance and significance testing.

First, all quantitative results presented in Tables 1-4 (e.g., `tab/pose.tex`, `tab/recon.tex`, `tab/image_metric.tex`) report single-point performance metrics without standard deviations or confidence intervals. In deep learning experiments, results can vary significantly due to random initialization and stochastic optimization. Reporting mean and standard deviation over multiple random seeds (e.g., 3 seeds) is standard practice to ensure that observed improvements are robust and reproducible. Currently, it is impossible to determine if the reported gains over baselines (e.g., GARD vs. VAE_MVD in `tab/pose.tex`) are statistically meaningful or artifacts of a specific initialization.

Second, the paper does not employ statistical significance testing when comparing against the numerous baselines (Restormer, HI-Diff, VRT, etc.). With multiple comparisons across five datasets and three tasks, the risk of Type I error (false positives) increases. The authors should apply corrections (e.g., Bonferroni) or report p-values from paired t-tests to substantiate claims of "superior performance."

Third, there is a discrepancy in experimental setup between training and evaluation. Section 5 (`sec/5_exp.tex`) and the Supplementary Material (`suppl/suppl_sec/impl_detail.tex`) state that training uses up to 4 views per iteration, while evaluation uses 10 views (`V=10`). This domain shift in input dimensionality introduces potential variance. The manuscript should statistically analyze whether the model generalizes reliably to the higher view count or if performance fluctuates significantly with different subsets of 10 views.

Finally, the attention alignment loss relies on target correspondence maps derived from clean point clouds (`suppl/suppl_sec/impl_detail.tex`). If the upstream reconstruction used to generate these targets has errors on degraded inputs (which it likely does), the supervision signal becomes noisy. The authors should quantify the sensitivity of performance to this supervision noise.

Addressing these statistical gaps is essential to validate the robustness of the proposed method beyond single-run observations.
