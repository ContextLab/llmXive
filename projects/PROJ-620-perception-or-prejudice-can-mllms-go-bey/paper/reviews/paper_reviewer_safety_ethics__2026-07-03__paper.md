---
action_items:
- id: 4af33c162ee1
  severity: writing
  text: 'The manuscript addresses a critical safety concern: the distinction between
    genuine perception and algorithmic prejudice in personality assessment. The "Prejudice
    Gap" metric is a valuable contribution to safety evaluation. However, several
    ethical and safety gaps require attention before publication. First, the Ethics
    and Responsible Use section (Appendix E) is currently too brief regarding the
    specific risks of the new annotations. While the authors acknowledge the Western
    bias inherited from'
artifact_hash: 46c2ca87e5752401742be8e75f855167112497e54e4e0af681d19e8bf31d8374
artifact_path: projects/PROJ-620-perception-or-prejudice-can-mllms-go-bey/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T19:35:55.855722Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript addresses a critical safety concern: the distinction between genuine perception and algorithmic prejudice in personality assessment. The "Prejudice Gap" metric is a valuable contribution to safety evaluation. However, several ethical and safety gaps require attention before publication.

First, the **Ethics and Responsible Use** section (Appendix E) is currently too brief regarding the specific risks of the new annotations. While the authors acknowledge the Western bias inherited from ChaLearn First Impressions V2, they do not detail how the 24 human annotators or the "Psychologist" stage mitigated cultural bias when generating the 5,320 new MCQs and trait analyses. Without a statement on the demographic diversity of the annotators or a cross-cultural validation step, the benchmark risks encoding and amplifying specific cultural stereotypes under the guise of "grounded" reasoning.

Second, the **dual-use risk** is significant. The paper explicitly mentions "interview screening" as a deployment scenario in the Introduction. Although the authors state the benchmark is a "diagnostic research tool," the detailed "Prejudice Gap" and "Holistic-grounding Rate" metrics could be misinterpreted by industry actors as a validation of automated personality screening. The Ethics section must include a stronger, explicit prohibition against using MM-OCEAN for real-world hiring, lending, or surveillance decisions without rigorous, independent fairness audits and human-in-the-loop oversight.

Third, **data privacy and consent** require clarification. The dataset consists of 1,104 video clips of individuals. While the source is public, the new annotations (atomic behavioral cues, bounding boxes, and specific trait scores) create a much more granular profile of the subjects than the original dataset. The authors must clarify the consent status of the original subjects regarding this specific secondary use for personality profiling and ensure the CC-BY-NC license explicitly covers the derived personality labels to prevent misuse.

Finally, the **AI-as-Judge** protocol (Appendix) uses GPT-4o-mini to score reasoning. While cross-judge robustness is tested, the potential for the judge model to inherit its own biases regarding "appropriate" personality expressions (e.g., penalizing non-Western communication styles) is not discussed. A brief analysis of the judge's own cultural bias would strengthen the safety claims.
