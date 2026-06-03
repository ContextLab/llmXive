---
action_items:
- id: cf336815a043
  severity: science
  text: Report confidence intervals or standard errors for all aggregate metrics in
    Table 1 (lineage search) and Table 3 (idea generation).
- id: 40d6f7b3e3ef
  severity: science
  text: Perform statistical significance tests (e.g., paired t-test, McNemar) for
    baseline comparisons in Sections 4.1 and 4.3.
- id: 208e1a52c3f1
  severity: science
  text: Report inter-annotator agreement (e.g., Krippendorff's alpha) for the human
    evaluation study in Section 4.2.
- id: 5b2cf429673d
  severity: writing
  text: Address multiple-comparison correction when testing across five evaluation
    dimensions in Section 4.2.
artifact_hash: 8cf472ae2a887b5d12e0bb466a1ee80bacbf411e923611b73e3a5325c617cf94
artifact_path: projects/PROJ-569-intern-atlas-a-methodological-evolution/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-03T07:50:54.307750Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis supporting the claims of Intern-Atlas requires significant strengthening to ensure the reported improvements are robust and reproducible. While the scale of the graph construction is impressive, the evaluation metrics lack necessary uncertainty quantification.

In Section 4.1 (Lineage Reconstruction), Table 1 presents point estimates for Node Recall (NR), Edge Recall (ER), and Chain Alignment Score (CAS). Without standard errors or confidence intervals, it is impossible to determine if the observed differences between SGT-MCTS and baselines (e.g., NR 84.8 vs 44.9) are statistically significant or due to random variation in the 133 evaluation chains. A bootstrap analysis or variance reporting is essential.

In Section 4.2 (Idea Evaluation), the comparison with human expert ratings relies on Spearman correlations (Figure 3a). While Intern-Atlas shows higher correlation (0.81 vs 0.58), no statistical test (e.g., Fisher’s z-transformation) is provided to confirm this difference is significant. Furthermore, the human evaluation involving 10 PhD researchers does not report inter-annotator agreement (e.g., Krippendorff's alpha). High variance in human scoring could undermine the validity of the correlation metrics. Additionally, testing across five dimensions without correction for multiple comparisons increases the risk of Type I errors.

In Section 4.3 (Idea Generation), win-rate results (Figure 3b) are reported as percentages (e.g., 88.0%) without binomial confidence intervals or McNemar's test results. Given $N=100$ queries, significance should be explicitly validated. Similarly, Table 3 mean scores lack standard deviations, making it difficult to assess effect sizes.

To improve reproducibility and scientific rigor, please provide uncertainty estimates for all metrics, validate baseline comparisons with appropriate hypothesis tests, and report agreement metrics for human evaluations. These additions are critical for establishing the reliability of the proposed system's performance claims.
