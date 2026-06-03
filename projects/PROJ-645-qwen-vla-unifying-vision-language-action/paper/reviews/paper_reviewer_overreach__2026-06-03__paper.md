---
action_items:
- id: 54ec21dd07e9
  severity: science
  text: Temper the claim of 'zero-shot success rate on DOMINO dynamic manipulation'
    (Abstract, Sec 5.1.4). Clarify if pretraining data included dynamic object interactions,
    as the text states 'without any dynamic-manipulation fine-tuning' but does not
    explicitly detail dynamic priors in the data section.
- id: 4a71ab20f1d7
  severity: writing
  text: Qualify the 'across robot embodiments' generalization claim (Abstract, Intro).
    Real-world validation is limited to ALOHA; emphasize that cross-embodiment claims
    rely heavily on simulation data to avoid overclaiming physical hardware robustness.
- id: 85e689d5c80c
  severity: writing
  text: Avoid relying solely on average OOD success (76.9%) to characterize robustness
    (Abstract, Table 3). Highlight the lower Position Generalization score (53.8%)
    to provide a balanced view of limitations.
artifact_hash: 4317c2f95ff2f77ca9da4f22e56217afc73d1946ecdbafc6b1dfd103e809ccd5
artifact_path: projects/PROJ-645-qwen-vla-unifying-vision-language-action/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-03T04:45:25.881667Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

This review focuses on potential overreach in the manuscript's claims regarding generalization and capability. While the empirical results are strong, several assertions extend beyond the immediate evidence provided in the paper.

First, the abstract and Section 5.1.4 claim a "26.6% zero-shot success rate on DOMINO dynamic manipulation" achieved "without any dynamic-manipulation fine-tuning." Table 6 supports the performance metric against baselines. However, the pretraining data section (Sec 3.2) describes manipulation trajectories, egocentric data, and synthetic simulation, but does not explicitly confirm the inclusion of *dynamic* object interactions (e.g., moving targets during training) required to justify zero-shot dynamic handling. Attributing this solely to "spatial-to-kinematic priors" risks overclaiming the model's inherent ability to reason about dynamics without explicit training signals. Please clarify the nature of the pretraining data regarding dynamic scenes or temper the "zero-shot" claim if dynamic data was implicitly included.

Second, the title and abstract assert unification "across... Robot Embodiments." While Table 1 and 2 show strong simulation and ALOHA results, real-world validation is confined to the ALOHA platform. The claim of generalization across embodiments is primarily supported by simulation variants (WidowX, Panda, etc.). To avoid overreach, the text should qualify that physical embodiment generalization is demonstrated primarily on ALOHA, with broader claims resting on simulation benchmarks.

Finally, the abstract cites "76.9% average OOD success in real-world ALOHA experiments." Table 3 reveals significant variance, with Position Generalization at 53.8%. Presenting the average without context obscures specific failure modes. Reporting the range or highlighting the weaker category provides a more honest assessment of the model's limitations.

Addressing these points will align the manuscript's narrative more closely with the scope of the experimental evidence.
