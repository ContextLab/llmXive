---
action_items:
- id: b94d8dad2aaf
  severity: science
  text: Section 3.2 lists 'GPT-5.4', 'Gemini-3-Pro', and 'Sonnet-4.6' as source models
    for ground truth. These versions do not exist. Correct to actual existing models
    (e.g., GPT-4o) to validate the trajectory-grounded claim.
- id: 94ef4bd14046
  severity: science
  text: Table 1 claims SWE-Explore is the only benchmark with 'Trajectory-Grounded
    GT'. ContextBench (li2026contextbench) uses agent trajectories for gold contexts.
    Verify if this distinction is accurate or if the table entry is incorrect.
- id: 1ebd51094e69
  severity: writing
  text: Abstract claims r=0.950 correlation on n=150 instances. Explicitly state the
    p-value in the text to fully support the statistical significance of the 'strong
    tracking' claim.
artifact_hash: d01bf725e90093797f2151085112b0bd34f0dac442648b3b22aae07b0ee791b3
artifact_path: projects/PROJ-687-swe-explore-benchmarking-how-coding-agen/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T20:43:57.363563Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The paper makes several strong factual claims regarding the novelty of the benchmark and the statistical validity of its results. While the overall methodology is sound, there are critical factual errors regarding the model versions cited and potential inaccuracies in the comparative benchmark table that require correction.

First, in Section 3.2 ("Ground-Truth Annotation") and the Abstract, the authors list "GPT-5.4", "Gemini-3-Pro", "Sonnet-4.6", "GLM-5.1", and "Kimi-K2.6" as the source models used to generate the successful trajectories for ground truth. As of the paper's stated publication context (2026), these specific version numbers (e.g., GPT-5.4, Sonnet-4.6) do not correspond to any publicly released or known model versions (current generations are GPT-4o, Claude 3.5/4, Gemini 1.5, etc.). This appears to be a hallucination or a placeholder error. If these are hypothetical future models, the claim that the ground truth is derived from "successful agent trajectories" of these specific models is factually unsupported. The authors must replace these with actual, existing model versions (e.g., GPT-4o, Claude 3.5 Sonnet) or clarify the nature of these models to ensure the claim of "trajectory-grounded supervision" is valid.

Second, the comparative claim in Table 1 regarding "Trajectory-Grounded GT" requires verification. The table marks ContextBench (li2026contextbench) as lacking this feature. However, the Related Work section describes ContextBench as introducing "human-annotated gold contexts and scores retrieval over agent trajectories." If ContextBench's gold contexts are derived from or validated against agent trajectories, the distinction made in Table 1 might be semantically imprecise. The authors should verify the exact methodology of ContextBench to ensure the claim that SWE-Explore is the *only* benchmark with trajectory-grounded ground truth is accurate.

Finally, regarding the statistical claim in the Abstract and Section 5.2: the paper states a correlation of r=0.950 on n=150 instances. While the authors mention adding confidence intervals, the text does not explicitly report the p-value for this correlation. Given the high correlation, the claim that metrics "strongly track" repair behavior is plausible, but explicitly stating the statistical significance (p < 0.05) in the text would strengthen the factual support for this conclusion.

These issues are primarily factual accuracy concerns regarding the existence of cited models and the precision of comparative claims. Correcting the model names is essential for the scientific validity of the ground-truth construction.
