---
action_items:
- id: f232d747b625
  severity: writing
  text: Revise the Impact Statement to explicitly discuss dual-use risks (e.g., deepfakes,
    misinformation) and mitigation strategies, rather than dismissing societal consequences.
- id: c9e1d8a01556
  severity: writing
  text: Add a statement in the Appendix confirming that the user study received IRB
    approval or followed ethical guidelines regarding informed consent for annotators.
artifact_hash: 2fc45fd89cfd8c3cc27102ad20713af6a66d4f721af1c258a0cd318f7ea682b3
artifact_path: projects/PROJ-614-enhancing-train-free-infinite-frame-gene/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-01T11:00:00.262024Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript presents a novel train-free method for infinite-frame video generation. While the technical contributions are clear, the safety and ethics documentation requires significant improvement to meet conference standards for generative AI research.

**Impact Statement (Page 13, Section "Impact Statement"):**
The current statement asserts, "There are many potential societal consequences of our work, none which we feel must be specifically highlighted here." This is inadequate for a technology that enables consistent, long-duration video synthesis. Such capabilities significantly lower the barrier for creating convincing deepfakes, long-form misinformation, and synthetic propaganda. The authors must revise this section to explicitly acknowledge dual-use risks, including identity impersonation, political disinformation, and copyright infringement. Furthermore, the statement should discuss potential mitigation strategies, such as watermarking or detection mechanisms, to demonstrate responsible AI development practices.

**Human Evaluation Ethics (Appendix, Section "Human Evaluation Experiments"):**
The paper describes a user study involving eight annotators comparing generated videos. However, there is no mention of Institutional Review Board (IRB) approval, ethical oversight, or informed consent procedures. Standard ethical guidelines for research involving human participants require confirmation that subjects were treated ethically and consented to their data being used for research purposes. Please add a statement confirming compliance with relevant ethical standards or institutional guidelines.

**Conflict of Interest (Page 1):**
The disclosure regarding employment at AMAP, Alibaba Group, and the use of the Wan2.1 model from a separate team is transparent and acceptable.

These revisions are primarily textual but are critical for ensuring the paper adheres to ethical research standards.
