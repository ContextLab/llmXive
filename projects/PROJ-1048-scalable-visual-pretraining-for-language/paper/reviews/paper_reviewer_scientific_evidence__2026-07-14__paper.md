---
action_items:
- id: 69478c03c024
  severity: writing
  text: The paper presents a compelling hypothesis that visual pretraining (VP) on
    raw scientific documents improves reasoning capabilities compared to text-only
    pretraining (TP) on the same corpus. The experimental design generally follows
    a matched-corpus approach, which is a strong starting point. However, several
    critical gaps in the experimental design prevent the evidence from fully supporting
    the magnitude and specificity of the claims made. First, the statistical robustness
    of the reported impro
artifact_hash: 819c8b5fd062f0531cdf830c89d642bcd4d25ad03c275f7103c9aac8218dec1b
artifact_path: projects/PROJ-1048-scalable-visual-pretraining-for-language/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-14T02:59:25.548773Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling hypothesis that visual pretraining (VP) on raw scientific documents improves reasoning capabilities compared to text-only pretraining (TP) on the same corpus. The experimental design generally follows a matched-corpus approach, which is a strong starting point. However, several critical gaps in the experimental design prevent the evidence from fully supporting the magnitude and specificity of the claims made.

First, the statistical robustness of the reported improvements is unclear. Table 1 (tab:main_result_text) presents specific point estimates for gains (e.g., +3.22 on GPQA, +2.1 on MMLU-Pro) without reporting standard deviations, confidence intervals, or the number of random seeds used for the non-AIME benchmarks. While the text mentions "32 runs" for AIME-25, it is silent on the variance for the other benchmarks. In large-scale LLM evaluations, performance can fluctuate significantly based on random initialization, sampling temperature, or prompt variations. Without reporting variance across multiple seeds, it is impossible to determine if the observed gains are statistically significant or within the noise floor of the evaluation protocol. The authors must report mean ± standard deviation (or standard error) across at least 3-5 independent training runs for all benchmarks to establish that the effect is stable and not a result of lucky seeds.

Second, the claim that the improvement is due to the *visual representation* rather than the *total training budget* is confounded. The paper explicitly states that VP uses 20B visual tokens while TP uses 80B text tokens from the same PDFs, resulting in a total CPT budget of 120B for VP versus 180B for TP. The authors argue this difference reflects the "compactness" of visual tokens, but they do not control for the total amount of optimization steps or data volume. It is equally plausible that the performance gain arises because the VP model was trained on a different (potentially more optimal) total token count, or that the specific ratio of visual-to-text tokens in the VP mix (1:4) is simply a better training recipe than the TP mix, rather than the visual modality itself being superior. To isolate the contribution of the visual modality, the authors should include a control experiment where the TP baseline is trained on a matched token budget (e.g., 120B tokens) or where the VP model is trained on a matched 180B budget. Without this, the "efficiency" claim is ambiguous.

Third, the attribution of the gain to the specific VP mechanism (next-visual-latent prediction) lacks ablation. The paper introduces a complex pipeline involving foreground filtering, raster ordering, and a contrastive loss. However, there is no ablation study that removes or varies these components in isolation. For instance, does the gain persist if the visual tokens are not filtered for foreground? Does the contrastive loss matter compared to a simple MSE reconstruction? Without these controls, the claim that the specific "visual pretraining" paradigm is the driver of the improvement is not fully supported; the gain could be an artifact of the specific hyperparameters or the inclusion of any visual signal, regardless of the specific objective.

Finally, the evaluation of "visual structure density" (Figure 2c) relies on a post-hoc categorization of the test set. While the trend is consistent with the hypothesis, the paper does not provide a negative control or a randomized baseline to ensure that the density metric itself isn't correlated with other confounding factors (e.g., question difficulty or length).

In summary, while the direction of the results is promising, the evidence is currently insufficient to rule out alternative explanations such as training budget differences, random seed variance, or the specific tuning of the visual pipeline. Addressing these design gaps is necessary to substantiate the central claims.
