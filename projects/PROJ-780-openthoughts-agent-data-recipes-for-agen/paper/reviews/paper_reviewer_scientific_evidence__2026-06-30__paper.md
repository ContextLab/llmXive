---
action_items:
- id: 1645b7eb038a
  severity: writing
  text: The paper presents an extensive ablation study (>100 runs) on data recipes
    for agentic models, but the statistical rigor required to support the central
    claims is insufficient in several key areas. First, the conclusion regarding teacher
    model selection (Section 3.5, Table 5) asserts that GPT-5.3-Codex is a "worse
    teacher" than GLM-4.7-AWQ, citing a ~5 percentage point drop on Terminal-Bench
    2.0. However, the table reports standard errors (SE) of 1.40 and 0.99 respectively.
    Without a reported p-
artifact_hash: 1762f575d6ad502232c74311f4c0e12a6d2ed21a38bf5e7d1493821d45367039
artifact_path: projects/PROJ-780-openthoughts-agent-data-recipes-for-agen/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T18:54:23.094294Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents an extensive ablation study (>100 runs) on data recipes for agentic models, but the statistical rigor required to support the central claims is insufficient in several key areas.

First, the conclusion regarding teacher model selection (Section 3.5, Table 5) asserts that GPT-5.3-Codex is a "worse teacher" than GLM-4.7-AWQ, citing a ~5 percentage point drop on Terminal-Bench 2.0. However, the table reports standard errors (SE) of 1.40 and 0.99 respectively. Without a reported p-value or a confidence interval, it is impossible to determine if this difference is statistically significant or within the noise of the evaluation harness. Given the high variance in agentic benchmarks, a claim of "worse" performance requires a formal significance test.

Second, the scaling analysis (Figure 2, Section 4) distinguishes between a "plateau" (Method 1) and "continued improvement" (Method 3). The error bars (SE) for Method 3 at the 100k mark overlap with the plateau region of Method 1. The visual distinction is not robust enough to claim a qualitative difference in scaling behavior without a statistical test comparing the slopes or the means at the final data point. The text asserts a plateau where the data shows high variance.

Third, the RL data source ablation (Section 5.1, Table 4) identifies `pymethods2test` as the superior source. While the performance spread (7.6pp) is large, the experimental design does not explicitly control for total compute or training steps across the six sources. If the superior source converged faster or required fewer steps to reach peak performance, the result reflects training efficiency rather than intrinsic data quality. The paper must clarify if the "48 steps" mentioned in Section 5 were fixed for all sources or if early stopping was used, as this would confound the comparison.

Finally, the "compute-controlled" filtering experiment (Table 6) claims that filtering for traces with $\ge$5 turns improves performance even at matched token budgets. However, the filtered set inherently contains more complex, longer tasks. The observed gain (+5.4pp on SWE-Bench) could be attributed to the model learning from harder tasks rather than the specific "turn count" heuristic. A control experiment matching the filtered set to the random set on task difficulty (e.g., using a difficulty proxy) is necessary to isolate the effect of the filter itself.

These issues do not invalidate the dataset release but weaken the causal claims regarding *why* specific data choices work. The authors should add statistical significance tests and clarify compute controls to strengthen the evidence.
