---
action_items:
- id: 813d8fbcde73
  severity: writing
  text: Add a dedicated 'Ethical Considerations' section addressing dual-use risks
    (e.g., automated malware, vulnerability exploitation) beyond technical governance.
- id: 7d7f4606d034
  severity: writing
  text: Include a formal Conflict of Interest statement given the mix of industry
    (OpenAI, Anthropic, Microsoft) and academic authors.
- id: ef9a100915ca
  severity: science
  text: Expand Section 5.1.4 to explicitly reference biosecurity and chemical safety
    protocols for self-driving labs synthesizing compounds.
artifact_hash: cbd4e8e17c331b3d11d6d3473a72ca30389ded91296199ea84247ea30361db9d
artifact_path: projects/PROJ-606-https-arxiv-org-abs-2605-18747/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-02T05:26:49.328899Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

This survey provides a comprehensive taxonomy of code-centric agent harnesses. However, from a safety and ethics perspective, the treatment of risk is primarily technical rather than societal. Section 5.2.5 (e002) discusses "Human-in-the-Loop Safety and Accountability" but frames it as a governance mechanism (sandboxing, permission tiers) rather than addressing broader dual-use implications. Autonomous coding agents capable of repository-level modification (Section 5.1.1, e003) pose significant dual-use risks, including automated malware generation or exploitation of vulnerabilities, which should be explicitly analyzed. The paper cites safety tools like AutoSafeCoder and Codex Security but does not critically evaluate their limitations against adversarial use cases. Additionally, the paper lacks a formal "Conflict of Interest" statement despite numerous authors from industry (OpenAI, Anthropic, Microsoft, Meta) and academia. This is particularly relevant given the discussion of production systems (Cursor, OpenAI Operator) in Section 5.1.1. Section 5.1.5 (e003) mentions privacy risks in personalization but does not detail data handling protocols for the survey itself. A dedicated "Ethical Considerations" section is recommended to address misuse potential, workforce displacement, and transparency in industry-academia collaborations. The current safety discussion is sufficient for technical governance but insufficient for ethical oversight of the technology's deployment. Furthermore, while Section 5.1.3 (e003) covers embodied agents, it should explicitly reference physical safety standards (ISO/IEC) for robotic control to ensure real-world harm mitigation is considered. Section 5.1.4 (e003) on scientific discovery mentions self-driving labs synthesizing compounds; this requires specific ethical disclosure regarding biosecurity and chemical safety protocols, which is currently absent.
