---
action_items:
- id: 8988aacccd86
  severity: science
  text: Add explicit dual-use risk assessment for chemistry/biology systems (MOOSE-Chem,
    BioPlanner, CRISPR-GPT). Current discussion in Sec 5.4.6 mentions cross-domain
    risks but lacks concrete safety protocols or biosecurity guardrails for autonomous
    experimentation in sensitive domains.
- id: add8ea9ea223
  severity: writing
  text: Clarify accountability framework for AI-generated research claims. Section
    5.5.5 discusses governance but does not specify who bears responsibility (authors,
    institutions, tool developers) when AI-generated experiments produce erroneous
    or harmful results.
- id: 640623b73c11
  severity: writing
  text: Add data privacy and consent considerations for research involving human subjects
    or sensitive data. The paper does not address IRB/IACUC requirements or data protection
    when AI systems process research participant information.
- id: 883d5824713c
  severity: science
  text: Strengthen discussion of AI-assisted peer review manipulation risks (Sec 5.3.1).
    While prompt injection is noted, the paper should explicitly recommend disclosure
    requirements and audit mechanisms for venues using AI in review workflows.
artifact_hash: 406e68578ff634bb909200355e48bd438ba9dc41c31d75ef24170dcb14dc58cd
artifact_path: projects/PROJ-602-https-arxiv-org-abs-2605-18661/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-08T05:10:42.091914Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

This survey makes important contributions to understanding AI-assisted research across the complete lifecycle, and appropriately acknowledges many governance challenges. However, from a safety and ethics lens, several critical gaps remain:

**Dual-Use Risks (Section 5.4.6)**: The paper discusses chemistry (MOOSE-Chem), biology (BioPlanner, CRISPR-GPT), and medical AI Scientist systems but does not provide concrete safety protocols for autonomous experimentation in these sensitive domains. Autonomous chemistry/biology research carries inherent biosecurity and safety risks that require explicit guardrails, not just general "cross-domain generalization" concerns.

**Accountability Framework**: Section 5.5.5 discusses governance and disclosure but lacks specificity on liability chains. When an AI system generates experimental claims that turn out to be erroneous or cause harm, who bears responsibility—the paper author, the institution, the tool developer? This must be clarified for responsible deployment.

**Human-Subjects Research**: The paper does not address IRB/IACUC requirements or data privacy protections when AI systems process research involving human participants. This is a significant gap for systems that may automate literature review, data analysis, or experimental design in clinical or behavioral research.

**Peer Review Integrity**: Section 5.3.1 notes that 15.8% of ICLR 2024 reviews were AI-assisted and that prompt injection can manipulate scores, but does not recommend concrete venue policies. Given that LLMs misclassify 95.8% of rejected papers as acceptable, stronger disclosure and audit requirements should be proposed.

**Research Misconduct at Scale**: The paper notes AI can generate papers for ~$15 each (Section 1), raising concerns about literature pollution. While "human-governed collaboration" is recommended, the paper should explicitly address how to prevent AI from being used to flood venues with unverified or fraudulent work.

These issues are addressable through manuscript revisions and do not require new experiments, but they are essential for responsible publication of this survey.
