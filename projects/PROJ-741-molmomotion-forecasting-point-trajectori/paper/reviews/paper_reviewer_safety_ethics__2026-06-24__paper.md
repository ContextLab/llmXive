---
action_items:
- id: 9f6227d3c399
  severity: writing
  text: "Add a dedicated Ethics & Safety section that discusses consent for the source\
    \ videos, privacy safeguards for any identifiable humans, and the potential dual\u2011\
    use of 3D motion forecasting (e.g., surveillance, weaponizable robot planning)."
- id: 8221c18fe9ba
  severity: writing
  text: "Provide a clear data\u2011usage statement confirming that all internet videos\
    \ used in MolmoMotion\u20111M were publicly available under licenses that permit\
    \ redistribution and that any personal data was removed or blurred; if not, obtain\
    \ appropriate permissions or exclude such clips."
- id: fd125fd9a98b
  severity: science
  text: "Include a risk\u2011mitigation plan outlining how the released model and\
    \ dataset could be misused (e.g., generating realistic manipulation videos for\
    \ disinformation or aiding malicious autonomous systems) and propose technical\
    \ or policy controls (e.g., usage licenses, watermarking of generated content)."
- id: eff5071234bf
  severity: writing
  text: "Document any IRB or equivalent ethical review that was performed for the\
    \ annotation pipeline, especially when human subjects appear in the source videos,\
    \ and describe steps taken to anonymize or de\u2011identify individuals."
- id: 8c661df541d4
  severity: writing
  text: "Consider adding a usage\u2011policy clause in the model\u2019s repository\
    \ (e.g., on HuggingFace) that restricts deployment in high\u2011risk domains without\
    \ additional safety evaluation."
artifact_hash: 43d44b1b7f12aef158eaf0787875484ea72c6860cf8af3c796e4579ec99e55ab
artifact_path: projects/PROJ-741-molmomotion-forecasting-point-trajectori/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-24T15:40:05.767394Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript focuses on a novel technical problem—goal‑conditioned 3D point motion forecasting—and presents a large‑scale dataset, model, and downstream applications. From a safety and ethics perspective, several concerns arise that are not sufficiently addressed in the current text.

**Privacy and consent** – MolmoMotion‑1M is built from ~1.16 M public videos sourced from platforms such as YouTube, EgoDex, HD‑EPIC, and others. Many of these clips contain identifiable humans (e.g., hands, faces, by‑standers). The paper does not describe any systematic process for verifying that the videos are released under licenses that allow 3D reconstruction and redistribution, nor does it discuss steps taken to anonymize or blur personal identifiers. Without such safeguards, the dataset could violate privacy expectations and potentially breach platform terms of service.

**Human‑subject research oversight** – The annotation pipeline involves extracting fine‑grained 3D trajectories of objects that are often manipulated by people. This constitutes a form of secondary analysis of human‑subject data. The manuscript should state whether an Institutional Review Board (IRB) or equivalent ethical review was obtained, and if not, justify why the work is exempt. Explicitly describing any de‑identification procedures would strengthen compliance.

**Dual‑use and misuse potential** – Predicting future 3D object motion from a single frame and a language instruction can be repurposed for malicious ends: (1) enhancing surveillance systems to anticipate human actions, (2) enabling autonomous weapons to plan object‑level interactions, and (3) providing high‑quality motion cues for deep‑fake video generation. While the authors briefly mention downstream benefits (robotics, video synthesis), they do not discuss these risks or propose mitigations (e.g., licensing restrictions, watermarking of generated videos, or usage‑policy enforcement).

**Data bias and fairness** – The dataset aggregates videos from a variety of domains, but the paper does not analyze demographic or contextual biases (e.g., over‑representation of certain object types, cultural settings, or activity classes). Such biases could affect downstream robot policies or video generators, leading to uneven performance across environments.

**Safety in downstream robotics** – The transfer experiments to robot manipulation are evaluated only in simulation or limited real‑world clips. Deploying a model that predicts object trajectories without rigorous safety validation could cause unsafe robot behavior (e.g., collisions). The authors should outline safety testing protocols or fail‑safe mechanisms for real‑world deployment.

**Recommendations** – The authors should add a dedicated Ethics & Safety section covering the points above, provide a data‑usage statement confirming licensing and anonymization, disclose any IRB review, and outline a risk‑mitigation strategy (usage licenses, watermarking, safety testing). Addressing these issues will bring the work into alignment with community standards for responsible AI research.
