---
action_items:
- id: 49431f68809c
  severity: writing
  text: Abstract claims specific gains (+3.34, +4.00, etc.) not explicitly derived
    in tables. Tables show different averages (e.g., +3.06 math). Clarify or remove
    precise numbers to avoid over-claiming precision.
- id: 456b7c0cbc69
  severity: writing
  text: Claim to 'establish a general benchmark' overstates contribution. The work
    performs a unified evaluation on existing datasets, not creating a new benchmark.
    Rephrase to 'conduct a unified evaluation'.
- id: d94c2710b00e
  severity: science
  text: Claim that TrOPD specifically mitigates 'K1 reverse-KL estimator' instability
    lacks direct evidence isolating K1 failure modes. Provide training curves or analysis
    linking stability gains specifically to K1 mitigation.
artifact_hash: 74f03d7ab60f5026cfa7c71878897ef40634611691a4c76f5e68e8e21f3101c9
artifact_path: projects/PROJ-659-trust-region-on-policy-distillation/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T18:40:38.271497Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper exhibits over-claiming in three primary areas regarding the specificity of results, the definition of contributions, and the mechanistic attribution of success.

First, the Abstract and Introduction assert that TrOPD achieves specific point improvements: "+3.34, +4.00, +5.11, and +6.18 points on math, code, instruction following, and STEM benchmarks." However, the provided tables (Table 1, Table 2, Table 3) do not explicitly display these exact aggregate numbers. For instance, Table 2 reports an average improvement of +3.06 on math and +2.63 on general domains, which conflicts with the specific breakdown in the abstract. Without a transparent derivation or a table showing these exact per-domain deltas, the claim of these precise figures constitutes an over-claim of precision and potentially misrepresents the data's granularity.

Second, the Contributions section states, "We establish a general benchmark for reasoning-oriented OPD." The manuscript describes evaluating existing methods (OPD, EOPD, REOPOLD) on existing datasets (AIME, LiveCodeBench, etc.) under unified settings. While this constitutes a valuable "unified evaluation" or "comparative study," it does not meet the standard definition of "establishing a benchmark," which typically implies creating a new dataset, metric, or protocol. This phrasing overstates the novelty of the experimental setup.

Finally, the claim that the method specifically "mitigates the optimization difficulty of the K1 reverse-KL estimator" (Abstract) is a strong causal assertion. While the paper demonstrates improved stability and performance, the evidence provided (primarily final accuracy scores and a referenced gradient norm figure) does not explicitly isolate the K1 estimator's instability as the sole or primary failure mode being addressed, distinct from general distribution mismatch issues. The paper would benefit from more direct evidence, such as training curves showing collapse in baselines specifically due to K1 variance, to support this specific mechanistic claim.
