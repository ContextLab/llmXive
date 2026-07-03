---
action_items:
- id: b6b7850fdc17
  severity: writing
  text: The paper describes training on healthcare robotic surgery data (398K conversations,
    2.2M images) and dense pedestrian localization (208K images, 5.6M boxes) without
    explicit mention of IRB approval, patient consent, or PII redaction protocols.
    Add a dedicated subsection in Section 4 (Data) detailing the ethical review process,
    consent mechanisms, and specific anonymization techniques used for these sensitive
    datasets.
- id: 6866ed48734b
  severity: writing
  text: The 'Healthcare robotic surgery' dataset (Section 4.1) and 'SDG-Warehouse'
    safety scenarios (Appendix E.5) involve high-stakes physical interactions. The
    paper lacks a discussion on the potential for these models to be misused to generate
    deceptive safety-critical training data or to simulate hazardous scenarios for
    malicious physical AI development. Include a 'Dual-Use and Safety' discussion
    in the Conclusion or Introduction addressing these risks.
- id: 91954da8148a
  severity: writing
  text: The 'Cosmos-HUE' benchmark (Section 7) relies on VLM-generated questions and
    human annotation. The paper does not specify the safety guidelines provided to
    human annotators or the VLMs when evaluating potentially harmful or physically
    dangerous generated content (e.g., collisions, falls). Clarify the safety protocols
    and exclusion criteria used during the annotation and evaluation phases.
artifact_hash: 868016604b8d9a3bb37ad3c74cf4a71a551a99c22f54a694c5fb583a974a744e
artifact_path: projects/PROJ-665-https-arxiv-org-abs-2606-02800/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T12:39:04.653918Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript presents a comprehensive technical framework for Cosmos 3, a multimodal world model. From a safety and ethics perspective, the paper is largely descriptive of the model's capabilities but lacks sufficient detail regarding the ethical handling of sensitive data and the potential for dual-use risks.

**Data Privacy and Consent:**
In Section 4.1 ("Reasoner Data"), the authors mention using a "Healthcare robotic surgery" dataset comprising 398K multi-turn conversations and 2.2M images, including exocentric, egocentric, and console views. Similarly, the "Smart infrastructure" section notes "Dense pedestrian localization" with 5.6M person boxes. While the paper briefly mentions "PII redacted" in passing, it does not provide a rigorous account of the ethical review process. There is no mention of Institutional Review Board (IRB) approval, patient consent forms, or the specific algorithms used for anonymization (e.g., face blurring, voice anonymization) for the healthcare data. Given the sensitivity of medical and surveillance data, the absence of a dedicated ethics statement or detailed data governance protocol is a significant omission.

**Dual-Use and Physical Safety:**
The paper emphasizes the model's ability to simulate physical interactions, including "forklift-human near-miss," "fire," and "collision" scenarios (Appendix E.5, SDG-Warehouse). While intended for safety training, these capabilities present dual-use risks. The model could potentially be used to generate realistic but deceptive training data for malicious physical AI agents or to simulate hazardous scenarios for harmful purposes. The manuscript currently lacks a "Safety and Dual-Use" discussion section that acknowledges these risks and outlines any mitigation strategies (e.g., watermarking, access controls, or refusal mechanisms for harmful prompts).

**Evaluation Safety:**
The Cosmos-HUE benchmark (Section 7) evaluates physical plausibility and safety. The methodology relies on VLMs and human annotators to judge generated videos. The paper does not describe the safety protocols in place for human annotators who might be exposed to generated content depicting accidents, violence, or medical procedures. Furthermore, it does not specify if the VLMs used for question generation were constrained to avoid generating harmful or unsafe evaluation queries.

To address these concerns, the authors should add a subsection in the Data section detailing consent and anonymization, include a discussion on dual-use risks in the Conclusion, and clarify safety protocols for the evaluation phase.
