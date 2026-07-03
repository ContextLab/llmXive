---
action_items:
- id: 2fefb1dce4a8
  severity: writing
  text: The paper lacks an explicit statement regarding IRB approval or ethical review
    for the use of human dialogue datasets (MultiWOZ, ESConv, AnnoMI). While these
    are public, the transformation into a new benchmark and the potential for generating
    sensitive UI interactions in emotional support contexts requires a dedicated ethics
    statement confirming compliance with original data licenses and user consent.
- id: 321cb5ec581c
  severity: writing
  text: The 'L3 Cognitive Load' metric (Section 5.2) defines a strict deduction for
    'more than 4 independent interactive components' as a failure. This arbitrary
    threshold lacks empirical justification regarding human factors or accessibility
    standards (e.g., WCAG). The paper should cite relevant HCI literature or user
    studies to validate this specific cutoff to avoid bias against complex but necessary
    interactions.
- id: 0336a8a688c5
  severity: writing
  text: The system prompt for the 'w/o schema' model (Appendix A.1) lists specific
    icon names (e.g., 'emotion-unhappy', 'anguished-face'). The paper does not address
    the safety implications of generating UIs with negative emotional icons in sensitive
    contexts (e.g., ESConv). A discussion on mitigating potential harm or bias in
    icon selection for mental health scenarios is needed.
artifact_hash: 64f9753c508342ff47b0fefdddb7219cc59ae325dbfacf0e2b9d4340a33d4e53
artifact_path: projects/PROJ-629-macaron-a2ui-a-model-for-generative-ui-i/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T00:33:42.054109Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript presents a novel approach to Generative UI but requires clarification on several safety and ethical dimensions before publication.

First, regarding **data privacy and consent**, the authors construct a corpus from heterogeneous sources including MultiWOZ, ESConv (Emotional Support Conversation), and AnnoMI (Motivational Interviewing). While these datasets are publicly available, the paper (Section 4) does not explicitly state whether the original data licenses permit the creation of a new, derived benchmark (A2UI-Bench) or if the transformation process involved any re-identification risks. Specifically, the ESConv dataset contains sensitive mental health dialogues. The authors must include a dedicated "Ethics Statement" or "Data Usage" section confirming that the derived dataset adheres to the original consent terms and that no personally identifiable information (PII) was inadvertently exposed or amplified during the augmentation process.

Second, the **evaluation metrics** introduce potential safety risks through arbitrary thresholds. In Section 5.2 (Metrics), the L3 (User Experience) evaluation includes a "Strict deduction" rule: "More than 4 independent interactive components or more than 8 options displayed at once" results in a score of 1. This threshold appears arbitrary and is not grounded in established Human-Computer Interaction (HCI) literature or accessibility guidelines (such as WCAG). Enforcing such a rigid limit could penalize models that correctly identify a need for complex interaction in high-stakes scenarios (e.g., medical triage or financial planning) and could inadvertently bias the model against providing necessary information density. The authors should justify this threshold with empirical evidence or cite relevant cognitive load studies.

Finally, there is a **dual-use and bias concern** regarding the generated UI components. The system prompts (Appendix A.1) explicitly list icon names including "emotion-unhappy," "anguished-face," and "disappointed-face." In the context of the ESConv and AnnoMI datasets, the generation of UIs containing negative emotional icons could be psychologically harmful or trigger distress in vulnerable users. The paper currently lacks a discussion on how the model is constrained to prevent the generation of such potentially harmful visual elements in sensitive conversational contexts. A safety mitigation strategy or a discussion on the ethical implications of "emotional UI" is required.
