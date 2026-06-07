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
reviewed_at: '2026-06-07T13:15:23.393706Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: full_revision
---

This re-review confirms that the three action items from the previous statistical analysis review remain unaddressed in the current revision. The manuscript has not incorporated the necessary statistical reporting improvements requested in the prior cycle.

First, regarding Appendix `app:sig` (Section "Significance Test Details"), the manuscript still reports only that p-values are "below 0.05" without providing the exact numerical values. Furthermore, no effect size metrics (e.g., rank-biserial correlation) are reported alongside the Mann-Whitney U test results. Exact p-values and effect sizes are required for reproducibility and to assess the magnitude of the observed differences beyond statistical significance, as requested in item `5ab5bf356cf7`.

Second, Table `tab:results_main` (`tabs/main_tab.tex`) continues to present mean scores across the seven benchmarks without any measure of variance. The caption and table body lack standard deviations or 95% confidence intervals. Given that the evaluation protocol involves 16 repeated generation runs, reporting variance is essential to visualize the stability of the performance gains across the evaluation seed distribution, as requested in item `36adfe34e8b0`.

Third, the "Limitations" section does not contain the required clarification regarding the source of variance in the significance tests. The text currently discusses proxy gradients, evaluation focus, and computational overhead, but fails to explicitly state that the reported significance tests reflect evaluation sampling variance rather than training seed variance, acknowledging the single-seed training protocol. This distinction is critical for interpreting the statistical claims correctly and prevents over-interpretation of the results as robust to training initialization, as requested in item `674db1646b05`.

Since these items concern statistical reporting transparency and the interpretation of significance claims (one item is classified as science severity), they must be resolved before the paper can be accepted. The statistical evidence remains difficult to validate without exact p-values, effect sizes, and variance metrics. The single-seed limitation, in particular, affects the validity of the generalization claims regarding the training process.
