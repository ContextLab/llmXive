---
action_items:
- id: a6fed3b5b032
  severity: science
  text: Specify the statistical test used for F1 significance (McNemar is for binary
    EM).
- id: 1a22e32d7127
  severity: science
  text: Clarify train/test split for NQ/HotpotQA to rule out overfitting on evaluation
    sets.
- id: fd73aeb5d69b
  severity: science
  text: Control for hardware/shard configuration in latency comparisons to ensure
    fair baselines.
artifact_hash: 5d85c06c69d8e12a9cf2281b0d8f94964a15c102cc7625c442c21ea4362e7831
artifact_path: projects/PROJ-651-grepseek-training-search-agents-for-dire/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-05T19:00:14.756428Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The empirical evidence is generally robust, with a large evaluation corpus (51,713 queries, Appendix Table 1) and comprehensive baselines including dense retrievers (E5, Qwen3-4B) and agentic methods (Search-R1). The ablation study (Table 3) effectively isolates the contribution of the SFT and GRPO stages, showing significant degradation when either is removed. However, several aspects of the statistical evidence require clarification. First, Table 1 reports statistical significance ($p < 0.05$) for token-level F1 scores, yet the Appendix specifies McNemar’s test exclusively for Exact Match (EM) outcomes. F1 is a continuous metric; the specific test used for F1 significance (e.g., paired t-test, bootstrap confidence intervals) is not stated, raising concerns about the validity of the $^\uparrow$ markers on F1 values.

Second, NQ and HotpotQA are marked with $^*$ as training datasets (Section 3.1, Appendix Table 1) but are included in the evaluation tables (Table 1, Table 2). While test splits are likely disjoint, reporting results on datasets involved in RL fine-tuning risks overfitting to specific benchmark distributions, potentially inflating the claim of "strongest overall performance." It is crucial to demonstrate that gains generalize to unseen datasets (e.g., MuSiQue, Bamboogle) without the training overlap.

Third, the efficiency claims (7.6x speedup, Section 1) rely on sharded parallel execution (Figure 4). The baseline latency comparisons (E5, Qwen3-4B) do not control for shard configuration or hardware parallelism, introducing a confounding variable between algorithmic efficiency and infrastructure scaling. Finally, the corpus is a 2018 Wikipedia dump; performance on newer knowledge (post-2018) is unverified, limiting claims of general corpus interaction robustness. These issues do not invalidate the core findings but require methodological transparency to support the strength of the scientific claims.
