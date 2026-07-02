---
action_items:
- id: c4bcc5c088bd
  severity: science
  text: The evaluation protocol relies on 'best-of-5' sampling for all baselines (Sec
    4.1), but the text does not explicitly state if the proposed MolmoMotion models
    also used best-of-5 or a single deterministic pass. If MolmoMotion used a single
    pass while baselines used sampling, the reported ADE/FDE improvements are inflated.
    Clarify the sampling strategy for all methods in Tab 1.
- id: 82dc014728a5
  severity: science
  text: The claim that pixel-space methods (Wan2.2, Cosmos) perform poorly on metric
    3D tasks (Tab 1) relies on a post-hoc lifting pipeline (Sec 4.1 Baselines). The
    error introduced by this specific lifting pipeline (ViPE + AllTracker) is not
    quantified separately from the video generator's failure. A control experiment
    showing the lifting pipeline's error on ground-truth video frames is needed to
    isolate the generator's contribution to the metric error.
- id: 85ed6673ca76
  severity: science
  text: The robotics transfer results (Fig 3a) show a large gap in success rates (51%
    vs 19% at 10K steps). The text attributes this to the motion prior, but does not
    report the variance (standard deviation) across the 4 splits (SS, SU, US, All)
    or the number of seeds used for the policy training. Without variance estimates,
    the statistical significance of the 'substantial improvement' claim is unclear.
artifact_hash: 43d44b1b7f12aef158eaf0787875484ea72c6860cf8af3c796e4579ec99e55ab
artifact_path: projects/PROJ-741-molmomotion-forecasting-point-trajectori/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T05:12:37.053534Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The scientific evidence presented for the core claims of MolmoMotion is generally robust, particularly regarding the scale of the dataset (1.16M clips) and the diversity of the benchmark (111 object categories). The ablation studies in the Appendix (Tab 4) effectively isolate the contribution of the anchor-relative coordinate parameterization and language conditioning, providing strong causal evidence for the architectural choices. The use of human-verified ground truth for the benchmark (Sec 4.2) strengthens the validity of the quantitative comparisons.

However, there are critical gaps in the experimental rigor regarding the evaluation protocol and statistical reporting. First, Section 4.1 states that "we follow best-of-5 evaluation for each sample" for all methods. It is ambiguous whether the proposed MolmoMotion models (both AR and FM) were evaluated using this sampling strategy or a single deterministic pass. If the baselines (e.g., pixel-space generators) were evaluated with best-of-5 selection while MolmoMotion was not, the reported superiority in ADE/FDE is artificially inflated. The authors must explicitly confirm the sampling strategy for every row in Table 1.

Second, the claim that pixel-space video generators fail at metric 3D prediction (Table 1) relies on a specific post-hoc pipeline (ViPE depth estimation + AllTracker) to lift 2D video outputs to 3D. The paper does not quantify the error floor of this lifting pipeline itself. If the lifting pipeline introduces significant noise or bias, the poor performance of Wan2.2 and Cosmos may reflect the limitations of the evaluation metric rather than the video generators' inability to model motion. A control experiment measuring the lifting pipeline's error on ground-truth video frames is necessary to validate the comparison.

Finally, the robotics transfer results (Figure 3a) present mean success rates across four splits but omit variance metrics (standard deviation) and the number of random seeds used for training the downstream policies. Given the stochastic nature of policy optimization and the relatively small sample size of the MolmoSpaces benchmark, the statistical significance of the "substantial improvement" (e.g., 51% vs 19%) cannot be assessed without this information. The authors should report standard deviations or confidence intervals to support the claim of improved generalization.
