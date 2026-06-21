---
action_items:
- id: 3bea507e85b2
  severity: science
  text: "Add statistical reporting (e.g., mean\u202F\xB1\u202Fstd, confidence intervals)\
    \ for all benchmark results in Tables\u202F\\ref{tab:video_eval}, \\ref{tab:code_agent_eval},\
    \ and \\ref{tab:tool_use_eval}. Specify the number of evaluation runs, random\
    \ seeds, and any data\u2011splitting strategy."
- id: e611d1658525
  severity: science
  text: "Perform appropriate significance testing (e.g., paired t\u2011test, bootstrap)\
    \ when claiming superiority over baselines such as Qwen3.5\u201135B or InternVL3.5.\
    \ Report p\u2011values or effect sizes."
- id: ab5de23d515c
  severity: science
  text: "Address multiple\u2011comparison concerns: when evaluating on dozens of benchmarks,\
    \ control the family\u2011wise error rate (e.g., Bonferroni or Holm correction)\
    \ or clearly state that each benchmark is considered independently."
- id: 1fc8a45608cd
  severity: writing
  text: "Provide a reproducibility checklist: list software versions, hardware configuration,\
    \ and exact commands used for inference cost measurement (Figure\u202F\\ref{fig:inference_cost}).\
    \ Include scripts or seeds to enable independent replication."
- id: 8d48b092b2e6
  severity: writing
  text: "Clarify handling of missing entries (marked \u201C--\u201D) in evaluation\
    \ tables: explain whether the model was not evaluated, the benchmark was unavailable,\
    \ or results were omitted for other reasons."
artifact_hash: 5db0f3878ddf869f97ae5b85f5c21e6bee16133e4d0bee899b71eabf9aaf1f3a
artifact_path: projects/PROJ-692-kwai-keye-vl-2-0-technical-report/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T09:52:54.115819Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents an impressive suite of benchmark scores (e.g., Table \\ref{tab:video_eval} shows a 74.1 % score on LongVideoBench) but provides no statistical context for these numbers. Across all evaluation tables the authors report single point estimates without any indication of variability (standard deviation, confidence interval) or the number of independent runs. This makes it impossible to assess whether observed differences (e.g., a 1 % gain over Qwen3.5 on Video‑MME‑v2) are statistically meaningful or could be due to random seed effects, data sampling variance, or measurement noise.

The paper also compares the model against many baselines on dozens of tasks, raising a multiple‑comparisons problem. Without correction or a clear statement that each benchmark is treated independently, the risk of cherry‑picking favorable results is high. The authors should either apply a family‑wise error control method (e.g., Bonferroni, Holm) or explicitly limit the scope of inferential claims.

Reproducibility of the reported inference cost (Figure \\ref{fig:inference_cost}) is unclear: the caption mentions “H800 pricing” but the exact hardware configuration, batch sizes, and software stack (e.g., FlashInfer version) are not enumerated. A reproducibility checklist (software versions, random seeds, exact command‑line invocations) would greatly aid verification.

Finally, several entries in the tables are marked “--” without explanation. Readers need to know whether the model was not evaluated, the benchmark was unavailable, or results were omitted for other reasons.

Addressing these statistical and reproducibility gaps will strengthen the credibility of the reported performance gains and align the paper with community standards for rigorous empirical evaluation.
