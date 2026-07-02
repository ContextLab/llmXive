---
action_items:
- id: 46a541c5887a
  severity: writing
  text: The paper aggregates 1.16M videos from public sources (e.g., Xperience, YT-VIS)
    without explicit mention of consent for 3D motion annotation or downstream model
    training. Add a statement in Section 3.1 or the Appendix confirming that all source
    data complies with original licenses and that no personally identifiable information
    (PII) or sensitive biometric data was retained or used.
- id: b77ec7f5bffa
  severity: writing
  text: The robotics transfer section (Sec 4.2) claims improved 'closed-loop success'
    in simulation but explicitly states 'We leave closed-loop real-robot evaluation
    to future work.' Given the potential for physical harm in real-world deployment,
    the paper must include a dedicated 'Safety and Limitations' subsection discussing
    the risks of deploying this model on physical hardware without further safety
    validation.
- id: f3f44b683ea4
  severity: writing
  text: The data pipeline uses LLMs (Molmo2, Qwen3) to generate captions and object
    phrases for 1.16M clips. There is no discussion of potential bias amplification
    or the inclusion of harmful/unsafe action descriptions in the training corpus.
    A brief statement on the filtering of unsafe content or the limitations of the
    automated curation regarding safety is required.
artifact_hash: 43d44b1b7f12aef158eaf0787875484ea72c6860cf8af3c796e4579ec99e55ab
artifact_path: projects/PROJ-741-molmomotion-forecasting-point-trajectori/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T05:12:19.333293Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript presents a significant contribution to 3D motion forecasting but requires specific clarifications regarding data ethics and safety implications before acceptance.

**Data Privacy and Consent:**
The construction of the MolmoMotion-1M dataset relies on scraping and processing 1.16M unconstrained videos from public sources (Section 3.1, Appendix A.1). While the authors cite the original datasets (e.g., Xperience, HD-EPIC), the paper lacks a specific statement regarding the ethical use of this data for *new* 3D trajectory annotation tasks. Specifically, there is no mention of whether the original licenses permit this specific type of derivative work or if any Personally Identifiable Information (PII) (e.g., faces, license plates) was redacted from the 1.16M clips before training. Given the scale, a statement confirming compliance with original data licenses and the absence of sensitive biometric data in the training set is necessary.

**Dual-Use and Physical Safety:**
The paper demonstrates that the model can predict object trajectories for robot manipulation (Section 4.2) and claims "closed-loop success" in simulation. However, the authors explicitly state in the Conclusion and Appendix that "closed-loop real-robot evaluation" is left to future work. This is a critical safety gap. A model trained on internet videos that predicts physical trajectories could be misused to plan harmful physical interactions if deployed on real hardware without rigorous safety constraints. The paper currently lacks a dedicated discussion on the risks of deploying this technology in the physical world. A "Safety and Limitations" section must be added to explicitly address the potential for physical harm, the necessity of safety layers (e.g., collision avoidance, human-in-the-loop) for real-world deployment, and the limitations of sim-to-real transfer regarding safety.

**Content Safety and Bias:**
The data curation pipeline relies heavily on LLMs (Molmo2, Qwen3) to generate action descriptions and object phrases for the training corpus (Appendix A.1.2). There is no discussion of how the authors ensured the training data does not contain harmful, violent, or unsafe action descriptions (e.g., "break," "throw at," "stab"). Without a filtering mechanism or a statement on the safety of the generated captions, there is a risk of the model learning to predict or facilitate harmful physical actions. The authors should clarify if any safety filtering was applied to the generated text or the source videos.

These issues are primarily writing and disclosure-related but are essential for the ethical deployment of the described technology.
