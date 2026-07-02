---
action_items:
- id: 46a32340dcef
  severity: writing
  text: The manuscript lacks an explicit statement regarding IRB approval or ethics
    committee oversight for collecting workflows from 250+ industry experts. Add a
    formal ethics statement or exemption justification in Section 3.3 or Appendix
    B.
- id: e7c2d3e01e27
  severity: writing
  text: The 'GUI-as-Tool' mode grants agents full desktop control. The paper must
    explicitly detail sandboxing measures beyond standard VM isolation to prevent
    host escape, external network access, or modification of systems outside the task
    scope.
- id: 1921ba9c3dfc
  severity: writing
  text: Tasks in radiology and cybersecurity raise dual-use and privacy risks. Clarify
    HIPAA/GDPR compliance for patient data in radiology tasks and confirm cybersecurity
    tasks use synthetic/public data to prevent generating real exploits.
artifact_hash: 326ff13c3b60fc13345363439d3391333425191b488bb3324c7d31083263c3e8
artifact_path: projects/PROJ-688-agents-last-exam/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T03:11:42.509428Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper presents a comprehensive benchmark for evaluating AI agents on professional workflows. From a safety and ethics perspective, the scope of the benchmark—spanning radiology, cybersecurity, and industrial control systems—introduces significant dual-use and privacy risks that require explicit mitigation strategies in the text.

First, regarding **human subjects and data privacy**, the benchmark relies on workflows sourced from 250+ industry experts (Section 3.3, Appendix B). While the paper mentions a "submission portal," it does not state whether the collection of these professional tasks and the associated data (which may include proprietary code, financial records, or patient data in the radiology examples) was conducted under an Institutional Review Board (IRB) protocol or with informed consent. Given the potential for these tasks to reveal sensitive professional practices or personal data, a formal ethics statement or a clear justification for exemption is necessary.

Second, the **dual-use potential** of the benchmark is high. The inclusion of tasks in cybersecurity (e.g., `snake_crackme`) and the ability of agents to execute shell commands and interact with GUIs in industrial software (e.g., PowerMill, Moldex3D) creates a risk that the benchmark itself could be used to train agents for malicious purposes, such as automating cyberattacks or industrial sabotage. The paper currently describes the evaluation pipeline but lacks a dedicated section on **safety guardrails and containment**. Specifically, it should detail how the virtual machine environments are sandboxed to prevent agents from escaping to the host, accessing external networks, or modifying systems outside the task scope.

Third, specific **domain-sensitive tasks** require clarification. The radiology task (`radiology/microdicom_nih_cxr_reader_adjudication`) involves medical imaging. The authors must explicitly confirm that all patient data has been de-identified in accordance with HIPAA or GDPR standards and that no Protected Health Information (PHI) is present in the benchmark artifacts. Similarly, for cybersecurity tasks, the paper should clarify that the "crackme" challenges are synthetic or derived from public, non-malicious sources, and that the benchmark does not facilitate the generation of real-world exploits.

Finally, the use of **LLM-as-judge** for certain tasks (Section 4.3, Appendix A.3) introduces risks of bias or hallucination in scoring, particularly for subjective or safety-critical domains. While the paper notes a preference for deterministic scoring, the 6.8% of tasks relying on LLM judges should be reviewed for potential safety failures (e.g., an agent generating harmful content that the judge fails to penalize). A brief discussion on the safety of the judging prompts and the potential for reward hacking in these specific cases would strengthen the ethical rigor of the evaluation.

In summary, while the benchmark is technically sound, the manuscript requires additions to address IRB/ethics compliance, dual-use risks, data privacy in sensitive domains, and containment strategies to meet safety and ethics standards.
