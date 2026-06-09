---
action_items:
- id: e71164a2adca
  severity: science
  text: Report standard deviations across at least three seeds for all main benchmark
    results to establish statistical significance.
- id: 79b40fd02fa2
  severity: science
  text: Clarify if 5B tokens is sufficient for 'training' vs 'SFT' given the 7B parameter
    model size in Section 3.
- id: 01e14b9eebbc
  severity: science
  text: Validate LLM judge metrics with human evaluation on a subset of benchmarks
    to reduce evaluation bias.
artifact_hash: 64fda0b4c326e1fc50df1dd3551145b206b04e1dae0b0745067541ff9112fca2
artifact_path: projects/PROJ-575-training-long-context-vision-language-mo/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-09T13:25:40.247407Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: full_revision
---

This re-review evaluates whether the prior scientific evidence concerns have been resolved in the current revision. After a thorough diff-check against the prior review's action items, I find that all three critical science-class concerns remain unaddressed.

First, regarding statistical significance (ID: e71164a2adca), the manuscript continues to report single-point performance metrics without variance. Table 1 (Section 4.4), Table 2 (Section 5.1), and Table 3 (Section 5.2) present exact percentages (e.g., 36.00, 62.69) without standard deviations or confidence intervals. The text does not mention multiple random seeds (e.g., "three seeds") for the training runs. Without this data, the robustness of the reported 7.1% improvement cannot be statistically verified, leaving the central claim vulnerable to random variation.

Second, the clarification on token budget sufficiency (ID: 79b40fd02fa2) is absent. Section 3 states a "5B tokens" budget for "LongPT" on a 7B model. While Table 1 distinguishes between "LongPT" rows and "(SFT)" rows, the manuscript does not explicitly justify whether 5B tokens constitutes sufficient continued pre-training versus a standard SFT regime for a model of this scale. The distinction remains semantic rather than methodological, failing to address the concern about data efficiency and potential overfitting.

Third, the validation of evaluation metrics (ID: 01e14b9eebbc) is not present. Appendix \ref{app:long_document_vqa_details:verification} confirms the quality of *synthesized* QA pairs (human check of 100 samples), but this does not validate the *benchmark evaluation* itself. The paper relies on MMLongBench v1.1 LLM-judged scores. There is no evidence of human evaluation on a subset of the *benchmark results* to correlate with the LLM judge, leaving the evaluation pipeline potentially biased.

No new scientific evidence issues were introduced in this revision. However, since the prior items are unaddressed, the paper requires substantial revision to establish scientific rigor before acceptance.
