---
action_items:
- id: a480b97c1ebe
  severity: writing
  text: In Section 5.3 (RQ3), the claim of a uniform '20-40 points' gap is an overgeneralization.
    Table 1 shows gaps varying from ~11 points (Color) to ~47 points (Emotion). Please
    qualify this claim to reflect the variance across categories.
- id: aab3063f45dd
  severity: writing
  text: In Section 5.3 (RQ2), the text states 'no evaluated VLA reaches above-random
    performance on Symmetry or Counting.' Table 1 shows SpatialVLA at 52% (Counting)
    and Xiaomi at 58% (Symmetry). While marginal, the absolute claim is factually
    contradicted. Please revise to 'no VLA demonstrates robust above-random performance'
    or acknowledge these exceptions.
- id: 5bfb30696a36
  severity: writing
  text: In Section 5.3 (RQ5), the text implies a strict performance separation between
    joint-trained and robotics-only models. Table 1 shows InternVLA-M1 (joint) scoring
    lower than OpenVLA (robotics) on Attribute (49% vs 51%). Please qualify the claim
    to reflect that this is a general trend with exceptions, not a definitive rule.
artifact_hash: b7bf68dc7049e64af55a4f743a5addf0de48270ccdf470df63d9da46224951a5
artifact_path: projects/PROJ-848-does-vla-even-know-the-basics-measuring/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T20:31:45.360408Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The paper makes several strong claims regarding the performance gaps between VLMs and VLAs and the specific capabilities of models on the Act2Answer benchmark. While the overall narrative is supported by the data, there are instances where the textual claims are slightly stronger or more absolute than the evidence in the tables permits.

Specifically, in Section 5.3 (RQ3), the authors state that VLMs exceed VLAs by "roughly 20-40 points." While this holds for many categories (e.g., Emotion: 95% vs 48%), it does not hold for others like Color, where the gap is often smaller (e.g., 100% vs 89% for InternVL vs OpenVLA is 11 points). The claim should be qualified to reflect the variance across categories.

More critically, in Section 5.3 (RQ2), the text asserts that "no evaluated VLA reaches above-random performance on Symmetry or Counting." This is factually incorrect based on Table 1. SpatialVLA achieves 52% on Counting, and Xiaomi-Robotics-R0 achieves 58% on Symmetry. While these scores are close to the 50% chance baseline (and likely within the statistical noise defined by $\Delta$ in the appendix), the absolute phrasing "no evaluated VLA" is contradicted by the reported numbers. The text should be revised to state that "no VLA demonstrates *robust* or *statistically significant* above-random performance" or to acknowledge the marginal exceptions.

Finally, the claim in RQ5 regarding the superiority of joint-training models is generally supported but presented as a uniform trend. The data shows that while Magma is a clear outlier, other joint-trained models like InternVLA-M1 perform comparably to or sometimes worse than robotics-only baselines in specific categories (e.g., Attribute). The text should avoid implying a strict dichotomy and instead emphasize the "trend" or "average" nature of the finding, as the data shows significant overlap.

These are primarily issues of precision in reporting rather than fundamental flaws in the scientific conclusions. Correcting the absolute phrasing to match the nuance of the data will improve the accuracy of the claims.
