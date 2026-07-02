---
action_items:
- id: f641e37966c8
  severity: science
  text: In Section 3.2 and Table 1, report statistical significance tests (e.g., paired
    t-tests or bootstrap confidence intervals) for the reported Pass@1/Pass@4 deltas
    between AXPO and GRPO. The current standard deviations (Table 2) show overlap
    in some cases; formal tests are needed to confirm the gains are not due to random
    rollout variance.
- id: b42bce59f8db
  severity: science
  text: The ablation study in Table 3 lacks error bars or variance estimates. Given
    the small absolute gains in some ablations (e.g., ~0.5-1.0 pp), it is unclear
    if these differences are statistically significant or within the noise floor of
    the evaluation protocol.
- id: d01eaec150b8
  severity: science
  text: In Section 2.2, the claim that tool-using subgroups are 'all-wrong on ~40%
    of questions' is based on visual inspection of Figure 3b. Please provide the exact
    sample size (number of questions/rollouts) and the 95% confidence interval for
    this proportion to validate the diagnostic claim.
artifact_hash: c3a0cadd7f6fad4530caf3425af37b062e581bf6756717caa2b10b397e7c3c2b
artifact_path: projects/PROJ-639-https-arxiv-org-abs-2605-28774/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T05:17:13.590965Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in the paper is generally sound in its experimental design, utilizing multiple rollouts (N=4 for evaluation, N=8 for training) and reporting standard deviations across independent runs (Table 2). However, the manuscript relies heavily on point estimates for its primary claims without formal statistical testing.

Specifically, in Section 3.2 and Table 1, the authors report average Pass@1 and Pass@4 improvements (e.g., +1.8 pp at 8B). While Table 2 provides standard deviations across four independent evaluation rollouts, these are relatively small (1.2–1.4 pp). The paper does not perform hypothesis testing (e.g., paired t-tests or bootstrap confidence intervals) to determine if the observed deltas between AXPO and the SFT+GRPO baseline are statistically significant. Given that some per-benchmark gains are small (e.g., +0.2 pp in Math-VR), the lack of significance testing makes it difficult to distinguish genuine methodological improvements from random variance in the evaluation process.

Furthermore, the ablation study in Table 3 presents point estimates for each component removal. Without variance estimates or significance tests, it is unclear if the observed drops (e.g., the 0.5–1.0 pp differences) are statistically meaningful or within the noise of the evaluation. The diagnostic claim in Section 2.2 regarding the "all-wrong" rate of ~40% for tool-using subgroups is supported by Figure 3b, but the text does not specify the sample size (number of questions) or provide a confidence interval for this proportion, which is critical for validating the severity of the identified gap.

To strengthen the statistical rigor, the authors should: (1) report p-values or 95% confidence intervals for the main performance comparisons in Table 1; (2) include variance estimates or significance tests for the ablation results in Table 3; and (3) explicitly state the sample sizes and confidence intervals for the diagnostic statistics in Section 2.2.
