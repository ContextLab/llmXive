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
reviewed_at: '2026-06-05T16:12:35.969916Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis demonstrates methodological soundness in test selection but requires improved reporting transparency. In Appendix `app:sig`, the authors correctly identify that full training repetitions are computationally prohibitive and opt for a one-sided Mann-Whitney U test on evaluation-run-level scores. This non-parametric approach is appropriate for comparing aggregate benchmark scores which may not follow a normal distribution. However, the text claims significance "at both model scales" without reporting the exact p-values or effect sizes. To satisfy reproducibility standards, the specific p-values and a measure of effect size (e.g., rank-biserial correlation) must be included in `app:sig`.

Furthermore, Table `tab:results_main` presents only point estimates (e.g., 28.40) without error bars, standard deviations, or confidence intervals. Given that the significance claims rely on 16 repeated evaluation runs, visualizing this variance in the main results table is critical for readers to assess the stability of the gains. The current presentation obscures the spread of the underlying data distribution.

Regarding scope, the claim in Section `sec:main-results` that DelTA achieves the "best result on every benchmark" implies per-benchmark statistical superiority. However, the significance test in `app:sig` is performed on the question-count weighted aggregate score. If per-benchmark significance is claimed, multiple-comparisons correction (e.g., Bonferroni) is required to control the family-wise error rate. Currently, the analysis aggregates to avoid this, but the text should clarify that the statistical claim applies to the aggregate performance, not necessarily every individual benchmark.

Finally, the single training seed limitation (Section `sec:exp_s`) introduces a confounding variable (training initialization variance) that the significance test does not capture. While acknowledged in `app:sig`, this should be elevated to the main Limitations section with a clearer statement that the reported p-values reflect evaluation noise only, not the stability of the learning trajectory across different random seeds. This distinction is vital for interpreting the statistical validity of the method's superiority.
