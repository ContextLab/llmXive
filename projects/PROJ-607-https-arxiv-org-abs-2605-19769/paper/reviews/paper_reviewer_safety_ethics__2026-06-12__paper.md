---
action_items:
- id: 5f9d6f09067a
  severity: writing
  text: Add explicit IRB approval statement or ethics exemption regarding human annotators
    mentioned in Section 4.1, including consent and compensation details.
- id: f44c77594806
  severity: writing
  text: Include a Dual-Use and Responsible Release discussion addressing potential
    misuse of the agent framework for unauthorized automation or malicious tasks.
- id: fd8d8b6a3407
  severity: writing
  text: Explicitly confirm that all benchmark data (e.g., zotero.sqlite, commissions.xlsx)
    is synthetically generated and contains no real user PII in the Data Availability
    or Limitations section.
artifact_hash: 0d09bbe6836d7c3ba38dc0386a722fbaec7b727145cadfcb8e187e60eeb63fee
artifact_path: projects/PROJ-607-https-arxiv-org-abs-2605-19769/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-12T11:20:48.464726Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

This review focuses exclusively on safety, ethics, and responsible conduct regarding the OpenComputer framework.

**Human Subjects and IRB Compliance**
In Section 4.1 ("Analysis"), the authors state: "we sample 120 tasks and send the same completed trajectories to human annotators." This implies human participation in the research process. However, the manuscript lacks an explicit statement regarding Institutional Review Board (IRB) approval or an ethics exemption determination. For NeurIPS and similar venues, any interaction with human annotators requires documentation of informed consent, compensation standards, and ethical oversight. Please add a dedicated ethics statement in the paper or Appendix confirming compliance with local regulations and detailing how annotator data was handled (e.g., anonymization).

**Dual-Use and Misuse Risks**
The proposed framework enables automated control of desktop environments (Section 1, Introduction; Section 3.4, Evaluation Harness). While the primary intent is benchmarking, the underlying infrastructure (verifiers, task synthesis, sandbox execution) could theoretically be repurposed for unauthorized automation, credential harvesting, or system manipulation. The paper currently lacks a "Dual-Use" or "Responsible Release" discussion. Authors should address potential misuse scenarios and outline any safeguards or usage policies implemented for the released code repository (Section 3.4, Release).

**Data Privacy and Synthetic Data**
Section 3.2.1 ("Verifier Generation") mentions generating "rich synthetic artifacts with realistic structure." Appendix/limitations.tex references tasks involving files like `zotero.sqlite` and `commissions.xlsx`. While the claim is that these are synthetic, the manuscript should explicitly state in the Data Availability or Limitations section that no real user personally identifiable information (PII) or sensitive data was used in the benchmark construction. This clarification is vital to ensure researchers using the benchmark do not inadvertently introduce privacy risks by modifying the task seeds with real data.

**Sandbox Safety**
Section 3.4 mentions cloud-scale execution (AWS, E2B). The authors should briefly confirm that sandboxed environments include safeguards to prevent agents from performing destructive actions (e.g., deleting system files, network exfiltration) even within the evaluation context, ensuring the infrastructure itself does not pose a risk to the hosting environment.

These additions will align the manuscript with standard safety and ethics guidelines for AI infrastructure papers.
