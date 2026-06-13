---
action_items:
- id: fa559498eb05
  severity: science
  text: Address selection bias in ground-truth construction (Section 3.2). Only instances
    solvable by >=2 agents are included, limiting generalizability to hard/unresolved
    issues.
- id: 43c517a4c46c
  severity: science
  text: Explain the high correlation (r=0.950) in Table 3 (Section 5.2). Verify no
    data leakage exists between exploration metrics and downstream repair validation.
- id: dd6a944b74c5
  severity: science
  text: Clarify the 'LLM-based promotion' step in GT refinement (Appendix B). Provide
    audit logs or inter-annotator agreement to ensure reproducibility.
artifact_hash: 4f74e000b69de2d67ea831b1e89044d5ab493f7912139c51fbf7fc4d4c2ada92
artifact_path: projects/PROJ-687-swe-explore-benchmarking-how-coding-agen/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-13T21:53:15.751088Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The manuscript presents a substantial dataset (848 instances, 203 repos) and rigorous downstream validation protocols. However, specific concerns regarding the evidence base limit confidence in the central claims.

First, the ground-truth construction (Section 3.2) relies on the intersection of successful agent trajectories. This introduces selection bias: instances where current agents fail are excluded. Consequently, the benchmark measures "exploration of solvable problems" rather than general repository understanding. This limits the external validity of the claim that SWE-Explore evaluates "repository exploration" broadly. The dataset is skewed toward problems already solved by SOTA models (GPT-5.4, etc.), potentially underestimating the difficulty of exploration in harder cases.

Second, the correlation analysis in Section 5.2 shows Context Efficiency achieving $r=0.950$ with downstream repair rates. This is anomalously high for software engineering metrics. While it supports the paper's thesis, it risks indicating data leakage between the exploration definition and the repair validation (e.g., if the repair agent relies heavily on the exact lines provided, correlation becomes trivial). The authors must verify no information leakage exists between the GT lines used for scoring and the context provided to the repair agent.

Third, the refinement of ground truth via "LLM-based promotion" (Section 3.2, Appendix B) introduces subjectivity. Without reporting inter-annotator agreement or specific criteria for promotion, reproducibility is compromised. The claim that line-level evaluation adds information (Section 5.3) is supported by the data, but the low recall ($\text{Rec}_\ell \approx 0.14$--$0.19$) indicates the GT definition may be too strict or the task too hard for current models.

Finally, the controlled context degradation (Section 5.4) provides strong evidence for the "missing context" hypothesis. However, the sample size for this ablation needs to be explicitly stated for the degradation curves to assess statistical significance.

Overall, the evidence is promising but requires clarification on GT validity and correlation robustness before the claims can be fully accepted.
