---
action_items:
- id: ef3b3cb15562
  severity: science
  text: The paper describes training on real-world videos (SpatialVID, RealEstate10K,
    Sekai, DL3DV) and game data without explicit mention of IRB approval, informed
    consent, or data usage licenses. Given the use of potentially identifiable human
    subjects in real-world footage, a dedicated 'Data Ethics and Privacy' subsection
    is required to detail consent mechanisms, anonymization procedures, and compliance
    with relevant data protection regulations (e.g., GDPR).
- id: 487f1f705a53
  severity: science
  text: The 'Event Instruction Tuning' and 'Interactive World Model' capabilities
    allow for the generation of photorealistic, controllable video sequences. The
    paper lacks a 'Dual-Use and Misuse' discussion addressing the potential for generating
    deepfakes, disinformation, or non-consensual intimate imagery. A mitigation strategy
    (e.g., watermarking, safety filters, or usage restrictions) must be explicitly
    described.
- id: d04b27f06b6c
  severity: writing
  text: The evaluation section relies on a VLM (Gemini-3.1-Pro) for artifact detection
    and human preference studies. The paper does not disclose the demographic composition
    of the human evaluators or the safety protocols used to prevent exposure to harmful
    content during the study. A brief statement on human subject protection and evaluator
    safety is necessary.
artifact_hash: dd358f57d42e68a3445f4b34d5b2202a60d20e2d68878dcf007801dde467660f
artifact_path: projects/PROJ-717-dreamx-world-1-0-a-general-purpose-inter/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T05:18:52.307089Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript presents a sophisticated interactive world model but lacks critical safety and ethical disclosures required for a system capable of generating photorealistic, controllable video content.

First, regarding **data privacy and consent**, Section 2.2 ("Real-world and Game Data") lists the ingestion of real-world video datasets (SpatialVID, RealEstate10K, Sekai, DL3DV). The paper fails to address whether these datasets were collected with informed consent from individuals appearing in the footage, particularly given the potential for identifying faces or private locations. There is no mention of IRB/IACUC approval for the data curation process or specific anonymization techniques applied to the training data. A dedicated subsection detailing data provenance, consent status, and compliance with privacy regulations (e.g., GDPR) is mandatory.

Second, the **dual-use risk** is significant. The system's ability to generate "photorealistic" videos with precise camera control and "composable events" (Section 2.4) creates a high risk for misuse in generating deepfakes, disinformation, or non-consensual intimate imagery. The paper currently treats these capabilities as purely technical achievements without acknowledging the societal harm they could facilitate. The authors must include a "Safety and Misuse" discussion outlining potential misuse scenarios and the specific mitigation strategies employed (e.g., output watermarking, safety classifiers, or restricted access to the model weights).

Finally, the **human evaluation** protocol described in Section 4.4 ("Human Preference Study") lacks ethical safeguards. The paper does not specify how evaluators were protected from exposure to potentially harmful or disturbing generated content, nor does it detail the demographic diversity of the evaluators or the consent process for their participation. Standard ethical review procedures for human subjects research should be referenced or described.

These omissions prevent the paper from meeting the ethical standards required for publication in a venue focused on general-purpose AI systems.
