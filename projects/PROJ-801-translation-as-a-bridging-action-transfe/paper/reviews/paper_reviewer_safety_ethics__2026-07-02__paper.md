---
action_items:
- id: 768db68befc1
  severity: writing
  text: The manuscript describes collecting ~500 hours of 'out-sourced free-form household
    manipulation' data (Sec. 3.3) but lacks details on human subject consent, IRB
    approval, or data privacy protocols. Explicitly state the ethical review status
    and how participant anonymity was preserved.
- id: 6080efb70dba
  severity: writing
  text: The study involves real-world robot deployment on 15 manipulation tasks (Sec.
    4.1) with potential for physical harm (e.g., breaking objects, pinching). The
    paper does not mention safety protocols, emergency stop mechanisms, or risk mitigation
    strategies used during data collection and evaluation.
artifact_hash: 6729da456139f307f3d0e73ac6f31e579b7d43848bd0dd84327d8a569e70121b
artifact_path: projects/PROJ-801-translation-as-a-bridging-action-transfe/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T07:08:57.860004Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

This review focuses exclusively on safety and ethical considerations regarding the data collection, human subjects, and physical deployment of the robotic system.

**Human Subject Data and Consent**
The manuscript states in Section 3.3 ("Training Strategies") that the authors utilized "approximately 600 hours of human actions," including "~500 hours of out-sourced free-form household manipulation." While the paper mentions using PICO 4 Ultra Enterprise headsets for data collection, it provides no information regarding the ethical oversight of this data collection. Specifically, the text lacks:
1.  **IRB/Ethics Approval:** A statement confirming whether the data collection protocol was reviewed and approved by an Institutional Review Board (IRB) or equivalent ethics committee.
2.  **Informed Consent:** Details on how human participants were informed about the data usage, storage, and potential risks, and whether explicit consent was obtained.
3.  **Privacy and Anonymity:** Given the use of head-mounted cameras (PICO 4) and "in-the-wild" or "out-sourced" settings, there is a high risk of capturing identifiable faces, private environments, or sensitive activities. The paper does not describe the methods used to anonymize this data (e.g., blurring faces, cropping backgrounds) or how privacy was maintained.

Without these disclosures, the reproducibility and ethical validity of the human data component are unclear.

**Physical Safety and Risk Mitigation**
The experiments involve a bi-manual mobile robot (ByteMini) performing manipulation tasks in real-world environments (Section 4.1), including opening microwaves, handling mugs, and interacting with drawers. These tasks carry inherent risks of physical harm to humans (if present), damage to property, or injury to the robot itself.
*   The "Evaluation Setups" section (Section 4.1) describes the tasks and metrics but does not mention safety protocols.
*   There is no description of **emergency stop mechanisms**, **collision avoidance** strategies during the rollout phase, or **supervision requirements** (e.g., was a human operator present to intervene?).
*   The "Failure Case Analysis" (Section 5.8) acknowledges that the robot fails at grasping straws or opening drawers, which could lead to dropped objects or collisions. The paper should explicitly state how these failure modes were managed to ensure safety during the 8 trials per task.

**Recommendations**
To address these concerns, the authors should add a dedicated "Ethics and Safety" subsection or expand the "Experimental Setup" to include:
*   Confirmation of IRB approval or a statement that the research was exempt, along with details on consent procedures for the 500+ hours of human data.
*   A description of data anonymization techniques applied to the video streams.
*   A summary of safety measures implemented during real-robot experiments (e.g., safety zones, emergency stops, human supervision).

These additions are necessary to ensure the research adheres to standard ethical guidelines for human-subject research and safe robotic deployment.
