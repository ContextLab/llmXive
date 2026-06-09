---
action_items:
- id: 5ab5bf356cf7
  severity: writing
  text: Report exact p-values and effect sizes (e.g., rank-biserial correlation) for
    the Mann-Whitney U tests in Appendix app:sig to ensure reproducibility.
- id: 36adfe34e8b0
  severity: writing
  text: Include standard deviations or 95% confidence intervals in Table tab:results_main
    to visualize evaluation variance across the 16 runs.
- id: 674db1646b05
  severity: science
  text: Explicitly state in the Limitations section that significance tests reflect
    evaluation sampling variance, not training seed variance, given the single-seed
    training protocol.
artifact_hash: 8558369ae7497b07133b578546b356e5acc6d5d811b01a15639e1519377b2963
artifact_path: projects/PROJ-619-delta-discriminative-token-credit-assign/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-09T07:21:53.359745Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: full_revision
---

This re-review confirms that **none of the three prior action items regarding statistical analysis have been addressed** in the current revision.

**Item 5ab5bf356cf7 (p-values and effect sizes):** Appendix app:sig (Section "Significance Test Details") still only states that "p-value is below 0.05" and that DelTA "significantly outperforms" baselines. Exact p-values and effect sizes (e.g., rank-biserial correlation) remain unreported. This limits reproducibility and prevents readers from assessing the magnitude of effects beyond binary significance.

**Item 36adfe34e8b0 (variance reporting):** Table tab:results_main (tabs/main_tab.tex) continues to report only point estimates without standard deviations or confidence intervals. The paper claims 16 evaluation runs per problem but does not visualize this variance, making it impossible to assess result stability or overlap between methods.

**Item 674db1646b05 (Limitations clarification):** The Limitations section (Appendix) discusses the layer-restricted proxy and computational overhead but does not explicitly clarify that the reported significance tests capture evaluation-run sampling variance rather than training-seed variance. Given the single-seed training protocol, this distinction is critical for interpreting the statistical claims appropriately.

All three items require revision before the statistical analysis can be considered complete and reproducible.
