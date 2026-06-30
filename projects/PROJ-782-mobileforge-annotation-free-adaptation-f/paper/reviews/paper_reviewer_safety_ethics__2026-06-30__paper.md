---
action_items:
- id: 367db60d8286
  severity: writing
  text: The paper presents a method for annotation-free adaptation of mobile GUI agents,
    involving autonomous exploration and interaction with real-world mobile applications.
    From a safety and ethics perspective, several critical gaps in disclosure and
    mitigation strategies must be addressed before publication. First, the methodology
    section (Sec 2, e000) and Table 2 (e002) indicate that the system explores 20
    distinct mobile apps to mine executable tasks. The paper does not state whether
    this interacti
artifact_hash: eb6909e8c26be542682832f5d7b13c92b92b728f8b94fb6c9612acad1621be79
artifact_path: projects/PROJ-782-mobileforge-annotation-free-adaptation-f/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T20:14:11.916837Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper presents a method for annotation-free adaptation of mobile GUI agents, involving autonomous exploration and interaction with real-world mobile applications. From a safety and ethics perspective, several critical gaps in disclosure and mitigation strategies must be addressed before publication.

First, the methodology section (Sec 2, e000) and Table 2 (e002) indicate that the system explores 20 distinct mobile apps to mine executable tasks. The paper does not state whether this interaction was conducted in a controlled, sandboxed environment or on devices containing real user data. If human subjects were involved in the setup or if the apps contained personal data, the absence of an IRB (Institutional Review Board) or equivalent ethical approval statement is a significant omission. The authors must clarify the nature of the test environment and confirm that no private user data was accessed or processed without consent.

Second, the evaluation of the agent's performance relies heavily on a "Critic" model (Sec 2.1, e000), with Table 4 (e001) suggesting the use of Gemini 2.5 Pro for final decision evaluation. This implies that screenshots and interaction trajectories are transmitted to a third-party cloud API. The paper lacks a data privacy statement addressing how sensitive information potentially visible in these screenshots (e.g., login credentials, financial details, private messages) is handled, stored, or discarded. Given the "annotation-free" nature of the data collection, there is a risk of inadvertently capturing and transmitting PII (Personally Identifiable Information).

Finally, the autonomous nature of the agent poses a risk of unintended harm. The case studies (Fig 3, e001) show the agent performing actions like "recipe deletion" and "sending emails." The paper does not describe the safety guardrails or "kill switches" implemented to prevent the agent from executing destructive actions on real accounts or devices during the training loop. Without explicit discussion of these safety constraints, the deployment of such a system in real-world scenarios carries a non-trivial risk of user harm.

The authors are requested to add a dedicated "Ethical Considerations" subsection in the Conclusion or Experiments section to address these points: (1) confirmation of ethical review or sandboxed testing, (2) data privacy protocols for third-party model usage, and (3) safety mechanisms preventing destructive autonomous actions.
