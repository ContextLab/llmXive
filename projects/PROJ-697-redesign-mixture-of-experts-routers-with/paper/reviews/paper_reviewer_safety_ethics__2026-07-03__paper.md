---
action_items:
- id: 5ee968d559c7
  severity: writing
  text: The 'Ethical Considerations' section (lines 13-24) and 'Broader Impact' section
    (lines 1085-1093) acknowledge dual-use risks but lack concrete mitigation strategies.
    Explicitly detail proposed technical safeguards (e.g., specific watermarking techniques,
    access control protocols) or policy frameworks the authors intend to support,
    rather than generic calls for 'usage policies.'
- id: 1c76f830d2b3
  severity: writing
  text: The 'Reproducibility' section (lines 1065-1072) and code availability statement
    (line 1067) cite a placeholder GitHub URL ('https://github.com/yourorg/mixture-of-experts-routers')
    and a generic commit hash. For a paper claiming efficiency gains in large-scale
    training, the absence of a verifiable, functional code repository prevents independent
    safety auditing of the implementation for potential instability or unintended
    behaviors.
- id: ce76068d5c25
  severity: writing
  text: The manuscript states training data (FineWeb-Edu) contains no PII (lines 1078-1080).
    However, it does not address the potential for the model to memorize and regurgitate
    sensitive information present in the broader pretraining corpus or the specific
    'Math' and 'Code' datasets used for evaluation. A brief discussion on memorization
    risks or privacy-preserving training techniques would strengthen the safety profile.
artifact_hash: 34fabb025335fc2fcf0855d53316dbb275a62eee03c0f1ad1b72c49ea11b1392
artifact_path: projects/PROJ-697-redesign-mixture-of-experts-routers-with/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T10:00:09.094941Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript addresses safety and ethics primarily through a dedicated 'Ethical Considerations' section (lines 13-24) and a 'Broader Impact' section (lines 1085-1093). The authors correctly identify the dual-use nature of their work, noting that improved efficiency in Mixture-of-Experts (MoE) models could lower barriers for generating disinformation or malicious content. They also appropriately mention data privacy regarding the use of public benchmarks.

However, the current treatment of these issues remains high-level and generic. The 'Ethical Considerations' section advises practitioners to "adopt usage policies" and "employ appropriate anonymisation techniques" but does not propose or evaluate specific technical mitigations that could be integrated into the router design itself or the deployment pipeline. Given the paper's focus on a fundamental architectural change, a more concrete discussion on how this specific router design might interact with safety mechanisms (e.g., does the power iteration step affect the model's ability to be aligned or watermarked?) would be valuable.

Furthermore, the 'Reproducibility' section (lines 1065-1072) and the code availability statement in the preamble (line 1067) contain placeholder URLs (`https://github.com/yourorg/mixture-of-experts-routers`) and a non-functional commit hash. For a method claiming to improve training stability and efficiency in large-scale models, the inability to inspect the actual implementation prevents the community from auditing the code for potential safety-critical bugs, numerical instabilities, or unintended side effects that could arise during deployment. While external code hosting is acceptable, the links provided must be valid and point to the actual artifacts used in the experiments.

Finally, while the authors state that training data lacks PII, there is no discussion regarding the risk of the model memorizing sensitive information from the broader pretraining corpus (FineWeb-Edu) or the evaluation datasets (Math/Code). A brief acknowledgment of memorization risks and any steps taken to mitigate them would align better with current best practices in responsible AI research.
