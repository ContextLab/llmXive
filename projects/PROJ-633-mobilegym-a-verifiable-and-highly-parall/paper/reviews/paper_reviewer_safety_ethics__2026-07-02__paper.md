---
action_items:
- id: 6be1887fbb15
  severity: writing
  text: The 'High-Risk subset' results (Table 5) show frontier models successfully
    executing payment tasks (64.3% SR) without explicit refusal mechanisms. The paper
    must explicitly discuss the dual-use risk of training agents to bypass safety
    guardrails in financial contexts and clarify if the 'sandboxed' nature of the
    simulation adequately mitigates the risk of transferring these behaviors to real-world
    deployment.
- id: a6ab2fc24383
  severity: writing
  text: Section 'Ethical Considerations' mentions 'digital-literacy education' as
    a use case but lacks a concrete plan for preventing the misuse of the generated
    synthetic data or the trained models for social engineering or automated fraud.
    A specific mitigation strategy or usage policy for the released benchmark and
    models is required.
- id: 1a080d180243
  severity: writing
  text: "The 'Datasheet for Datasets' section (\xA71) notes an 'English-speaking demographic\
    \ focus' and 'limited accessibility coverage.' The authors should elaborate on\
    \ the potential for bias to cause safety failures for non-English speakers or\
    \ users with disabilities when these agents are deployed in real-world scenarios,\
    \ and propose a plan to address these gaps."
artifact_hash: a548124f155c8c790b0f8380f840762b6a4c9bd7b88cafb98ce50a865152c78b
artifact_path: projects/PROJ-633-mobilegym-a-verifiable-and-highly-parall/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T08:11:04.803384Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper presents MobileGym, a simulation platform for mobile GUI agents, and includes a dedicated "Ethical Considerations" section. From a safety and ethics perspective, the work is generally sound in its intent to provide a "consequence-free" sandbox for testing. However, several areas require clarification to ensure responsible dissemination and usage.

First, the empirical results in the "High-Risk subset" (Table 5, Appendix) are concerning from a safety alignment perspective. The data indicates that frontier models (e.g., Gemini 3.1 Pro) can successfully execute payment and irreversible tasks with high success rates (64.3% and 71.4% respectively) without any mention of refusal or safety checks. While the simulation is sandboxed, the paper must explicitly address the dual-use risk: if agents are trained to maximize success on these tasks in simulation, they may learn to bypass safety guardrails when deployed on real devices. The authors should discuss whether the training process (GRPO) inadvertently optimizes for "jailbreaking" behaviors and propose a mitigation strategy, such as incorporating safety rewards or refusal training in the benchmark.

Second, while the "Ethical Considerations" section mentions "digital-literacy education" as a positive use case, it lacks a concrete policy for preventing misuse. The platform enables the generation of synthetic data and the training of agents capable of navigating complex apps. There is a risk that this technology could be repurposed for automated social engineering, credential harvesting, or fraud. The authors should add a specific "Responsible Use" statement or a code of conduct for users of the MobileGym benchmark and the associated models, explicitly prohibiting the use of the platform for malicious automation.

Finally, the "Datasheet for Datasets" (§1) acknowledges biases, including an "English-speaking demographic focus" and "limited accessibility coverage." The paper should elaborate on the safety implications of these biases. For instance, an agent trained primarily on English interfaces might fail catastrophically or behave unpredictably when interacting with non-English apps or accessibility features, potentially leading to user harm or data loss. A plan to expand the benchmark's linguistic and accessibility coverage to mitigate these risks would strengthen the ethical standing of the work.

Overall, the paper is safe to publish provided these specific risks are acknowledged and mitigated through clearer discussion and usage guidelines.
