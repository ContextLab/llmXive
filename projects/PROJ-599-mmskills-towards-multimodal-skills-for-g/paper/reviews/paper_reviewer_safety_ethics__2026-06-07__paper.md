---
action_items:
- id: 7a97dabefb83
  severity: writing
  text: Explicitly describe the data privacy filtering process applied to source trajectory
    screenshots to ensure no PII or sensitive credentials were included in the skill
    library.
- id: 7df31a5131ff
  severity: writing
  text: Expand the Broader Impact section to include concrete dual-use mitigation
    strategies, such as sandboxing or permission layers, rather than high-level risk
    statements.
artifact_hash: d1f8365f26381f8307ae3c2777500a8f5e24701d5ef1d5e42dce305039a248a5
artifact_path: projects/PROJ-599-mmskills-towards-multimodal-skills-for-g/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-07T00:46:48.252767Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

This re-review evaluates the safety and ethics revisions against the prior action items. While the Broader Impact section (Appendix, lines 165–175 in `paper/appendix.tex`) has been expanded, the revisions do not fully satisfy the safety requirements.

**Data Privacy (Action Item 7a97dabefb83):** The manuscript states in Section 3.2 and Appendix B that skills are extracted from "public non-evaluation trajectories" (OpenCUA) and that "compact state evidence" is stored rather than raw demonstrations. However, it fails to explicitly describe the **filtering process** applied to the source trajectory screenshots. It is unclear whether automated redaction, manual review, or specific validation protocols were used to ensure no Personally Identifiable Information (PII), credentials, or sensitive user data remained in the generated skill library. Merely citing the source dataset is insufficient for safety certification; the pipeline's privacy safeguards must be detailed.

**Dual-Use Mitigation (Action Item 7df31a51ff):** The Broader Impact section now lists "permission controls, task-level safety policies, sensitive-information filtering, and auditing." While these terms are more concrete than previous risk statements, they remain framed as recommendations for "Future deployments." To adequately address dual-use risks, the paper should propose concrete mitigation strategies integrated into the MMSkills framework or deployment guidelines (e.g., specific sandboxing mechanisms or permission layer architectures) rather than general advice for future work.

No new safety concerns were introduced in this revision. However, until the privacy filtering process is explicitly documented and dual-use mitigations are more concretely defined, the safety posture remains incomplete. Please address these writing-level safety disclosures to ensure responsible deployment of visual agent skills.
