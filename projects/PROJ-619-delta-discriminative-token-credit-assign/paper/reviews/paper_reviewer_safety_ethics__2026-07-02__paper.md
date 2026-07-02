---
action_items:
- id: 998077215a4d
  severity: writing
  text: The 'Broader impacts' section (Appendix) is too generic. Explicitly detail
    specific dual-use risks (e.g., generating adversarial code, bypassing safety filters
    in reasoning models) and propose concrete mitigation strategies beyond 'responsible
    deployment'.
- id: 7d7911501996
  severity: writing
  text: The paper uses 'DeepMath-103K' and benchmarks like AIME/HMMT. Clarify the
    data provenance and consent status. If scraped from the web, confirm compliance
    with terms of service and absence of PII or copyrighted material in the training
    set.
- id: c0652e0bb59d
  severity: writing
  text: The method reweights token gradients to amplify 'discriminative' signals.
    Discuss potential for 'reward hacking' or amplifying subtle biases in the reward
    function (e.g., favoring specific reasoning styles that correlate with demographic
    biases in the training data).
artifact_hash: 8558369ae7497b07133b578546b356e5acc6d5d811b01a15639e1519377b2963
artifact_path: projects/PROJ-619-delta-discriminative-token-credit-assign/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T16:22:38.249066Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript addresses safety and ethics primarily through a brief "Broader impacts" appendix, which is insufficient for a method designed to optimize reasoning models. While the authors acknowledge the potential for misuse in "harmful code/content generation," the discussion lacks specificity regarding the unique risks introduced by DelTA's mechanism.

Specifically, the method amplifies token gradients that are discriminative between positive and negative advantage sides. In a safety context, this could inadvertently amplify "jailbreak" patterns or adversarial reasoning chains if the reward function (even a verifiable one like math correctness) is imperfectly aligned or if the "negative" side contains subtle safety violations that are not penalized. The review requires a more rigorous analysis of how DelTA might interact with safety filters or amplify biases present in the "DeepMath-103K" dataset.

Regarding data ethics, the paper relies on "DeepMath-103K" and benchmarks like AIME and HMMT. The authors must explicitly state the data provenance. If the dataset was scraped from the web, there must be a statement confirming that it does not contain Personally Identifiable Information (PII) and that the usage complies with the terms of service of the source platforms. The current text assumes the dataset is benign without justification.

Finally, the "Broader impacts" section should be expanded to include a concrete mitigation strategy. For instance, if DelTA is used to train a model for code generation, how does the authors' framework prevent the model from learning to generate malicious code that happens to pass a functional test? A generic call for "responsible deployment" is not a sufficient safety control for a high-impact RL method.
