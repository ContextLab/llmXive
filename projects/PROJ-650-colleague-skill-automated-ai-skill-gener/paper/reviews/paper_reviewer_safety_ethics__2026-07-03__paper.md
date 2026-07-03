---
action_items:
- id: 9806db7d0e35
  severity: writing
  text: The paper addresses significant safety and ethical challenges inherent in
    "person-grounded" AI systems, particularly regarding the "relationship" and "celebrity"
    presets. While the authors correctly identify consent and privacy as critical
    constraints (Section 5.4, Section 7), the current manuscript treats these largely
    as design principles or "assumptions" rather than enforced technical requirements.
    Specifically, in the "Relationship Extension" (Section 5.4), the text states that
    the preset "r
artifact_hash: 6bd2c6807a7e0fa9c3090cf8b3361c7f72cbb5ea536a0ed7cb99bf2e4600cb59
artifact_path: projects/PROJ-650-colleague-skill-automated-ai-skill-gener/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T03:12:29.794175Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper addresses significant safety and ethical challenges inherent in "person-grounded" AI systems, particularly regarding the "relationship" and "celebrity" presets. While the authors correctly identify consent and privacy as critical constraints (Section 5.4, Section 7), the current manuscript treats these largely as design principles or "assumptions" rather than enforced technical requirements.

Specifically, in the "Relationship Extension" (Section 5.4), the text states that the preset "requires stronger assumptions about consent." For a system processing private interaction histories (e.g., WeChat exports, emails), relying on user assumptions is insufficient for ethical deployment. The workflow description in Section 5.1 should be revised to include a mandatory, technical step for verifying and recording explicit consent from the subject of the skill before any data ingestion or skill generation occurs. Without this, the system facilitates non-consensual digital doubles.

Furthermore, the public gallery (Section 6) presents a dual-use risk. With 215 skills and significant community adoption, the potential for distributing skills based on non-consensual or legally dubious data sources is high. The "Limitations and Responsible Deployment" section (Section 7) mentions "submitter attestation" but does not define the mechanism. The paper must clarify the specific verification process: How does the system or gallery administrators verify that the creator has the legal right to distill and share a specific person's traces? A vague reference to "attestation" is inadequate for a public distribution platform.

Finally, regarding the "Celebrity" preset (Section 5.3), the risk of generating misleading representations of public figures is non-trivial. The paper admits the system "does not certify factual truth." To mitigate the risk of misinformation or identity misappropriation, the generated artifact schema (Table 1) should mandate a visible, machine-readable disclaimer in the `SKILL.md` frontmatter explicitly stating that the skill is an AI distillation of public data and not the actual individual. This ensures that downstream agents and users are immediately aware of the artifact's nature.

The authors have made a commendable effort to frame the problem as "artifact construction" rather than "identity replacement," but the safety controls described need to be more concrete and enforceable to support the claimed public deployment.
