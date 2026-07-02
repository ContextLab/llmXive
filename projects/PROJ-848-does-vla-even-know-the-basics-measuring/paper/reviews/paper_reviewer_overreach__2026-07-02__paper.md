---
action_items:
- id: b131be8e909f
  severity: writing
  text: The claim that Act2Answer 'reduces confounds from low-level control' is over-stated.
    Failures in categories like 'Symmetry' may reflect motor precision limits rather
    than knowledge loss. The text should acknowledge that control confounds are reduced
    but not eliminated, and low SR could stem from motor errors.
- id: 21512966422b
  severity: writing
  text: The claim that 'VQA co-training is associated with better knowledge retention'
    over-extrapolates from a small, non-experimental sample. The study compares existing
    models with different training histories without controlling for architecture
    or data scale. This is correlational, not causal. Language should be softened
    to reflect correlation only.
- id: 2c77b8e5db45
  severity: writing
  text: The assertion that 'answer-relevant signals... attenuate in upper layers'
    implies a specific bottleneck. However, linear probing only shows information
    is less linearly recoverable, not that it is lost. The signal may be encoded non-linearly
    for action. The interpretation should be limited to probe recoverability, not
    signal attenuation.
artifact_hash: b7bf68dc7049e64af55a4f743a5addf0de48270ccdf470df63d9da46224951a5
artifact_path: projects/PROJ-848-does-vla-even-know-the-basics-measuring/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T20:32:33.216350Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several strong claims regarding the nature of knowledge retention in Vision-Language-Action (VLA) models that extend beyond what the provided data and methodology strictly justify. While the Act2Answer protocol is a valuable contribution, the interpretation of the results frequently conflates correlation with causation and attributes performance drops to "knowledge loss" without fully ruling out alternative explanations related to the evaluation protocol itself.

First, the abstract and introduction repeatedly claim that the protocol "reduces confounds from low-level control" and yields an "action-grounded success rate with reduced control confounds." This is an over-claim. The protocol requires the agent to perform a precise placement action (moving a cube to a specific tile). While this is simpler than long-horizon manipulation, it is not free of control requirements. The results in Table 1 show that models like $\pi_0$ and OpenVLA perform near chance on categories like "Symmetry" and "Counting." The paper attributes this to a lack of knowledge. However, it is equally plausible that these models fail due to the specific motor precision required to distinguish between two closely spaced tiles, or due to a failure in the visual grounding of the "left/right" spatial instruction, rather than a lack of abstract knowledge about symmetry. The text should be revised to explicitly state that while control complexity is *reduced*, it is not *eliminated*, and that low success rates cannot be definitively attributed solely to knowledge forgetting without further ablation studies isolating motor failure.

Second, the claim in the abstract and RQ5 that "VQA co-training is associated with better knowledge retention" presents a correlational finding as a causal mechanism. The study compares models like Magma (which has VQA co-training) against OpenVLA (which does not). However, these models differ significantly in architecture, pretraining data scale, and specific fine-tuning procedures. Attributing the performance gap primarily to the presence of VQA co-training ignores these confounding variables. The paper does not perform a controlled experiment (e.g., fine-tuning the same base VLM with and without VQA data) to isolate this variable. The language should be softened to reflect that VQA co-training is *correlated* with better performance in this specific sample, rather than being a proven driver of retention.

Finally, the interpretation of the layerwise intent probing results (RQ4) over-extrapolates from the limitations of linear probes. The paper concludes that "answer-relevant signals peak in middle VLA layers but attenuate in upper layers," suggesting a specific bottleneck where knowledge is lost or suppressed. However, linear probes only measure linearly separable information. A drop in probe accuracy in upper layers could simply indicate that the information is encoded in a non-linear, task-specific, or distributed manner that is optimal for action generation but invisible to a linear classifier. The paper does not rule out the possibility that the information is still present but transformed. The conclusion should be restricted to the recoverability of information by linear probes, rather than making definitive claims about the "attenuation" or "loss" of the signal within the model's internal representations.
