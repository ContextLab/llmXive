---
action_items:
- id: 9e75747267ab
  severity: science
  text: The paper describes training on 'MemGUI-3K' (2,956 trajectories) derived from
    'task expansion' and 'teacher rollouts' (Section 4.2, Fig 3). It is unclear if
    these trajectories involve real user data or simulated interactions. If real user
    data was used, the paper must explicitly state IRB approval status, consent procedures,
    and data anonymization methods. If synthetic, the generation process must be detailed
    to ensure no PII leakage from the teacher model's training data.
- id: 8c767269591f
  severity: science
  text: The agent is designed to perform 'memory_add', 'memory_update', and 'memory_delete'
    actions (Eq 3, Appendix e001) on mobile devices. The paper lacks a safety analysis
    regarding the potential for the agent to autonomously delete user data, modify
    sensitive settings, or leak private information (e.g., passwords, financial data)
    into its 'Folded UI State' or 'Memory' fields. A discussion on guardrails or constraints
    to prevent harmful autonomous actions is required.
- id: 235b2d5d7264
  severity: writing
  text: The dataset construction involves 'entity substitution' and 'task simplification'
    (Appendix e002, Table A1). The paper does not address whether the resulting synthetic
    tasks inadvertently create scenarios that could be used for social engineering
    or phishing simulations (e.g., 'transfer money to X', 'change password to Y').
    A statement on the safety of the benchmark tasks and the exclusion of high-risk
    scenarios is needed.
artifact_hash: 7ba9201f0f49d9384a35f3eca07d4fd8d448c0da222a8a4e9472044b7e857c18
artifact_path: projects/PROJ-781-memgui-agent-an-end-to-end-long-horizon/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T19:24:45.075329Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper presents MemGUI-Agent, a system capable of autonomous long-horizon interaction with mobile GUIs, including the ability to read, write, and delete memory items (Section 3, Eq 3). While the technical contribution is significant, the manuscript lacks sufficient discussion on safety and ethical implications, particularly regarding data privacy and potential for harm.

First, the provenance of the **MemGUI-3K** dataset (Section 4) is ambiguous. The authors state the data comes from "task expansion" and "teacher rollouts" using a 235B model. It is critical to clarify if any real user interaction logs were used. If so, the paper must explicitly confirm IRB/IACUC approval, describe how Personally Identifiable Information (PII) was scrubbed, and detail the consent process. If the data is entirely synthetic, the authors should explain how they ensured the teacher model did not hallucinate or leak sensitive information from its own training data into the dataset. Without this, the release of the dataset poses a privacy risk.

Second, the agent's capability to autonomously execute `memory_delete` and `memory_update` actions (Appendix e001, Prompt) introduces a **dual-use risk**. An agent trained to optimize task completion could inadvertently or maliciously delete critical user data, alter security settings, or exfiltrate sensitive information (e.g., banking details, private messages) into its context window. The paper currently treats these actions as neutral performance metrics. A dedicated subsection in the "Limitations" or "Discussion" section is required to analyze these risks and describe any safety guardrails (e.g., human-in-the-loop confirmation for destructive actions, PII redaction in the observation stream) that were implemented or are recommended for deployment.

Finally, the benchmark tasks involve "entity substitution" (Appendix e002). The authors should verify that the generated tasks do not simulate high-risk scenarios such as unauthorized fund transfers, phishing attempts, or the bypassing of security protocols. A statement confirming the exclusion of such harmful scenarios from the benchmark is necessary to ensure the research does not inadvertently provide a blueprint for malicious automation.
