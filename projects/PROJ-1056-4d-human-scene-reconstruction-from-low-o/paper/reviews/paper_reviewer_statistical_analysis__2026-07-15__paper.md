---
action_items:
- id: 628c0f92b299
  severity: writing
  text: The statistical reporting in this paper is generally consistent with common
    practices in the computer vision and graphics community (reporting mean metrics
    on fixed datasets), but it lacks the rigor required to distinguish genuine improvements
    from random variance, particularly given the small number of test scenes. The
    primary issue is the absence of uncertainty quantification. Tables 1 and 2 present
    performance metrics (PSNR, SSIM, LPIPS) to two decimal places (e.g., 18.58, 0.569)
    as if they w
artifact_hash: ca7acd8eb96627c08c8e24703eed6a4159188067f14a19009f5f71e7f58b21ed
artifact_path: projects/PROJ-1056-4d-human-scene-reconstruction-from-low-o/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-15T02:35:09.066876Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical reporting in this paper is generally consistent with common practices in the computer vision and graphics community (reporting mean metrics on fixed datasets), but it lacks the rigor required to distinguish genuine improvements from random variance, particularly given the small number of test scenes.

The primary issue is the absence of uncertainty quantification. Tables 1 and 2 present performance metrics (PSNR, SSIM, LPIPS) to two decimal places (e.g., 18.58, 0.569) as if they were exact constants. In stochastic deep learning pipelines involving Gaussian Splatting and diffusion models, results typically exhibit run-to-run variance. Without reporting the standard deviation (SD) or standard error (SE) across multiple random seeds (e.g., 3–5 runs), the reader cannot determine if the reported improvements (e.g., +2.4 PSNR) are statistically significant or within the noise floor of the training process. The field norm for such claims is "mean ± SD over N seeds."

Similarly, Table 3 (ablation_association) reports a single aggregate accuracy of 97.8% across 8 scenes. With such a small sample size (N=8), the mean is highly sensitive to outliers. A single scene with poor association would significantly lower the average. The authors should provide the per-scene accuracy values or the standard deviation across the 8 scenes to demonstrate the robustness of the association strategy.

Furthermore, the claim of "State-of-the-art" results is based on 18 pairwise comparisons (6 scenes × 3 metrics) without addressing the multiple comparisons problem. Highlighting the best result in every cell without a formal hypothesis test (e.g., paired t-test) and correction (e.g., Holm-Bonferroni or Benjamini-Hochberg) inflates the Type I error rate. While the magnitude of the improvement in some cases (e.g., LPIPS) appears large, the statistical framework to support the "significant" nature of these wins is missing. The authors should either run the appropriate statistical tests with correction or soften the language to describe the results as "empirically superior" without invoking statistical significance.

Finally, the robustness analysis in Table 5 (sensitivity to input noise) reports PSNR drops to two decimal places (e.g., 20.04) but does not indicate if these values are averages over seeds or single runs. Given the sensitivity analysis involves re-training, the variance across seeds should be reported to ensure the observed robustness is not an artifact of a lucky initialization.
