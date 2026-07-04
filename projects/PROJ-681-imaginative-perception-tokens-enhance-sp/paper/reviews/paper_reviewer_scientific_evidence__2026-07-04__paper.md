---
action_items:
- id: 3ab5c93e8931
  severity: science
  text: The paper presents a compelling method for spatial reasoning, but the experimental
    design currently fails to rule out several alternative explanations for the reported
    gains. First, the primary evidence for the efficacy of Imaginative Perception
    Tokens (IPTs) relies on single-run results reported in Table 1 and the supplementary
    Table pt_breakdown. The authors report specific accuracy improvements (e.g., Bagel
    + IPT achieving 61.1% vs. Bagel base at 36.3% on EgoDir) without providing standard
    de
artifact_hash: c5de9734fccbfd100241f7fc8603c599264726354d7ecbedd4d657c0e121782f
artifact_path: projects/PROJ-681-imaginative-perception-tokens-enhance-sp/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-04T01:41:26.933565Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: full_revision
---

The paper presents a compelling method for spatial reasoning, but the experimental design currently fails to rule out several alternative explanations for the reported gains.

First, the primary evidence for the efficacy of Imaginative Perception Tokens (IPTs) relies on single-run results reported in Table 1 and the supplementary Table `pt_breakdown`. The authors report specific accuracy improvements (e.g., Bagel + IPT achieving 61.1% vs. Bagel base at 36.3% on EgoDir) without providing standard deviations, confidence intervals, or results across multiple random seeds. In spatial reasoning tasks, performance can fluctuate significantly based on initialization and sampling. Without variance reporting, it is impossible to determine if these gains are robust or artifacts of a lucky seed. The authors must re-run experiments across at least 3-5 seeds to establish statistical stability.

Second, the ablation study in Table `pt_breakdown` contains a critical confound regarding the source of improvement. The "Mixed Training" variant (which includes 15k real-world VST examples) achieves 71.7% on EgoDir, significantly outperforming the "+ IPT" variant (61.1%) which uses only synthetic data. The paper attributes the success to the IPT mechanism, yet the data suggests that simply increasing the volume and diversity of training data (the "Mixed" component) yields a larger boost than the IPT tokens themselves. The design does not isolate the contribution of the token architecture from the contribution of the expanded dataset. A fair comparison requires a control run where the model is trained on the full "Mixed" dataset using standard answer-only tokens (no IPTs) to see if the data alone explains the performance jump.

Finally, the comparison against frontier models (GPT-5, Gemini 3) is unfair due to training asymmetry. The proposed method is heavily fine-tuned on a custom dataset, while the baselines are evaluated in zero-shot or few-shot modes. This conflates the benefit of the proposed method with the benefit of task-specific fine-tuning. To support the claim that IPTs are a superior *method* for spatial reasoning, the authors must compare their approach against a baseline that receives the same fine-tuning regimen (same data, same compute) but lacks the IPT mechanism. Without these controls, the evidence supports "fine-tuning on this specific dataset helps" more than "IPTs enhance spatial reasoning."
