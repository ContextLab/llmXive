---
action_items:
- id: be4897d677d8
  severity: writing
  text: The claim that CDS yields 'up to a 5.42 percentage-point gain' (Abstract)
    is not supported by Table 1 in section/curvature.tex, where the maximum observed
    gain is 5.24 points (geometry, gpt-5.2, 16 shots). The text must be corrected
    to match the empirical data or the specific instance yielding 5.42 must be cited.
- id: b257b2f476dc
  severity: writing
  text: The paper claims 'consistent gains across math and narrative reasoning' in
    the Conclusion, but Table 1 shows CDS underperforms the baseline on number_theory
    for Qwen3 (87.78 vs 86.30 at 64 shots is a gain, but 87.22 vs 86.30 at 64 shots
    is a gain, wait, 87.78 > 86.30 is a gain. However, at 128 shots, 90.74 vs 90.93
    is a loss). The claim of 'consistent' gains is an overstatement given the performance
    drop at 128 shots for Qwen3 on number_theory.
- id: 5f16d6f349f5
  severity: writing
  text: The abstract states similarity-based retrieval 'fails on reasoning' because
    'semantic similarity poorly predicts procedural compatibility.' While the data
    shows similarity-based retrieval often underperforms random/original baselines,
    the paper does not definitively prove the *mechanism* is solely procedural incompatibility
    without ruling out other factors (e.g., noise in the embedding space for long
    CoT texts). The causal link is slightly over-claimed.
artifact_hash: da80d19d18126d829231e022c90784234c941daee73db4750a219950884e0e6f
artifact_path: projects/PROJ-563-many-shot-cot-icl-making-in-context-lear/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T23:25:13.850901Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several strong claims regarding the behavior of many-shot CoT-ICL that slightly exceed the strict bounds of the presented data, particularly in the Abstract and Conclusion.

First, the Abstract claims CDS yields "up to a 5.42 percentage-point gain." However, a review of Table 1 in `section/curvature.tex` reveals the maximum gain is 5.24 points (geometry, gpt-5.2, 16 shots: 81.21 vs 75.99). The specific value of 5.42 does not appear in the provided tables. This is a clear instance of over-claiming a specific metric that is not supported by the visible data.

Second, the Conclusion states that CDS yields "consistent gains across math and narrative reasoning." While gains are observed in many settings, Table 1 shows that for the Qwen3 model on the number_theory task at 128 demonstrations, CDS (90.74) actually underperforms the baseline (90.93). Similarly, for Qwen3 on geometry at 128 shots, the gain is marginal (73.90 vs 73.07). Describing these results as "consistent" glosses over the instances where the method fails to improve or slightly degrades performance compared to the baseline. The claim should be tempered to reflect that gains are "frequent" or "significant in specific regimes" rather than universal.

Third, the paper attributes the failure of similarity-based retrieval on reasoning tasks entirely to "procedural incompatibility" (Abstract, Section 4.3). While the qualitative example in Appendix A supports this, the quantitative results (Figure 4) only show that similarity-based selection performs worse than random or original ordering. They do not strictly isolate "procedural incompatibility" as the *sole* cause; it is possible that the embedding model (Qwen3-Embedding-4B) simply fails to capture the necessary features for long CoT texts, or that the "most-similar" set introduces a different type of bias. The causal mechanism is presented as a definitive fact rather than a well-supported hypothesis.

Finally, the claim in the Abstract that "standard many-shot rules do not transfer" is slightly broad. The paper shows they do not transfer to *reasoning* tasks for *non-reasoning* LLMs, but they do transfer to some extent for reasoning-oriented LLMs (which show positive scaling). The distinction is made in the body, but the abstract's phrasing suggests a total breakdown of prior rules, which is an over-generalization.
