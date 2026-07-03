---
action_items:
- id: aab141e992a1
  severity: writing
  text: The 'Broader Impacts' section (Section 7) acknowledges over-abstention risks
    but lacks a concrete mitigation strategy for high-stakes domains (e.g., medical
    or legal agents). Explicitly state that the proposed abstention mechanism is not
    a substitute for human oversight in critical applications and define specific
    failure modes where abstention could cause harm (e.g., denial of service).
- id: dca4295176cd
  severity: writing
  text: The dataset construction for WebShop and Terminal-Bench involves rewriting
    instructions to create 'False Premise' or 'Underspecified' scenarios (Section
    3, Appendix D). While reviewed by authors, the process relies on LLMs (GPT-5.4-mini)
    to generate adversarial examples. Add a statement confirming that human verification
    was performed on a random sample of these generated adversarial prompts to ensure
    they do not inadvertently contain harmful, biased, or sensitive content.
- id: 8c0624fd049d
  severity: writing
  text: The evaluation includes medical datasets (MediQ) and bias benchmarks (BBQ)
    within the Interactive QA tasks (Section 3, Appendix D). The paper does not explicitly
    mention whether the evaluation protocol included safety filters or if the 'ABSTAIN'
    action was the only allowed response for sensitive topics. Clarify if the agents
    were evaluated on their ability to refuse harmful queries in these specific subsets,
    or if the focus was solely on factual unanswerability.
artifact_hash: 38d0e8e4fb458c680aadb1d4bcdffd2c4f641f3bec33db525a174585bed1f06b
artifact_path: projects/PROJ-808-agentic-abstention-do-agents-know-when-t/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T01:29:30.006158Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper addresses a critical safety-adjacent capability: Agentic Abstention, defined as the ability of an agent to recognize when a task is infeasible and stop acting. This is a positive contribution to safety, as it directly targets the reduction of hallucinated completions and unnecessary tool use, which can lead to resource exhaustion or unintended side effects in real-world deployments.

However, from a safety and ethics lens, the manuscript requires minor revisions to fully address the implications of its findings and methodology:

1.  **High-Stakes Deployment Risks:** The "Broader Impacts" section (Section 7) correctly identifies that over-abstention can frustrate users. However, it does not sufficiently address the risks in high-stakes domains (e.g., medical diagnosis, legal advice, or autonomous driving). In these contexts, an agent that fails to abstain (false negative) could cause direct harm, while an agent that abstains too readily (false positive) could deny necessary services. The authors should explicitly state that the current benchmarks and the proposed \method are not sufficient for deployment in such high-risk environments without human-in-the-loop oversight. A sentence clarifying the "human oversight" requirement for critical applications is necessary.

2.  **Adversarial Dataset Construction:** The construction of the WebShop and Terminal-Bench abstention datasets relies heavily on LLMs (specifically GPT-5.4-mini) to rewrite instructions into "False Premise" or "Underspecified" categories (Section 3, Appendix D). While the authors mention a review process, there is no explicit confirmation that these generated adversarial prompts were screened for safety. There is a risk that the rewriting process could inadvertently introduce toxic, biased, or sensitive content into the test set. The authors should add a statement confirming that a human review or safety filter was applied to the generated adversarial examples to ensure they do not contain harmful content.

3.  **Sensitive Benchmark Integration:** The evaluation includes datasets like MediQ (medical questions) and BBQ (bias benchmark) (Section 3, Appendix D). The paper focuses on "unanswerability" but does not explicitly discuss how the agents handled sensitive or potentially harmful queries within these datasets. Did the agents abstain on sensitive topics as a safety measure, or did they attempt to answer? The authors should clarify if the evaluation protocol included specific safety constraints for these subsets or if the "ABSTAIN" action was the only safe response for sensitive topics. This distinction is crucial for understanding the agent's safety alignment.

Overall, the paper presents a valuable framework for improving agent reliability, but the safety implications of its methodology and the limitations of its applicability to high-risk scenarios need to be more explicitly articulated.
