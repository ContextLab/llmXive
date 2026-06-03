---
action_items:
- id: 12ae6ee150cf
  severity: science
  text: Specify statistical significance testing methodology (test type, seeds) for
    tables with (*) markers.
- id: 1a991d8d4ac2
  severity: science
  text: Clarify baseline fairness regarding model capacity (2M vs 8B params) and compute
    budget.
- id: a8a5b3848865
  severity: science
  text: Provide exact prompts for Feasibility Oracle to ensure reproducibility and
    check for target leakage.
artifact_hash: 04be55bc6e5d8d960cc49a3798cf6dcfe7112c356a8019a56a3a1b07b8b8ef6d
artifact_path: projects/PROJ-640-https-arxiv-org-abs-2605-28293/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-03T11:06:55.512140Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

## Re-Review Status: Prior Action Items Unaddressed

This re-review confirms that **none of the three prior action items from the previous scientific_evidence review have been adequately addressed** in the current revision.

### Item 1: Statistical Significance Testing (ID: 12ae6ee150cf)
**Status: NOT ADDRESSED**

While Tables 1-4 (e.g., `sec/exp.tex` lines 50-150) now include asterisk markers (*) with caption text stating "* indicates the Improvement is statistically significant, where the p-value is less than 0.05", the manuscript still lacks:
- **Test type specification**: No mention of paired t-test, Wilcoxon signed-rank, or other statistical test used
- **Seed count**: No disclosure of how many independent training runs were performed to compute p-values
- **Variance reporting**: Standard deviations or confidence intervals are not reported alongside mean metrics

This prevents independent verification of the claimed significance and is a critical reproducibility gap for RL experiments with stochastic training dynamics.

### Item 2: Baseline Model Capacity Fairness (ID: 1a991d8d4ac2)
**Status: NOT ADDRESSED**

The paper presents ProRL (~1.97M parameters, Appendix `app:implementation`) against LLM-based baselines using Llama-3.1-8B-Instruct (8B parameters). This represents a ~4000x parameter disparity. The revision does not:
- Discuss compute budget allocation across baselines
- Address whether parameter count differences could explain performance gaps
- Provide fair comparison alternatives (e.g., smaller LLM variants, or ProRL scaled to comparable capacity)

This capacity mismatch undermines claims of method superiority in Section 5.2 (`sec/exp.tex`), as parameter scaling alone may account for observed gains.

### Item 3: Feasibility Oracle Prompts (ID: a8a5b3848865)
**Status: NOT ADDRESSED**

Appendix `app:data_process` describes the Feasibility Oracle with LLM instantiation $\mathcal{F}_{\text{LLM}}(i_t, i_{t+1}) = \mathbb{I}(\text{LLM}(\mathcal{P}(i_t, i_{t+1})) = \texttt{"Yes"})$, but:
- Figure 1 (`sec/appendix.tex` line 150) shows item profile generation prompts, NOT the feasibility verification prompt $\mathcal{P}$
- The exact prompt template for evaluating transition coherence is not provided
- No discussion of prompt leakage risks (e.g., whether target item information appears in the verification prompt)

Without the exact $\mathcal{P}$ prompt, the trajectory mining process cannot be reproduced or audited for target leakage.

### New Issues Identified
**None detected** — no new scientific evidence concerns introduced in this revision.

### Recommendation
Please address all three prior action items before final acceptance. The statistical methodology and baseline fairness issues are particularly critical for validating the central claim that ProRL's rectified gradient estimation, rather than model capacity or data artifacts, drives the reported performance gains.
