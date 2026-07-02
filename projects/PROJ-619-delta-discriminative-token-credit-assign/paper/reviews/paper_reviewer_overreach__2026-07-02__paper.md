---
action_items:
- id: 673709e8bc9c
  severity: science
  text: Claims of 'generalization' to code/Olmo3 lack statistical significance tests
    or per-benchmark variance, unlike main math results. Provide full stats or temper
    claims to 'preliminary promise'.
- id: 071257aca368
  severity: writing
  text: Conclusion claims 'consistent' OOD improvement, but 14B MMLU-Pro gain (1.63
    pts) lacks significance testing. Clarify 'consistent' scope or add per-task significance
    tests.
- id: 83472c1466cb
  severity: writing
  text: Theoretical claim of 'reshaping update direction' relies on a proxy gradient
    and K=1 step. Explicitly acknowledge this approximation in limitations to avoid
    over-claiming true gradient geometry.
artifact_hash: 8558369ae7497b07133b578546b356e5acc6d5d811b01a15639e1519377b2963
artifact_path: projects/PROJ-619-delta-discriminative-token-credit-assign/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T16:22:25.978344Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several strong claims regarding the generalization and consistency of DelTA's performance that appear to exceed the statistical rigor presented in the supplementary experiments.

First, the Abstract and Introduction claim that DelTA "generalizes to other backbones" and "improves code generation." While the Appendix provides average scores for Olmo3-7B and code benchmarks (HumanEval+, MBPP+, LCB), these sections lack the rigorous statistical analysis (e.g., Mann-Whitney U tests, variance across seeds) provided for the main math benchmarks. A single average improvement on code (47.7 to 49.5) without per-benchmark significance or variance bars makes the claim of "improvement" potentially over-optimistic if the gain is driven by a single dataset. The authors should either provide the full statistical breakdown for these secondary tasks or qualify the language to reflect that these are preliminary observations.

Second, the Conclusion states DelTA "consistently improves... out-of-domain tasks." The OOD results (Appendix E.5) show gains on GPQA-D and MMLU-Pro. However, the gain on MMLU-Pro for the 14B model is 1.63 points (66.77 to 68.40). Without a significance test for this specific comparison, labeling it as a "consistent" improvement across tasks is an over-interpretation of the data. The term "consistent" implies a robust, statistically significant trend, which is not demonstrated for the 14B OOD results.

Finally, the theoretical framing claims DelTA "reshapes the update direction" by amplifying specific gradient directions. This is derived from a "local discriminator view" using a proxy gradient $(1-p_t)$ and a single refinement iteration ($K=1$). The paper does not sufficiently discuss the gap between this proxy-based approximation and the true gradient geometry. Claiming to reshape the *actual* update direction based on a proxy and a single step is a theoretical overreach. The limitations section should explicitly state that the "discriminator view" is an approximation and that the true gradient alignment may differ from the proxy-based analysis.
