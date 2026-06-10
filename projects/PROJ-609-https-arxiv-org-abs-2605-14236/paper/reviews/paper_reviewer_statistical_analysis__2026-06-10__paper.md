---
action_items:
- id: cafcbcfc7240
  severity: science
  text: Bidirectional-oracle results still lack uncertainty estimates (Table 1). The
    caption states CIs are omitted because bidirectional is 'deterministic given outcomes,'
    but query-level resampling uncertainty remains unquantified. Add bootstrap CIs
    from query resampling or seed variation.
- id: c2ad4450894f
  severity: science
  text: "Multiple-testing correction (Bonferroni/BH) is still absent when reporting\
    \ significance across 9 budget columns \xD7 multiple ranker comparisons (Appendix\
    \ Tables A.10-A.11). This inflates Type I error. Apply and report corrected p-values\
    \ or adjusted significance indicators."
- id: 0f962fc81111
  severity: science
  text: Dependence structure among LLM calls is mentioned in Limitations but not quantified.
    The bootstrap validity assumption (independent oracle outputs) may be violated
    by API caching/hidden state. Add empirical analysis (e.g., autocorrelation of
    outcomes) or sensitivity analysis quantifying impact on CI coverage.
- id: c2f1c0c77019
  severity: science
  text: "Effect-size measures (mean \u0394NDCG@10) are shown in Tables A.10-A.11 but\
    \ without confidence intervals around these differences. Add 95% CIs for effect\
    \ sizes to distinguish statistical from practical significance, as originally\
    \ requested."
artifact_hash: cd07e7bb4bb589b2a1856ce03b3a0d9b21496c25c8e521b71f38e853b3f15fc5
artifact_path: projects/PROJ-609-https-arxiv-org-abs-2605-14236/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-10T21:52:22.057493Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

This re-review finds all four prior action items inadequately addressed:

1. **Bidirectional uncertainty (id: 975930f5a261)**: Table 1 caption still states bidirectional CIs are "omitted" due to determinism. However, query-level variance remains—bootstrap over queries (not just seeds) should be reported. The current justification conflates oracle determinism with result stability.

2. **Multiple-testing correction (id: 160b9279ea2b)**: Appendix Tables A.10-A.11 report significance across 9 budgets × 2 comparison pairs without correction. With 18+ hypothesis tests, uncorrected p<0.05 thresholds yield ~1 false positive expected. Neither Bonferroni nor BH correction is applied or discussed.

3. **Dependence structure (id: 73441eaeea4c)**: The Limitations section (lines 240-260) acknowledges potential LLM API dependence but provides no quantification. Bootstrap CI validity requires independence assumptions; without empirical validation (e.g., lagged autocorrelation of pairwise outcomes), CI coverage claims are unsupported.

4. **Effect-size CIs (id: c47c3d91fe3b)**: Tables A.10-A.11 show mean ΔNDCG@10 but omit uncertainty bands. A +0.1 NDCG difference with CI [−0.3, +0.5] differs substantively from [0.05, +0.15]. This distinction is critical for practical significance claims.

No new statistical issues introduced. However, the four original concerns remain unresolved and require re-analysis before acceptance.
