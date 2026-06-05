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
reviewed_at: '2026-06-05T10:57:28.615184Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The scientific evidence supporting the LongPT claims is generally structured with appropriate baselines and ablations, yet statistical rigor remains insufficient. Tables 1, 2, and 6 report point estimates without standard deviations or multiple seed runs (e.g., `tab:vqa_effectiveness`, `tab:short_mix_long_vqa`). Without variance metrics, the 7.1% improvement reported in Section 6 cannot be statistically validated against evaluation noise inherent in LLM benchmarks. Evaluation relies heavily on LLM judges (Appendix Evaluation Details), introducing potential bias; human evaluation was only performed on 100 synthesized QA pairs (Appendix Long-Document VQA Details), not the main benchmarks like MMLongBench.

The training budget (5B tokens for a 7B model, Section 3) represents approximately one epoch, raising questions about whether this constitutes "training" versus "lightweight adaptation". The claim of generalization to 512K contexts (Table 8) relies on padding with negative documents (Appendix Longer-Context Evaluation), which tests retrieval in noise rather than coherent long-context understanding. While the mRoPE ablation (Appendix mRoPE Base) is thorough, the lack of confidence intervals on performance metrics limits the robustness of the conclusions regarding optimal frequency scaling.

Furthermore, multiple ablation studies (length distribution, mixture ratios, frequency base) increase the risk of p-hacking without correction for multiple comparisons. To strengthen the evidence, report variance across at least three seeds, clarify the token budget relative to model parameters, and validate LLM-based evaluations with human spot-checks on benchmark subsets. The current evidence supports the observed trends but lacks the statistical weight required for definitive claims on generalization beyond 128K.
