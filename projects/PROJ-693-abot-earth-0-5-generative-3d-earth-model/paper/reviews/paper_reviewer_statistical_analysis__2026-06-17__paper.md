---
action_items:
- id: 04f706281280
  severity: science
  text: "Provide a detailed description of the evaluation protocol for FID/KID, including\
    \ the exact number of generated samples, the number of ground\u2011truth images,\
    \ and how the views were sampled. Without this information the reported scores\
    \ cannot be statistically interpreted."
- id: 6f0e89038a07
  severity: science
  text: "Report variability measures (e.g., mean\u202F\xB1\u202Fstd, confidence intervals)\
    \ for FID and KID, using bootstrapping or multiple random seeds. This will allow\
    \ assessment of whether the improvements over baselines are statistically significant."
- id: 06801cbae04a
  severity: science
  text: "Apply appropriate statistical tests (e.g., paired t\u2011test or Wilcoxon\
    \ signed\u2011rank) when comparing your method to baselines, and correct for multiple\
    \ comparisons if more than one metric or dataset is used."
- id: 059ee3c88ff9
  severity: writing
  text: Include the random seeds, data splits, and any preprocessing parameters used
    for both training and evaluation to ensure full reproducibility of the quantitative
    results.
- id: 0a58e0b40fb8
  severity: science
  text: "If ablation studies are presented elsewhere, add statistical significance\
    \ analysis (p\u2011values, effect sizes) to demonstrate that each component contributes\
    \ meaningfully to performance."
artifact_hash: 889d5a8e39acbdaa7baa4d1b8f93a551383f0dbc1ede3c36f50fc7a5e7bb8167
artifact_path: projects/PROJ-693-abot-earth-0-5-generative-3d-earth-model/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-17T06:18:17.514065Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript reports generative fidelity using FID = 16.1 and KID = 0.006 (Table 5), claiming a “substantial improvement” over baselines. However, the statistical foundation of these claims is insufficient. The paper does not specify how many images were generated for each method, how many ground‑truth renders were used, or whether the same camera poses were employed across methods. Without knowing the sample sizes, the variance of the FID/KID estimates cannot be assessed, making the reported point estimates unreliable.

Furthermore, no confidence intervals or standard deviations are provided. FID scores are known to be sensitive to random seed and dataset sampling; a single run may over‑ or under‑estimate true performance. The authors should compute variability (e.g., via bootstrap resampling of the generated and reference image sets) and report 95 % confidence intervals. This would enable a rigorous comparison to the baselines whose reported scores (e.g., CityDreamer FID = 97.3) also lack variance estimates.

The manuscript compares three baselines but does not address multiple‑comparison issues. If the authors later add more baselines or metrics, statistical corrections (Bonferroni, Holm‑Šidák, or false‑discovery‑rate control) should be applied to avoid inflated Type I error.

Reproducibility is also unclear: the code for the evaluation pipeline, random seeds, and preprocessing steps (e.g., image resolution, cropping, color normalization) are not disclosed. Since FID/KID are highly dependent on these details, providing the exact pipeline is essential for independent verification.

Finally, any ablation experiments (e.g., the effect of the sliding‑window inference or the VLM‑based conditioning) should be accompanied by statistical significance testing to substantiate claims that each component improves fidelity.

Addressing these points—detailing the evaluation protocol, reporting variability, performing proper statistical tests, and supplying reproducibility artifacts—will strengthen the empirical claims and bring the manuscript in line with standard statistical analysis practices.
