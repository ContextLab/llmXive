---
action_items:
- id: fc30089b26e2
  severity: writing
  text: 'The claim that ZPPO ''approaches'' the 27B teacher on AIME25 (70.0 vs 70.0)
    in Sec. 5.2.2 is an over-interpretation of a single data point. The 9B student
    matches the teacher on one specific benchmark but lags significantly on others
    (e.g., HLE: 9.8 vs 16.0). The text should qualify this as ''matching on specific
    benchmarks'' rather than a general approach to teacher capability.'
- id: a957dfd576d9
  severity: science
  text: The assertion that 'Distillation hurts generalization' (Finding 1) is slightly
    overstated given the confidence intervals in Tab. 10 (Appendix). For Video benchmarks
    at 4B/9B, the CI for ZPPO vs Best-non-ZPPO includes zero ([-0.24, +0.90] and [-0.02,
    +0.86]). The conclusion should acknowledge that the superiority of ZPPO over all
    baselines is not statistically significant in these specific high-scale video
    regimes.
- id: f11dcf3d8e1c
  severity: writing
  text: The paper claims BCQ/NCQ are 'super-additive' (Sec. 3.4, Sec. 5.3) based on
    macro-averaged gains. However, the ablation tables (Tab. 7, Tab. 8) show that
    for the 0.8B model on Video benchmarks, the gain from BCQ+NCQ is marginal compared
    to GRPO+Buffer. The term 'super-additive' implies a consistent multiplicative
    effect across all scales and domains, which the data does not uniformly support.
    The claim should be restricted to the specific VLM/LLM regimes where the effect
    is strong.
artifact_hash: 0fd8fa2b8ede4e304df4503c08bd0823fb3038495b7a89b759c4ee4216df60db
artifact_path: projects/PROJ-731-zone-of-proximal-policy-optimization-tea/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T03:38:55.448455Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several strong claims regarding the universality and magnitude of ZPPO's improvements that slightly exceed the statistical and empirical evidence provided.

First, the claim in Section 5.2.2 that a 9B ZPPO student "approaches the 27B teacher" is an over-generalization based on a single benchmark (AIME25). While the scores match (70.0 vs 70.0), the student lags significantly on other critical benchmarks like HLE (9.8 vs 16.0) and VBlind. The text should be tempered to state that the student matches the teacher on *specific* benchmarks where the teacher is not saturated, rather than implying a general convergence of capability.

Second, the "Finding" box in the Introduction and Section 5.1 asserts that distillation "hurts generalization" while ZPPO improves it. While the macro-averages support this, the cluster bootstrap confidence intervals in Table 10 (Appendix) reveal that for Video benchmarks at 4B and 9B, the difference between ZPPO and the best non-ZPPO baseline is not statistically significant (CIs include zero: [-0.24, +0.90] and [-0.02, +0.86]). Claiming a definitive "hurt" vs "improve" dichotomy without qualifying these specific non-significant regimes overstates the robustness of the finding.

Finally, the description of the BCQ/NCQ combination as "super-additive" (Section 3.4, Section 5.3) suggests a consistent, compounding effect across all scales. The ablation results (Tables 7 and 8) show that for the smallest model (0.8B) on Video benchmarks, the incremental gain of adding both components is minimal compared to the buffer-only baseline. The term "super-additive" should be qualified to reflect that this phenomenon is primarily observed in the VLM and LLM domains and at larger student scales, rather than being a universal property of the method.
