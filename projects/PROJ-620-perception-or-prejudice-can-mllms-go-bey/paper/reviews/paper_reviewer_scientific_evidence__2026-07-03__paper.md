---
action_items:
- id: 1f23e1ec51c3
  severity: science
  text: The 'Reasoning Capability' analysis (Appendix E002, Tab:reasoning) is observational
    and explicitly confounded by model size and family. The claim that reasoning capabilities
    drive the HR/PR gap requires a controlled ablation (e.g., same base model with/without
    RL) or a regression analysis controlling for parameters to rule out size as the
    primary driver.
- id: 7c807b4282cf
  severity: science
  text: The 'Prejudice Gap' (PR) metric relies on the assumption that T3 MCQs perfectly
    capture the evidence used for T1 ratings. The paper notes 153 'human-only' questions
    (1.8%) and varying difficulty. A sensitivity analysis is needed to show that the
    51% PR statistic is robust to the inclusion/exclusion of these ambiguous or extremely
    difficult items, rather than being an artifact of the specific MCQ distractors.
- id: fc4ddbf00264
  severity: science
  text: The AI-as-Judge for Task 2 (T2) shows a self-preference bias of +1.0 point
    for GPT-4o-mini (Tab:cross_judge). While the authors argue this doesn't distort
    ranking, the absolute score inflation could impact the calculation of the 'Holistic-grounding
    Rate' (HR) if the T2 threshold (theta_2=0.7) is sensitive to this bias. Report
    HR sensitivity to a +/- 1.0 score shift.
artifact_hash: 46c2ca87e5752401742be8e75f855167112497e54e4e0af681d19e8bf31d8374
artifact_path: projects/PROJ-620-perception-or-prejudice-can-mllms-go-bey/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T19:36:16.256836Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a substantial dataset (MM-OCEAN) and a novel evaluation framework distinguishing between correct personality ratings and grounded reasoning. The sample size (1,104 videos, 5,320 MCQs) is robust for benchmarking, and the multi-stage human annotation pipeline (24 annotators, 77% agreement) provides a solid foundation for the ground truth. The distinction between "perception" and "prejudice" is operationally defined through the Prejudice Rate (PR) and Holistic-grounding Rate (HR), which are mathematically sound given the three-task setup.

However, the scientific evidence supporting the causal interpretation of the "Reasoning Capability" effect is weak. In Appendix E002 (Table:reasoning), the authors compare "Reasoning-capable" vs. "Non-reasoning" models, finding a +18.3pp gap in T3. The text explicitly admits this is "Confounded by size/family/generation." Without a controlled experiment (e.g., ablating reasoning chains in a single model family) or a multivariate regression controlling for parameter count and training data, the claim that "reasoning capability" is the driver of the gap is speculative. The data equally supports the hypothesis that larger, more capable models simply have better visual grounding architectures, regardless of their "reasoning" label.

Additionally, the robustness of the central "Prejudice Gap" claim (51% of correct ratings are ungrounded) depends heavily on the validity of the T3 MCQs as a proxy for "evidence." The paper notes that 153 questions (1.8%) were answered correctly by no model, and difficulty varies widely (30.7% to 64.8%). If the MCQs are poorly constructed or if the "correct" answer relies on subtle cues not captured by the distractors, the PR metric may overstate the "prejudice." A sensitivity analysis showing how PR fluctuates when excluding the most difficult or ambiguous items is necessary to confirm the stability of the 51% figure.

Finally, while the cross-judge correlation is high (rho=0.94), the GPT-4o-mini judge exhibits a consistent +1.0 point self-preference bias (Table:cross_judge). Since the HR metric requires passing a threshold (theta_2=0.7) on the T2 score, this bias could artificially inflate the HR for GPT-4o-mini family models. The authors should demonstrate that the ranking of models by HR remains stable if the T2 scores are adjusted to remove this systematic bias.
