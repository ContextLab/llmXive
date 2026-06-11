---
action_items:
- id: a731b1637da0
  severity: writing
  text: Add a dedicated Ethics Statement detailing IRB/consent protocols for any user
    data used to train personal models or simulators.
- id: 515961fec201
  severity: writing
  text: Discuss dual-use risks of 'Million Personal Models', specifically regarding
    impersonation, manipulation, and privacy leakage from adapters.
- id: c9ae102514f3
  severity: writing
  text: Clarify safety guardrails in MinT infrastructure (Section 7) to prevent serving
    harmful or misaligned personal model instances.
- id: 294f90f517b9
  severity: writing
  text: Address ethical implications of 'User Simulators' (Section 6) that model real
    group-opinion dynamics, including potential for social engineering.
artifact_hash: 98f7fcdee505c1b0d734c7251a396631b218366acf62d66b7a26c51efa8d758b
artifact_path: projects/PROJ-655-https-arxiv-org-abs-2606-02437/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-11T21:56:29.121712Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

This paper proposes a framework for scaling Parameter-Efficient Fine-Tuning (PEFT) to support "Million Personal Models" (Abstract, Section 1). While technically ambitious, the manuscript currently lacks necessary safety and ethical disclosures regarding the deployment of persistent, personalized AI agents at population scale.

**Privacy and Consent (Section 4):**
The core proposal involves storing "memories, preferences, skills" in adapters (Section 4, "Personal Models for Individuals"). This implies the continuous collection and storage of sensitive user behavioral data. The paper does not mention IRB approval, informed consent mechanisms, or data anonymization strategies for this data. If the "DishNameBenchmark" or "EvoBot" experiments (Section 6, Table 3) involve real human behavioral data, explicit ethical clearance must be documented.

**Dual-Use and Misuse Risks (Section 5-6):**
The capability to create persistent, personalized agents at scale introduces significant dual-use risks. "Personal models" could be exploited for identity impersonation, targeted manipulation, or creating convincing deepfake behaviors. Section 6 ("User Simulators and Agent Environments") explicitly discusses modeling "real group-opinion dynamics" (Table 3, EvoBot). This capability carries high risks of social engineering or astroturfing if deployed without governance. A risk assessment section is required to address these potential harms.

**Infrastructure Safety (Section 7):**
The MinT infrastructure (Section 7, "Infrastructure for PEFT Populations") manages adapter lifecycle and serving but does not describe safety guardrails. There is no discussion of how the system prevents serving adapters trained on harmful data or optimized for malicious objectives. Mechanisms for revocation or safety filtering of personal models should be described.

To proceed, the authors must address these gaps in a dedicated ethics section, ensuring compliance with standard AI safety research practices.
