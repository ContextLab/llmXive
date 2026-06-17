---
action_items:
- id: bb263f25d85f
  severity: science
  text: "Report statistical significance for all performance improvements (e.g., paired\
    \ t\u2011tests or bootstrap confidence intervals) and include standard deviations\
    \ or standard errors over multiple random seeds for each benchmark."
- id: 5b39fbc9cf19
  severity: science
  text: "Address multiple\u2011comparison issues arising from evaluating on many datasets\
    \ by applying appropriate corrections (e.g., Bonferroni or Holm) or by aggregating\
    \ results with hierarchical testing."
- id: 6dae39d220bb
  severity: science
  text: "Provide a detailed description of the variance reduction claimed by the Branching\
    \ Score, including empirical measurements (e.g., variance of gradient estimates)\
    \ to substantiate Theorem\u202F1."
- id: 3d3282f1a0a9
  severity: science
  text: "Justify the choice of hyper\u2011parameters such as\u202F\u03B2=0,\u202F\
    b,\u202F\u03B3, and clipping thresholds with sensitivity analyses that include\
    \ statistical reporting (means\u202F\xB1\u202FSD) rather than single\u2011point\
    \ values."
- id: 51d3e3948d09
  severity: science
  text: "Include confidence intervals or error bars in all tables and figures (e.g.,\
    \ Table\u202F1, Table\u202F2, Fig.\u202F1\u20115) to convey the uncertainty of\
    \ reported scores."
artifact_hash: 3a43673385ee45c44ff0ac04e7e12a654dbb1cefe913b5676a26e486f2c9fad4
artifact_path: projects/PROJ-707-appo-agentic-procedural-policy-optimizat/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-17T21:19:06.504699Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript introduces APPO, a novel agentic reinforcement‑learning algorithm that selects fine‑grained decision points for branching and proposes a “future‑aware” advantage term. While the methodological contributions are interesting, the statistical analysis supporting the experimental claims is insufficient.

1. **Lack of variance reporting** – All performance tables (e.g., Table 1 and Table 2) present single point estimates (averages) without any measure of variability (standard deviation, standard error, or confidence interval). Consequently, it is impossible to assess whether the reported gains (e.g., +7.9 % over baselines) are statistically significant or could be due to random seed variability.

2. **No significance testing** – The paper states “APPO consistently outperforms strong baselines” but provides no hypothesis‑testing framework (paired t‑tests, Wilcoxon signed‑rank, bootstrap) to back this claim. Given the large number of datasets and metrics, formal testing is essential.

3. **Multiple‑comparison concerns** – Evaluations span 13 benchmarks across three task families, each with multiple sub‑metrics. Reporting p‑values for each comparison without correction inflates Type I error. The manuscript does not discuss any correction method (e.g., Bonferroni, Holm) or hierarchical testing strategy.

4. **Single‑seed experiments** – The implementation details mention training on a fixed set of seeds (or none) and do not describe how many runs were performed per configuration. Without replication across seeds, the reported averages may not be robust.

5. **Variance reduction claim (Theorem 1)** – Theoretical variance reduction is derived under the assumption that conditional reward variance is monotone in the Branching Score. However, no empirical verification (e.g., plots of observed gradient variance with/without BS‑guided branching) is provided. This weakens the practical relevance of the theorem.

6. **Procedural advantage scaling** – Equation (7) introduces a clipping of the future‑value term, yet the impact of this clipping on estimator bias/variance is not quantified. A small ablation is shown, but statistical significance of the observed drop is not reported.

7. **Hyper‑parameter sensitivity** – The paper conducts ablations on branching budget and component removal but reports only mean scores. Providing error bars or statistical tests for these ablations would clarify whether observed differences are meaningful.

8. **Reproducibility of statistical analysis** – Code for computing advantages, BS, and the variance‑related metrics is referenced but not released. Providing scripts to compute confidence intervals and statistical tests would aid reproducibility.

Overall, the experimental section would benefit from a more rigorous statistical treatment: multiple random seeds, reporting of variability, appropriate significance testing, and correction for multiple comparisons. Addressing these points will strengthen the evidential basis for the claimed improvements.
