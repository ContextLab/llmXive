---
action_items:
- id: d77d9816a08e
  severity: science
  text: Provide the exact prompt template and hyperparameters used by the LLM-based
    analyzer (A) to extract skills, including temperature, max tokens, and few-shot
    examples if any. Currently, the analyzer is a black box.
- id: 17221d258bf7
  severity: science
  text: Define the algorithm or heuristic used to identify 'critical timesteps' (C_tau).
    The paper claims a 'critical-first' routing mechanism but does not specify how
    the detector determines criticality, making the core contribution un-reproducible.
- id: c4e15d63f99f
  severity: science
  text: Include a quantitative analysis of the 'criticality detector' error rate.
    The theoretical Proposition 3.1 relies on the assumption of perfect or near-perfect
    detection; without empirical data on detector accuracy, the theoretical bound
    is speculative.
- id: b11e807f30ff
  severity: science
  text: 'Clarify the training loop timing: Does the skill extraction happen in the
    same iteration as the policy update, or is there a lag? If the analyzer uses the
    current policy to generate skills for the current policy, explain how this avoids
    immediate mode collapse or reward hacking.'
- id: 9edc8dfe2f03
  severity: writing
  text: Report the computational overhead of the skill extraction and routing steps.
    Given the use of an external LLM (GLM-5.2) for every trajectory, the training
    cost is likely significantly higher than standard GRPO; this must be quantified.
artifact_hash: ebe41e02149487ccd15d4c76bf5323b1b6f5d76f7c2ba35eb80cabef31288797
artifact_path: projects/PROJ-795-opid-on-policy-skill-distillation-for-ag/paper/metadata.json
backend: dartmouth
feedback: Critical methodological opacity in skill extraction and routing prevents
  reproducibility; theoretical claims lack empirical validation of the "criticality
  detector."
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T00:00:26.002057Z'
reviewer_kind: llm
reviewer_name: paper_reviewer
score: 0.0
verdict: major_revision_science
---

# Free-form review body

## Strengths
- **Clear Motivation**: The paper effectively identifies the sparsity of rewards in long-horizon agentic tasks and proposes a logical solution using on-policy skill distillation.
- **Comprehensive Evaluation**: The experiments cover diverse benchmarks (ALFWorld, WebShop, Search-based QA) and multiple model sizes, demonstrating consistent improvements over strong baselines like GRPO and Skill-GRPO.
- **Inference Efficiency**: A key strength is the demonstration that the distilled policy does not require skill retrieval at inference time, unlike methods such as Skill-GRPO which degrade significantly without external context.
- **Theoretical Framework**: The inclusion of theoretical propositions regarding routing optimality and occupancy matching adds depth to the methodological contribution.

## Concerns
- **Methodological Opacity (Critical)**: The core of the OPID method relies on an "LLM-based analyzer" to extract skills and identify "critical timesteps." The paper fails to provide the specific prompt, the criteria for identifying criticality, or the algorithm used for this detection. Without this, the "critical-first routing" mechanism is a black box, and the results cannot be reproduced.
- **Unvalidated Theoretical Assumptions**: Proposition 3.1 (Routing optimality) assumes a "perfect criticality detection" or bounds the error based on detector probability. The paper provides no empirical data on the accuracy of the criticality detector. If the detector is noisy, the theoretical guarantees may not hold, and the routing could introduce noise rather than signal.
- **Training Dynamics and Cost**: The use of an external LLM (GLM-5.2) to analyze every trajectory for skill extraction introduces significant computational overhead. The paper does not quantify this cost or discuss the training time compared to baselines.
- **Ablation of the Analyzer**: There is no ablation study on the quality of the extracted skills. It is unclear if the performance gain comes from the distillation mechanism itself or simply from the high-quality supervision provided by the external analyzer.
- **Reproducibility of "Critical" Steps**: The definition of a "critical timestep" is vague. Is it based on a change in state, a specific action type, or a heuristic? The lack of a concrete definition makes the "step-level skill" concept difficult to verify.

## Recommendation
The paper presents a promising direction for agentic RL but suffers from significant methodological opacity that prevents reproducibility. The core innovation—critical-first skill routing—relies entirely on an undefined "criticality detector" and an opaque analyzer. The theoretical claims regarding routing optimality are not supported by empirical validation of the detector's performance.

To proceed, the authors must:
1.  **Fully disclose the analyzer**: Provide the exact prompt, parameters, and logic used to extract skills and identify critical timesteps.
2.  **Validate the detector**: Include an analysis of the criticality detector's accuracy and its impact on performance.
3.  **Clarify the training loop**: Explain the timing of skill extraction relative to policy updates to rule out immediate mode collapse.
4.  **Quantify overhead**: Report the computational cost of the skill extraction phase.

Without these clarifications, the scientific contribution cannot be verified, and the paper requires a major revision of the research methodology section before it can be considered for publication.
