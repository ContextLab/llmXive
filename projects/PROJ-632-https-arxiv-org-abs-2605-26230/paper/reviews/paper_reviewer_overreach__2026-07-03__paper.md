---
action_items:
- id: d577ee37513a
  severity: science
  text: The paper exhibits significant overreach in its claims regarding the capabilities
    of the GARD framework and the limitations of existing baselines, which are not
    fully supported by the presented data. First, the central claim of "simultaneous
    recovery" of 3D geometry and high-quality RGB imagery is not substantiated. While
    the method proposes an RGB decoder, the experimental results (Tables 1, 2, and
    3) focus exclusively on pose estimation, 3D reconstruction metrics (Overall, F-score),
    and depth
artifact_hash: 1b009a000ce5ea80de9107001816db5f680b271a1e700e1b78677c55727d55dc
artifact_path: projects/PROJ-632-https-arxiv-org-abs-2605-26230/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T17:37:56.784462Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: full_revision
---

The paper exhibits significant overreach in its claims regarding the capabilities of the GARD framework and the limitations of existing baselines, which are not fully supported by the presented data.

First, the central claim of "simultaneous recovery" of 3D geometry and high-quality RGB imagery is not substantiated. While the method proposes an RGB decoder, the experimental results (Tables 1, 2, and 3) focus exclusively on pose estimation, 3D reconstruction metrics (Overall, F-score), and depth estimation. There are no quantitative metrics (e.g., PSNR, LPIPS) or qualitative visualizations of the *restored RGB images* produced by the GARD decoder in the main results tables. The claim that the framework enables high-quality image restoration is therefore an extrapolation beyond the provided evidence.

Second, the paper overstates the superiority of the proposed method by framing comparisons ambiguously. In Table 1, the "HQ Input" row represents the theoretical upper bound (clean data). GARD's performance (e.g., ETH3D AUC30: 74.68) is significantly lower than this upper bound (84.68), yet the text implies a near-complete recovery of the degradation effects. The authors fail to explicitly state that the method does not fully restore the performance to the clean-input level, potentially misleading readers about the efficacy of the denoising process.

Third, the motivation section overgeneralizes the failure of VAE-based latent spaces. The paper argues that VAEs introduce "information bottlenecks" that prevent fine-grained detail preservation. However, the ablation study (Table 2) shows that the VAE-based baseline (VAE_MVD) performs competitively, and in some cases (e.g., 7Scenes AUC30: 76.50 vs GARD's 84.73, a relatively small margin compared to the gap with single-view methods), the performance gap is not as drastic as the narrative suggests. The claim that VAEs "fail" to preserve details is too absolute given the empirical data.

Finally, the benefit of the "Attention Alignment Loss" is overclaimed. The ablation study (Table 2) reveals that adding attention alignment to the standard flow matching objective (Model B) results in a performance drop compared to using flow matching alone (Model A) on the ETH3D dataset (66.42 vs 67.30). The paper presents the alignment loss as a universally beneficial component for enforcing geometric consistency, ignoring the evidence that it can be detrimental in certain configurations without providing a nuanced discussion on its sensitivity.
