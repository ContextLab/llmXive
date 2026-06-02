---
action_items:
- id: c000d926a058
  severity: writing
  text: Add explicit ethics statement regarding IRB approval or informed consent for
    the three human gold-medal experts used in IMO/USAMO evaluation.
- id: f28f296a1e2f
  severity: writing
  text: Include a discussion on dual-use risks and responsible release policies for
    the SU-01 model, particularly given its generalization to Chemistry and Biology
    domains.
artifact_hash: 6b23039f76721ac00eaa6c408647f026893a62ad0f423ddd12fdde82e2327635
artifact_path: projects/PROJ-581-https-arxiv-org-abs-2605-13301/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-02T13:50:20.660781Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript presents significant safety and ethics considerations that require clarification before acceptance. First, regarding human subject involvement: Table 3 and the Appendix (`app:evaluation-details`) explicitly state that "IMO and USAMO use ProofBench-style grading with three gold-medal experts independently scoring {0,1,6,7}". This constitutes human subjects research. The paper currently lacks an explicit statement regarding Institutional Review Board (IRB) approval, ethical oversight, or informed consent from these experts. Standard academic ethics require disclosure of whether compensation was provided and if ethical guidelines were followed, even for expert evaluation. Please add a dedicated ethics statement clarifying IRB status or consent procedures for this human evaluation component.

Second, concerning dual-use risks: While the primary focus is Olympiad mathematics, Section `sec:exp-results` and Table 1 (`tab:verifiable-single-pass`) report performance on "FrontierScience-Olympiad," which includes Physics, Chemistry, and Biology. The abstract further claims "generalizing to broader scientific domains." Advanced reasoning models capable of scientific discovery carry inherent dual-use risks (e.g., automated design of hazardous materials, pathogens, or cyber-attack strategies). The paper does not discuss responsible AI deployment, safety filters, or usage policies associated with the model release (linked in the frontmatter). A discussion on potential misuse, risk mitigation strategies, and responsible release protocols is strongly recommended before public dissemination.

Finally, regarding data provenance: The SFT and RL data sources (e.g., AoPS, HuggingFace datasets like Nemotron and OpenCodeReasoning) appear to be publicly available. However, you must verify that all dataset citations align with their respective usage licenses and terms of service. Ensure no private or sensitive data was inadvertently included in the 338K trajectory mixture. Addressing these points will align the manuscript with standard research ethics guidelines and safety norms for AI development.
