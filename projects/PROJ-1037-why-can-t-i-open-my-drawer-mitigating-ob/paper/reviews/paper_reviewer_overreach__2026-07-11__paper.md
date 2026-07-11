---
action_items:
- id: b1f452041a49
  severity: writing
  text: The paper presents a strong diagnostic framework for object-driven shortcuts
    in Zero-Shot Compositional Action Recognition (ZS-CAR) and proposes a method (RCORE)
    that empirically reduces these shortcuts on two specific benchmarks. However,
    the rhetoric occasionally exceeds the scope of the demonstrated evidence, particularly
    in the strength of the claims made in the contributions list and conclusion. First,
    the contributions section (Introduction) claims the authors "prove that our approach
    miti
artifact_hash: f098ae707662ea7ce696ff8b8606006fdddb80c25be82361ec114d13c9a397ed
artifact_path: projects/PROJ-1037-why-can-t-i-open-my-drawer-mitigating-ob/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-11T04:11:55.180885Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper presents a strong diagnostic framework for object-driven shortcuts in Zero-Shot Compositional Action Recognition (ZS-CAR) and proposes a method (RCORE) that empirically reduces these shortcuts on two specific benchmarks. However, the rhetoric occasionally exceeds the scope of the demonstrated evidence, particularly in the strength of the claims made in the contributions list and conclusion.

First, the contributions section (Introduction) claims the authors "prove that our approach mitigates co-occurrence biases." The evidence provided in Section 5 consists of empirical metrics (FSP/FCP) showing a reduction in shortcut reliance on Sth-com and EK100-com. In the context of machine learning, "proof" is a mathematical term reserved for theoretical guarantees, whereas the paper offers empirical validation. This is a classic overreach of language strength; the claim should be softened to "demonstrate" or "show" to accurately reflect the nature of the experimental results.

Second, the Abstract and Conclusion generalize the findings to "across datasets" and "across backbones" without sufficient qualification. The experimental section (Section 5) validates the method exclusively on Sth-com and the newly introduced EK100-com, using CLIP-B/16 and InternVideo2-B/14 (and one 1B variant). While these are significant benchmarks, the phrasing implies a universality that extends to any dataset or model architecture, which is not supported by the data. The claim should be scoped to the specific datasets and model families tested, or the authors should acknowledge the limitation that generalization to other domains (e.g., egocentric vs. third-person, or other video foundation models) remains untested.

Finally, the Conclusion frames the work as moving the field "toward more reliable verb–object compositional reasoning." While the method improves performance, the paper's own failure analysis (Appendix, Tables on failure modes) reveals that significant errors persist (e.g., high confusion between opposite verbs like "opening" and "closing" on unseen compositions). The conclusion should be more nuanced, acknowledging that while the proposed method mitigates specific shortcuts, the broader challenge of reliable reasoning in sparse compositional settings is not fully resolved. This would provide a more honest assessment of the current state of the art.
