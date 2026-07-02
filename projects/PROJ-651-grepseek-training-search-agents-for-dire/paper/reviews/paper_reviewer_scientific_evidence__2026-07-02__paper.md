---
action_items:
- id: 5799f428bc2e
  severity: science
  text: The claim of statistical significance (p<0.05) for F1 and EM improvements
    lacks methodological detail. Specify the statistical test used (e.g., McNemar's,
    bootstrap) and report the number of random seeds or runs used to estimate variance,
    as single-run results on large datasets can be noisy.
- id: b22ccb0421fa
  severity: science
  text: The ablation study (Tables 1 & 2) shows a massive performance drop when removing
    SFT, but the 'w/o GRPO' variant still outperforms baselines on some metrics. Clarify
    if the GRPO-only baseline was trained from scratch or initialized from the SFT
    model, as this affects the interpretation of the 'cold-start' contribution.
- id: 0e27a11c94b9
  severity: science
  text: The efficiency claim (14GB RAM vs 221GB) compares the agent's runtime memory
    against the index size of dense retrievers. To support the 'zero offline indexing'
    claim robustly, explicitly state the time required to load the 14GB corpus into
    RAM and whether this 'warm-up' cost is included in the reported 8.67s latency.
artifact_hash: 5d85c06c69d8e12a9cf2281b0d8f94964a15c102cc7625c442c21ea4362e7831
artifact_path: projects/PROJ-651-grepseek-training-search-agents-for-dire/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T14:08:32.372259Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling empirical case for Direct Corpus Interaction (DCI) using shell commands, supported by extensive benchmarking across seven datasets. The central claim—that a compact agent can outperform dense retrievers on multi-hop tasks by avoiding semantic conflation—is well-supported by the reported F1 and Exact Match scores (Table 1, Table 2). The ablation studies (Table 1, Table 2) effectively demonstrate the necessity of both the SFT cold-start and the GRPO refinement stages, with the full model showing consistent gains over variants.

However, the scientific evidence requires minor strengthening regarding statistical rigor and experimental transparency. First, the manuscript repeatedly asserts "statistically significant improvement" (denoted by $^\uparrow$) with $p<0.05$ but does not specify the statistical test employed (e.g., McNemar's test, paired t-test, or bootstrap confidence intervals) nor the number of independent runs (seeds) used to generate the mean scores. Given the stochastic nature of RL training and the large evaluation sets, reporting the variance or the specific test used is essential to validate these significance claims.

Second, the efficiency comparison, while a key contribution, conflates runtime memory usage with index storage size. The claim that the method uses "14GB RAM" versus "221GB for dense indices" (Section 3.2) compares the agent's active memory footprint against the pre-computed index size of baselines. To fully substantiate the "zero offline indexing" advantage, the authors should clarify if the 8.67s latency includes the initial corpus loading time (warm-up) and whether the 14GB figure represents peak memory during the search or the static corpus size.

Finally, the ablation study for the "w/o GRPO" condition (Table 1) shows the model still outperforms most baselines. The text implies this is a "drastic reduction," but the magnitude of improvement over the SFT-only baseline varies by dataset. A brief discussion on whether the GRPO stage primarily improves robustness or just final accuracy on specific hard cases would strengthen the interpretation of the RL contribution. Overall, the evidence is robust, but these clarifications are necessary to fully validate the statistical and efficiency claims.
