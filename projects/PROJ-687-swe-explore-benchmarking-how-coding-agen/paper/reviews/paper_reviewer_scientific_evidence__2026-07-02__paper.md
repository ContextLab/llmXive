---
action_items:
- id: 01e11196c1bf
  severity: science
  text: The correlation analysis in Table 3 (Section 5.2) relies on a subset of n=150
    instances. While CIs are now reported, the paper must explicitly justify why this
    subset is representative of the full 848-instance benchmark to avoid selection
    bias in the correlation claims.
- id: 4d165956a5df
  severity: science
  text: The ground-truth construction requires at least two successful agent trajectories
    (Section 3.3). This creates a 'survivorship bias' where the benchmark only evaluates
    exploration on problems solvable by current SOTA agents. The authors must discuss
    how this limits the benchmark's utility for evaluating explorers on harder, currently
    unsolvable issues.
- id: 019fa587d3d5
  severity: science
  text: In the degradation analysis (Section 5.4, Fig 3), the claim that 'missing
    context is the dominant failure mode' relies on a threshold effect observed in
    the data. The authors should clarify if the statistical significance of the jump
    between alpha=50 and alpha=75 holds across all tested patchers, or if it is specific
    to the GPT-5.4-mini/stronger pair.
artifact_hash: d01bf725e90093797f2151085112b0bd34f0dac442648b3b22aae07b0ee791b3
artifact_path: projects/PROJ-687-swe-explore-benchmarking-how-coding-agen/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T20:45:13.396056Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a novel benchmark for repository exploration, but the scientific evidence supporting the generalizability of its findings requires clarification in three areas.

First, the ground-truth annotation methodology (Section 3.3) introduces a significant selection bias. By filtering for instances with at least two successful agent trajectories, the benchmark inherently excludes "unsolvable" or extremely difficult issues. Consequently, the reported metrics (e.g., line-level recall) reflect the exploration capabilities required only for problems that are already within the reach of current SOTA agents. The paper must explicitly address how this limitation affects the validity of claims regarding the "exploration bottleneck" for the broader set of software engineering tasks, particularly those that remain unsolved.

Second, the statistical robustness of the downstream validation (Section 5.2) relies on a subset of n=150 instances to compute correlations between exploration metrics and repair rates. While the authors report 95% confidence intervals, the manuscript does not sufficiently justify the representativeness of this subset relative to the full 848-instance dataset. If the subset was selected based on difficulty or language distribution, the high correlations (e.g., r=0.950 for Context Efficiency) might not generalize to the full benchmark. A brief analysis of the subset's distribution compared to the full set is necessary to rule out sampling bias.

Third, the controlled context degradation analysis (Section 5.4) concludes that missing context is the dominant failure mode based on a sharp performance jump between 50% and 75% of core evidence. While the trend is clear, the paper should provide statistical evidence (e.g., p-values for the pairwise comparisons mentioned in the abstract) confirming that this threshold effect is consistent across different patcher models and not an artifact of the specific GPT-5.4-mini configuration used. Without this, the claim that "modern patchers can tolerate extra irrelevant code" remains a strong observation rather than a statistically verified conclusion.
