---
action_items:
- id: 54ee0379b741
  severity: writing
  text: The paper discusses 'Human-in-the-Loop Safety' and 'Sandboxed Execution' extensively
    (Sec 3.4, 4.3) but lacks a dedicated Ethics/Safety section detailing specific
    mitigation strategies for dual-use risks (e.g., autonomous code generation for
    malware, supply chain attacks). Explicitly address how the proposed harness prevents
    or detects malicious intent in generated code.
- id: c52e054d573f
  severity: writing
  text: In Section 4.1 (Code Assistants), the paper cites 'solution leakage' in benchmarks
    (e.g., SWE-bench). The review must clarify the ethical implications of training
    agents on data that may contain private or proprietary code, and whether the survey
    addresses data provenance and consent for the training corpora of the cited systems.
- id: 9e1d27edb4a5
  severity: writing
  text: Section 4.3 mentions 'Self-Driving Labs' and 'Scientific Discovery' where
    agents execute physical experiments. The manuscript needs to explicitly discuss
    safety protocols for physical harm (e.g., chemical synthesis, robotics) and the
    ethical boundaries of autonomous experimentation, rather than treating safety
    only as a software sandboxing issue.
artifact_hash: cbd4e8e17c331b3d11d6d3473a72ca30389ded91296199ea84247ea30361db9d
artifact_path: projects/PROJ-606-https-arxiv-org-abs-2605-18747/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T15:40:16.474877Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript "Code as Agent Harness" provides a comprehensive taxonomy of code-centric agentic systems. From a safety and ethics perspective, the paper correctly identifies the shift from model-centric to harness-centric reliability, emphasizing sandboxing, verification, and human-in-the-loop (HITL) gates (Sections 3.4 and 4.3). However, the treatment of safety remains largely technical (i.e., preventing code execution errors) rather than addressing broader ethical and dual-use risks.

First, while the paper mentions "safety governance" and "capability primitives" (Section 4.1), it lacks a dedicated discussion on **dual-use risks**. The ability of these harnesses to autonomously generate, test, and deploy code at scale significantly lowers the barrier for creating malware, exploiting vulnerabilities, or conducting supply chain attacks. The survey should explicitly address how the proposed frameworks mitigate these risks, such as through intent verification, malicious code detection in the "Verify" phase, or ethical constraints on the "Action" interface.

Second, regarding **data privacy and consent**, the paper cites numerous benchmarks (e.g., SWE-bench, SWE-Lancer) and systems trained on large code corpora. There is insufficient discussion on the ethical implications of training these agents on potentially proprietary or private code, or the risk of agents memorizing and regurgitating sensitive information (e.g., API keys, PII) found in repositories. The "Memory" section (Sec 3.2) touches on context management but does not address the ethical necessity of filtering sensitive data from the agent's memory or training set.

Third, in the context of **autonomous scientific discovery** (Section 4.4), the paper describes agents that design and execute physical experiments (e.g., chemical synthesis, protein design). While it mentions "safety boundaries," it does not sufficiently detail the ethical protocols required to prevent physical harm or the misuse of these systems for creating hazardous materials. The distinction between software sandboxing and physical safety governance needs to be sharper.

Finally, the discussion on **accountability** (Section 4.5) is promising but brief. As agents become more autonomous, the "black box" nature of their decision-making in the "Plan-Execute-Verify" loop raises questions about liability for errors or malicious actions. The paper should expand on how the "harness" can provide auditable trails that satisfy legal and ethical accountability standards, particularly in high-stakes domains like finance or healthcare.

In summary, while the technical safety mechanisms are well-covered, the manuscript requires a more explicit and rigorous treatment of dual-use risks, data ethics, and physical safety governance to be complete.
