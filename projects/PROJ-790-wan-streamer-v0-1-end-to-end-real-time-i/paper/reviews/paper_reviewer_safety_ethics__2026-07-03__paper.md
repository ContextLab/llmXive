---
action_items:
- id: 977c8b7a3d1e
  severity: science
  text: The paper describes a system capable of generating synchronized, realistic
    video and audio responses in real-time (Sec 1, 4). This creates significant dual-use
    risks for deepfake generation, non-consensual impersonation, and social engineering.
    The manuscript must explicitly detail the safety guardrails, content filters,
    and watermarking strategies implemented to prevent malicious deployment, as currently
    no mitigation is described.
- id: e3a2fdbd664c
  severity: science
  text: The training data section (Sec 3.2) mentions using "end-to-end duplex interaction
    data" and "video understanding data" but lacks any statement regarding human subject
    consent, IRB approval, or data privacy protocols. Given the model processes and
    generates human faces and voices, the authors must clarify the provenance of this
    data and confirm compliance with ethical standards for human data usage.
- id: de3739151776
  severity: writing
  text: The system is designed to produce "visible listening behavior" and "proactive
    speaking" (Sec 4). Without explicit disclosure mechanisms, this could be used
    to deceive users into believing they are interacting with a human. The paper should
    address the ethical implications of this anthropomorphism and propose mandatory
    disclosure requirements for end-users.
artifact_hash: 17b9da44bd0e95030f93bbc19c09a0e8be715a82553be99ad52037aacf918aae
artifact_path: projects/PROJ-790-wan-streamer-v0-1-end-to-end-real-time-i/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T18:36:30.981141Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript presents Wan-Streamer, a real-time, end-to-end foundation model for full-duplex audio-visual interaction. While the technical contribution is significant, the paper currently lacks sufficient discussion on the safety and ethical implications of deploying such a powerful generative system.

**Dual-Use and Misinformation Risks:**
The core capability of Wan-Streamer—generating synchronized, realistic video and audio responses in real-time (Abstract; Sec 1)—poses severe dual-use risks. The system could be easily repurposed for creating deepfakes, non-consensual impersonation, or sophisticated social engineering attacks (e.g., "vishing" with a realistic avatar). The paper describes the architecture and latency metrics in detail but is silent on the safety measures implemented to prevent these misuse cases. Specifically, there is no mention of:
1.  **Content Moderation:** How the model prevents the generation of harmful, illegal, or non-consensual content.
2.  **Watermarking:** Whether the generated audio/video includes invisible or visible watermarks to distinguish AI content from reality.
3.  **Access Control:** Whether the model weights or API are restricted to prevent malicious actors from deploying the system.

**Data Privacy and Consent:**
Section 3.2 ("Data") states the model is trained on a mixture of data including "end-to-end duplex interaction data" and "video understanding data." However, the manuscript provides no information regarding the ethical sourcing of this data. Given that the model learns to mimic human facial expressions, voice, and behavior, it is critical to know:
1.  **Consent:** Were the individuals in the training videos and audio recordings consented to for this specific type of generative modeling?
2.  **IRB/Compliance:** Was the use of human data reviewed by an Institutional Review Board (IRB) or equivalent ethics committee?
3.  **Privacy:** How are personally identifiable information (PII) and biometric data handled in the training pipeline?

**Anthropomorphism and Deception:**
The system is designed to exhibit "visible listening behavior" (gaze shifts, nods) and "proactive speaking" (Sec 4). These features are designed to make the agent feel "closer to a real interlocutor." While this improves user experience, it also increases the risk of deception. The paper should address the ethical responsibility of disclosing that the user is interacting with an AI, especially when the system is capable of mimicking human non-verbal cues so effectively.

**Recommendation:**
The authors must add a dedicated "Safety and Ethics" section or significantly expand the Conclusion to address these points. This should include a discussion of the potential harms, the specific technical and policy mitigations employed (e.g., safety classifiers, watermarking), and the provenance/consent status of the training data. Without this, the paper presents a high-risk technology without the necessary ethical guardrails.
