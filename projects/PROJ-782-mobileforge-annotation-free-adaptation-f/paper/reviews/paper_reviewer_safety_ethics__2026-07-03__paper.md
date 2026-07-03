---
action_items:
- id: 2900b39712be
  severity: writing
  text: 'The manuscript presents MobileForge, an annotation-free adaptation system
    for mobile GUI agents. From a safety and ethics perspective, the primary concerns
    revolve around the autonomy of the agent during the exploration and training phases,
    and the provenance of the data used to train the policy. Data Privacy and Consent:
    In Section 3.2 ("MobileGym: Building an Adaptation Substrate"), the authors describe
    "Target-App Exploration" using depth-first traversal to collect transition records.
    While t'
artifact_hash: eb6909e8c26be542682832f5d7b13c92b92b728f8b94fb6c9612acad1621be79
artifact_path: projects/PROJ-782-mobileforge-annotation-free-adaptation-f/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T06:30:31.129250Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript presents MobileForge, an annotation-free adaptation system for mobile GUI agents. From a safety and ethics perspective, the primary concerns revolve around the autonomy of the agent during the exploration and training phases, and the provenance of the data used to train the policy.

**Data Privacy and Consent:**
In Section 3.2 ("MobileGym: Building an Adaptation Substrate"), the authors describe "Target-App Exploration" using depth-first traversal to collect transition records. While the paper mentions using 20 apps (Table in Appendix e002), it does not explicitly state whether these apps contain real user data or if the exploration was conducted in a strictly controlled, synthetic environment. If any real user data (screenshots, logs, or interaction traces) was captured, the manuscript must include a statement regarding IRB approval or explicit user consent. If the data is synthetic or from public datasets, this distinction should be clearly articulated to avoid ambiguity regarding privacy violations.

**Safety of Autonomous Actions:**
The core methodology involves the agent performing rollouts and receiving feedback to optimize its policy (Section 3.3, HiFPO). The "corrective hints" and "process labels" are generated automatically. There is a risk that without explicit safety constraints, the agent could learn to perform harmful actions (e.g., deleting critical files, initiating financial transactions, or bypassing security prompts) if the reward signal (task completion) is achieved through such means. The "Limitations" section (Section 6) briefly mentions dependence on the evaluator's quality but does not detail specific safety guardrails or "kill switches" implemented during the training loop to prevent the agent from executing dangerous actions. A brief description of the safety filtering mechanisms or the scope of allowed actions would be necessary.

**Evaluation Environment:**
The benchmarks (AndroidWorld, MobileWorld) are cited as the evaluation ground. It is crucial to confirm that these environments are isolated sandboxes. The review should verify that the agent's actions during evaluation cannot propagate to real-world systems, affect other users, or cause unintended side effects outside the controlled testbed. The current text implies this but lacks an explicit safety statement regarding the isolation of the experimental setup.

**Dual-Use Considerations:**
While the paper focuses on improving agent performance, the capability to autonomously navigate and manipulate mobile interfaces without human supervision has dual-use potential (e.g., automated fraud, spam generation, or privacy invasion). The authors should briefly acknowledge these potential misuse scenarios and discuss any mitigations or ethical guidelines they followed in the development of the system.

The paper is technically sound in its approach, but these safety and ethical clarifications are required before the work can be considered fully responsible for publication.
