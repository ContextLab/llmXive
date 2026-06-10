---
action_items:
- id: dcea918702bd
  severity: writing
  text: Add IRB approval statement or informed consent details for human teleoperation
    data collection described in sec/real_world_exp.tex.
- id: 05da97288c54
  severity: writing
  text: Describe physical safety protocols (emergency stops, barriers) used during
    real-world Franka robot trials in sec/real_world_exp.tex.
- id: e519b833299e
  severity: writing
  text: Include a dual-use discussion and responsible deployment limitations in sec/discussion.
artifact_hash: bf25ed8c32843a89226c47ca4dcbfcdb0c63d6720d9c7d52a55697f1d16cf9dc
artifact_path: projects/PROJ-600-https-arxiv-org-abs-2605-15298/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-10T10:35:26.931805Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The PhysBrain 1.0 report presents a VLA framework leveraging human egocentric video for physical commonsense. While the technical contribution is notable, several safety and ethics disclosures are missing that require attention before publication.

First, regarding human subject data, Section `sec/real_world_exp.tex` (Data Collection) describes collecting 450 trajectories via human teleoperation using a SpaceMouse. There is no mention of IRB approval or informed consent for the human operators involved in this data collection. Standard robotics ethics require explicit documentation of ethical clearance when humans generate training data, even via teleoperation.

Second, real-world physical safety is underspecified. The experiments involve a Franka robot arm interacting with objects in a physical workspace (`sec/real_world_exp.tex`). The text does not describe safety protocols (e.g., emergency stops, physical barriers, operator distance monitoring) during the 500+ trials. This omission raises concerns about physical safety during evaluation, particularly given the potential for hardware malfunction or unexpected policy behavior.

Third, data privacy and provenance require clarification. The training data includes public egocentric datasets (Ego4D, EPIC in `sec/data_engine.tex`). While public, the paper does not discuss compliance with original consent scopes or privacy-preserving measures for the video frames used in annotation. Additionally, the annotation pipeline relies on proprietary LLMs (GPT-5, Gemini 3), introducing opacity into the supervision signal.

Finally, the Discussion section lacks a dual-use analysis. The capability to transfer physical commonsense to generalist robots has potential for sensitive applications beyond the reported vegetable grasping tasks. Table 1 (`tab/QA.tex`) lists "Affordance and safety" as a QA category, but this refers to model understanding, not system-level safety certification.

Addressing these points through text additions is necessary to ensure ethical compliance and transparency.
