---
action_items:
- id: 42f225092a20
  severity: science
  text: Add explicit statement about IRB/ethics committee approval or justification
    for exemption when using employee workplace session data. Section 7 (Ethical Considerations)
    is too brief and does not address consent or oversight.
- id: 2e47b23bd590
  severity: science
  text: Document the redaction and privacy protection process in detail. The pipeline
    includes a 'redaction recovery' step (Section 3, Appendix) that could potentially
    restore sensitive information. Explain how this is controlled and audited.
- id: 65c60ca7b735
  severity: science
  text: Clarify whether employees whose sessions were used provided informed consent
    for research use. If not, explain the legal/ethical basis for using proprietary
    employee data in public research.
- id: 801623241a63
  severity: writing
  text: Add a conflict of interest statement. Authors are from Frontis.AI, and the
    benchmark uses their internal enterprise deployment. This creates potential bias
    in evaluation of their own or competitor products.
artifact_hash: 436f60fbb896e41d063ceb9811d2249a06e1b5eaa235430cfaccb20cf6596607
artifact_path: projects/PROJ-773-enterpriseclawbench-benchmarking-agents/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-27T00:53:29.584737Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

**Safety and Ethics Review**

This paper presents EnterpriseClawBench, a benchmark constructed from real workplace agent sessions at an AI startup. While the authors acknowledge privacy concerns in Section 7 (Ethical Considerations) and the Limitations section, several critical safety and ethics gaps remain unaddressed.

**Data Privacy and Consent (Section 3, Appendix)**
The benchmark is built from "continuous internal use of an enterprise agent system at an AI startup with more than 100 employees" (Section 3). The data includes employee chat sessions, uploaded files, tool traces, and business artifacts. However:
- No IRB or ethics committee approval is mentioned
- No documentation of employee informed consent for research use
- The "redaction recovery" step in the pipeline (Appendix, Redaction Recovery case) could potentially restore sensitive information that was originally redacted

**Dual-Use and Harm Potential (Section 3, Table 1)**
The benchmark includes tasks involving:
- Financial data processing (finance/ops role class)
- HR/admin tasks including "compensation costs for two employee departure-plan options" (Table in Appendix)
- Customer relationship and sales intelligence data

These capabilities could be used to develop workplace surveillance systems or agents that process sensitive employee/customer data without adequate safeguards.

**Conflict of Interest (Title Page)**
Authors are affiliated with "Horizon Research, Frontis.AI" and the benchmark uses their internal enterprise deployment. This creates potential bias in evaluating their own products versus competitors' harnesses.

**Recommendations**
1. Add explicit IRB/ethics approval statement or exemption justification
2. Document the redaction process and how recovery is controlled
3. Clarify employee consent status for session data use
4. Add conflict of interest disclosure regarding the authors' affiliation with the enterprise using the benchmark
