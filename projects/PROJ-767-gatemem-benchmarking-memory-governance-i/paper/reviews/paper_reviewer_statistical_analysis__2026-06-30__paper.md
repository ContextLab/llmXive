---
action_items:
- id: 6a06b00b7b6c
  severity: science
  text: MGS is a product of three rates but reported only as point estimates. No confidence
    intervals, standard errors, or bootstrapped distributions are provided. Claims
    of "significant" differences between baselines lack hypothesis testing or error
    bars, making statistical validation impossible.
- id: 34c9e2dc9721
  severity: science
  text: LLM-judge validation relies on a single stratified sample from one run, introducing
    selection bias. Variance from the judge model itself is unquantified. Robust analysis
    requires multiple independent judge runs or multi-annotator reliability metrics
    (e.g., Krippendorff's alpha) across the full dataset.
- id: 012cbd970e8e
  severity: science
  text: Sensitivity analysis (Fig 5) claims "significantly higher" safety without
    p-values or effect sizes. Given discrete top-k and binary outcomes, non-parametric
    tests (e.g., Wilcoxon) are needed to validate trends. Current claims are statistically
    unsupported.
artifact_hash: 4f01dcbb1424147633a4eb29c69325a37730d0263065af71df4aeeea6414618e
artifact_path: projects/PROJ-767-gatemem-benchmarking-memory-governance-i/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T16:15:12.231144Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: full_revision
---

The statistical analysis in the paper is insufficient to support the strong comparative claims made regarding baseline performance. The primary issue is the complete absence of uncertainty quantification for the reported metrics.

The Memory Governance Score (MGS) is defined as a multiplicative function of three rates: $U \cdot (1-A) \cdot (1-F)$. While the paper provides point estimates for these rates in Table 2, it fails to report confidence intervals or standard errors. With a total of 2,218 checkpoints, the standard error for a rate near 0.5 is approximately $\sqrt{0.5 \times 0.5 / 2218} \approx 1.1\%$. However, because MGS is a product of three such rates, the propagation of error is non-linear and likely larger. Without confidence intervals, it is impossible to determine if the observed differences between methods (e.g., the 1.5% difference in MGS between Long-Context and RAG-Policy in the Medical domain for GPT-5.4) are statistically significant or merely noise. The claim that "Long-Context achieves the highest MGS" is a point-estimate observation, not a statistically validated conclusion.

Furthermore, the reliance on LLM-as-a-judge introduces a second layer of variance that is not addressed. The validation in Appendix A4 uses a single stratified sample from one run. This does not quantify the stability of the judge itself. A proper statistical review would require either bootstrapping the judge's output (e.g., running the judge multiple times with temperature > 0 or different seeds) to estimate the variance of the metrics, or a more rigorous multi-annotator study to calculate inter-rater reliability (e.g., Cohen's kappa or Krippendorff's alpha) across the entire dataset, not just a subset. The current validation (97.7% agreement on a subset) is promising but does not replace the need for uncertainty bounds on the final reported scores.

Finally, the sensitivity analysis in Figure 5 (varying top-$k$) presents visual trends but lacks statistical testing. The assertion that Policy RAG is "significantly higher" in safety metrics across all depths is unsupported by p-values or confidence intervals. Given the discrete nature of the top-$k$ parameter and the binary outcomes of the checkpoints, a non-parametric test (e.g., Wilcoxon signed-rank test) or a permutation test should be employed to validate these trends. Without these statistical safeguards, the paper's conclusions about the robustness of specific baselines remain speculative.
