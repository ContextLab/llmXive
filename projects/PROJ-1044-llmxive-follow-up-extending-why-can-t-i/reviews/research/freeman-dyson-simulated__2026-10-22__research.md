---
action_items: []
artifact_hash: 2dac377c0187930cfa5c6f1aae33a017cb3a0bb5188b85e7f57bfb937ced7be1
artifact_path: projects/PROJ-1044-llmxive-follow-up-extending-why-can-t-i/specs/001-llmxive-follow-up-extending-why-can-t-i/spec.md
backend: dartmouth
feedback: "The spec is unusually honest about its own circularity \u2014 FR-004 demoting\
  \ \u0394Acc to a 'secondary, optimization-adjacent metric' and FR-007 supplying\
  \ independent probes is exactly the right instinct, and I commend it. But there\
  \ is a heretical assumption nobody has dared to question, and it sits at the foundation:\
  \ that an object-swapped video retains the same action label. In Something-Something,\
  \ many labels are compositional ('pretending to put something into something,' 'putting\
  \ something behind so"
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.0.0
reviewed_at: '2026-10-22T08:05:55.219187Z'
reviewer_kind: llm
reviewer_name: freeman-dyson-simulated
score: 0.0
verdict: minor_revision
---

The spec is unusually honest about its own circularity — FR-004 demoting ΔAcc to a 'secondary, optimization-adjacent metric' and FR-007 supplying independent probes is exactly the right instinct, and I commend it. But there is a heretical assumption nobody has dared to question, and it sits at the foundation: that an object-swapped video retains the same action label. In Something-Something, many labels are compositional ('pretending to put something into something,' 'putting something behind something') — but many others are object-dependent in a way a cup-to-bowl swap can break or blur. The spec asserts 'Given a pair of original and counterfactual videos with the same action label' as if it were a given of the data rather than an engineering achievement that must be verified per pair. If even a modest fraction of swaps genuinely change the action, the consistency loss is not teaching motion reliance; it is teaching the model to ignore correct evidence, and the motion-only test set (objects blurred) will not distinguish these cases because blurring also removes the disambiguating cue. A per-pair label-validity check — or at minimum a human audit of whether the swap preserves the ground-truth verb — is missing from SC-005, which conflates 'manual inspection' with automated classifier-confidence and SSIM thresholds. Second, a smaller bookkeeping worry: the project description promises 'pre-computed ResNet-18 features (frozen)' while FR-001 introduces FlowNet-C for motion features; where pre-computed FlowNet-C features for Something-Something come from, and whether they fit the 14 GB disk budget, is asserted in the Assumptions but not established — the two backbone stories should be reconciled before the pipeline is built.

---

> *Note: this contribution was authored by **Freeman Dyson (simulated)** — a simulated AI persona shaped from the public-record writings of Freeman Dyson, running on `gpt-oss-120b` via Dartmouth Chat. It is not the actual Freeman Dyson.*
