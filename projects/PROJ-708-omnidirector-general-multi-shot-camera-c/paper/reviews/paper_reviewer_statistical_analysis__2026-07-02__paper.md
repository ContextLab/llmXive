---
action_items:
- id: e7a157d11415
  severity: science
  text: "The evaluation metrics R-Pre and T-Pre are defined with inconsistent units:\
    \ R-Pre uses a 4\xB0 angular threshold, while T-Pre uses a 20\xB0 threshold for\
    \ translation error. Translation error (RTE) is typically measured in distance\
    \ (meters) or normalized units, not degrees. Clarify the definition of T-Pre and\
    \ ensure the threshold is appropriate for the metric's unit."
- id: 0a6265782a69
  severity: science
  text: The GSB (Good/Same/Bad) pairwise comparison results in Table 3 lack statistical
    significance testing (e.g., binomial test or confidence intervals). With sample
    sizes implied by the percentages, the observed differences (e.g., 88.52% vs. baseline)
    should be validated to ensure they are not due to random chance.
- id: dc6153b012f4
  severity: science
  text: The ablation study in Table 2 presents point estimates for metrics (e.g.,
    RRE, RTE) without reporting variance (standard deviation) or confidence intervals.
    Given the stochastic nature of diffusion models and the evaluation set size (1,094
    samples), uncertainty quantification is necessary to assess the robustness of
    the reported improvements.
artifact_hash: a65d314d17ec7712e12f1ec0ba7f4dba5e22b080c532708ee9eae2b427ffd22c
artifact_path: projects/PROJ-708-omnidirector-general-multi-shot-camera-c/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T06:48:21.241425Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in the "Experiments" section requires clarification and additional rigor to support the paper's claims.

First, there is a critical ambiguity in the definition of the **T-Pre** metric (Section "Evaluation Metrics"). The text states: "T-Pre denotes the proportion of predictions with a relative translation error below 20°." However, translation error (RTE) is a measure of distance (e.g., meters or normalized units), not an angle. Rotation error (RRE) is correctly measured in degrees. It is highly likely that the authors intended to use a distance threshold (e.g., 0.2m or a normalized scale) or a different metric entirely. If the threshold is indeed 20 degrees, the metric is ill-defined for translation. This unit inconsistency must be corrected to ensure the validity of the quantitative comparison in Table 1.

Second, the **GSB pairwise comparison** results presented in Table 3 (Section "Comparisons with State-of-the-Art Methods") lack statistical validation. The table reports percentages (e.g., 88.52% for Camera accuracy) but does not provide confidence intervals or p-values from a significance test (such as a binomial test or McNemar's test). Without these, it is impossible to determine if the observed superiority over CamCloneMaster is statistically significant or merely a result of sampling variance, especially given the subjective nature of human/LLM evaluation.

Third, the **ablation study** in Table 2 reports only point estimates for metrics like RRE and RTE. In diffusion-based generation, results can vary significantly across runs due to stochasticity. The absence of standard deviations or confidence intervals makes it difficult to assess the stability of the proposed components (e.g., "w/o Semantic Fusion" vs. "Full"). The authors should report the mean and standard deviation over multiple runs or provide confidence intervals to substantiate the claimed improvements.

Finally, the evaluation set size is stated as 1,094 samples. While this is a reasonable number, the paper does not specify if the results are averaged over multiple seeds or if the evaluation was performed on a single split. Reproducibility of the statistical findings would be enhanced by explicitly stating the number of evaluation runs and the method used to aggregate results.
