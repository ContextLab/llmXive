---
action_items:
- id: 60c7b56978e5
  severity: writing
  text: Abstract claims 'consistent improvements across model families,' but Table
    1 only shows Gemini and Qwen. Include results for GLM/Kimi in the main table or
    hedge to 'tested families' to support the generalization.
- id: 071249c4743c
  severity: writing
  text: Title/Abstract imply 'general visual agents,' but experiments are limited
    to GUI and two games. Add a limitation explicitly restricting the scope to screen-based
    and game environments, excluding robotics or video.
- id: f0bd97b75b94
  severity: writing
  text: Abstract claims the method 'complements internal priors' generally, but evidence
    is limited to OpenCUA-derived skills on specific benchmarks. Narrow the claim
    to 'complements priors in screen-based task execution'.
artifact_hash: d1f8365f26381f8307ae3c2777500a8f5e24701d5ef1d5e42dce305039a248a5
artifact_path: projects/PROJ-599-mmskills-towards-multimodal-skills-for-g/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-04T00:02:20.772235Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper presents a compelling framework for multimodal skills, but the rhetoric in the abstract and conclusion occasionally exceeds the specific scope of the reported experiments.

First, the abstract asserts "consistent improvements across model families." While the text mentions testing GLM-5V and Kimi-K2.6 (Appendix Fig 2), the primary results table (Table 1) only explicitly displays data for Gemini 3.1 Pro and Qwen3-VL-235B. The claim of "consistency" is not fully licensed by the highlighted data in the main body, as the reader cannot verify the trend for the other families from the primary evidence presented. The authors should either include the full comparative data in the main table or hedge the claim to "tested model families" to avoid implying a universal trend that isn't visually summarized in the key results.

Second, the scope of "general visual agents" in the title and abstract is broader than the evidence. The experiments are confined to desktop GUI environments (OSWorld, macOSWorld) and two specific game environments (Minecraft, Mario). There is no evidence presented for embodied agents (robotics), video analysis, or other visual domains. While the method *could* apply there, the paper's rhetoric suggests a broader validation than the "screen-based and game" reality of the data. A more precise limitation acknowledging that the "multimodal procedural knowledge" was only validated in screen-based contexts would align the claim with the evidence.

Finally, the conclusion states the method "improves GUI and game agents," which is accurate, but the abstract's framing of "complementing internal priors" is a strong theoretical claim. The paper demonstrates this complementarity only within the specific constraints of the OpenCUA-derived skills and the tested benchmarks. The claim is not false, but it is presented as a general principle rather than a finding specific to the tested domain. Narrowing the language to reflect the specific domain of validation (screen-based tasks) would tighten the link between the rhetoric and the demonstrated scope.

These are primarily issues of framing and precision. The paper is a solid contribution, but tightening the scope of the claims to match the specific experimental boundaries would eliminate the overreach.
