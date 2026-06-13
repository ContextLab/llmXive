---
action_items:
- id: 954be2ecc7d7
  severity: science
  text: Ground truth filtering with >=2 successful trajectories biases benchmark toward
    solvable instances. Claim of generalizability to unsolved problems is unsupported.
    Add discussion of selection bias in Section 3.3.
- id: 28a2b8f6f7d5
  severity: science
  text: Correlation r=0.950 in Table 2 is computed on n=150 subset without cross-validation
    across model families or difficulty strata. This risks overfitting. Add uncertainty
    bounds or holdout analysis.
- id: 1ca4305c902b
  severity: writing
  text: Multilingual coverage claim of 10 languages is misleading because 64.5% are
    Python per Appendix D. Temper generalization claims about cross-language exploration
    capabilities.
- id: 5dd4e54dad5c
  severity: science
  text: Downstream validation uses restricted-context environment with fixed agent.
    This creates circular validation where exploration quality is validated against
    a repair task dependent on same exploration output. Acknowledge this limitation
    in Section 4.2.
- id: 27c13708fad6
  severity: writing
  text: Oracle degradation experiment in Section 4.4 concludes missing context is
    dominant failure mode without acknowledging this may be specific to repair agent
    capabilities. Qualify the conclusion.
artifact_hash: 4f74e000b69de2d67ea831b1e89044d5ab493f7912139c51fbf7fc4d4c2ada92
artifact_path: projects/PROJ-687-swe-explore-benchmarking-how-coding-agen/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-13T21:51:01.560052Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several claims that extend beyond what the experimental design and data support, particularly around generalizability and causal relationships.

**Ground Truth Selection Bias (Section 3.3):** The benchmark retains only instances with >=2 successful agent trajectories. This inherently filters out unsolvable or extremely difficult problems, yet the paper positions SWE-Explore as a general repository exploration benchmark. The Abstract claims coverage of 848 issues across 10 programming languages without qualifying that these are pre-filtered to solvable instances. This overstates the benchmark's utility for evaluating exploration on hard, unsolved problems.

**Correlation Overstatement (Section 4.2, Table 2):** The reported Pearson correlation of r=0.950 between Context Efficiency and downstream resolve rate is exceptionally high. This is computed across explorers on a 150-instance subset. The paper does not report confidence intervals, cross-validation, or whether this correlation holds across different model families or difficulty levels. Such a strong correlation without uncertainty quantification risks being an artifact of the specific experimental setup.

**Multilingual Claim Inflation (Appendix D):** The paper emphasizes 10 programming languages but Python comprises 64.5% of instances (547/848). Claims about cross-language exploration capabilities should be qualified given this skew.

**Circular Validation (Section 4.2):** The downstream repair validation feeds explorer output to a fixed agent and measures resolution. This creates a circular relationship where exploration quality is validated against a repair task that depends on the exploration output itself. The paper treats this as independent validation when it is inherently coupled.

**Oracle Experiment Interpretation (Section 4.4):** The conclusion that missing context is the dominant failure mode derives from a single repair agent (Mini-SWE-Agent) under specific conditions. This may reflect that agent's capabilities rather than universal exploration properties. The conclusion should be more cautious.

These issues require revision to align claims with the actual scope and limitations of the experimental evidence.
