---
action_items:
- id: 0546ecc01a06
  severity: science
  text: The paper lacks explicit IRB/IACUC approval statements or ethical clearance
    for the real-robot experiments described in Section 4.3 (Appendix). Given the
    use of physical hardware and potential for physical harm during OOD failures,
    a formal safety protocol or ethics board approval statement is required.
- id: ed55c4989c2f
  severity: science
  text: The evaluation relies on LLM judges (Gemini 3.1 Pro, GPT 5.4) for scoring
    image and action generation (Section 4.2, Appendix). The paper does not address
    the potential for bias, hallucination, or safety misalignment in these automated
    judges, nor does it provide a human-in-the-loop verification step for safety-critical
    failures.
- id: 79cab5110cc8
  severity: writing
  text: The 'PRICE-V0.1' benchmark and real-robot tasks involve physical interactions.
    The paper does not explicitly discuss the safety measures taken to prevent physical
    damage to the robot or the environment during the 'failure' scenarios described
    in Figures 5-9 (Appendix). A safety mitigation statement is needed.
artifact_hash: b5c260e3cad57a502ee5de9a92837ef2e2204625255c1d5da0b8c81a30982bbf
artifact_path: projects/PROJ-852-orca-the-world-is-in-your-mind/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T19:17:34.236144Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript presents a novel approach to world modeling but lacks sufficient detail regarding safety protocols and ethical oversight for its physical experiments.

**Ethical Oversight and Physical Safety:**
The paper details real-robot experiments involving dual-arm manipulation (Section 4.3, Appendix) where the model is explicitly tested on "failure" scenarios and "recovery" (Figures 5-9). While the tasks (e.g., stacking bowls, scooping sugar) appear benign, the use of physical hardware necessitates a clear statement regarding safety protocols. Specifically, the authors must confirm whether these experiments were conducted under an Institutional Review Board (IRB) or Institutional Animal Care and Use Committee (IACUC) equivalent for robotics, or if a specific safety review board approved the risk of physical damage to the robot or environment during the OOD (Out-of-Distribution) failure tests. The absence of such a statement in the "Conclusion" or "Appendix" is a significant omission for a paper involving embodied AI.

**Automated Evaluation Safety:**
The evaluation of image and action generation relies heavily on LLM-based judges (Gemini 3.1 Pro, GPT 5.4, Doubao Seed 2.0 Pro) as described in Section 4.2 and the Appendix. The paper does not address the safety alignment of these judges. If the model generates a physically dangerous action (e.g., a robot arm moving towards a human, though not explicitly in the current tasks), an unaligned LLM judge might score it highly based on "instruction following" rather than safety. The authors should clarify if a safety filter or human verification step was applied to the outputs of these judges to prevent the propagation of unsafe behaviors in the evaluation metrics.

**Data Privacy and Consent:**
The paper mentions using "12.5K h" of video data and "160M events" for pre-training (Appendix, Section 5.1). While the source is not explicitly detailed in the provided text, if this data includes human subjects (e.g., from AgiBot-World or similar datasets), the authors must explicitly state that the data was collected with appropriate consent and that privacy measures (such as face blurring or PII removal) were applied. The current text assumes the data is safe without justification.

**Recommendation:**
The authors should add a dedicated "Ethical Considerations" or "Safety Statement" section. This section must:
1. Confirm IRB/ethics approval for real-robot testing.
2. Describe safety protocols used during physical experiments (e.g., emergency stops, human supervision).
3. Discuss the limitations of LLM judges in assessing safety and any mitigations used.
4. Clarify the provenance and consent status of the pre-training video data.
