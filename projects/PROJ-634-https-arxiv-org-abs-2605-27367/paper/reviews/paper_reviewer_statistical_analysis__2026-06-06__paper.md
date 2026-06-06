---
action_items:
- id: 459582ee323c
  severity: science
  text: Provide measures of variability (e.g., standard deviation, confidence intervals)
    for all reported quantitative metrics (AbsRel, AUC@30, ATE, etc.) across scenes
    and datasets to convey statistical uncertainty.
- id: 7195a034d5b9
  severity: science
  text: "When comparing models, perform appropriate statistical significance tests\
    \ (e.g., paired t\u2011test or Wilcoxon signed\u2011rank test) and report p\u2011\
    values to substantiate claims of superiority."
- id: f44b860b842c
  severity: science
  text: "Apply a multiple\u2011comparisons correction (e.g., Bonferroni, Holm\u2011\
    Bonferroni, or Benjamini\u2011Hochberg FDR) to control family\u2011wise error\
    \ rate given the large number of model\u2011dataset comparisons."
- id: 5c35b7ebad23
  severity: writing
  text: Document random seeds, evaluation order, and any stochastic components of
    the evaluation pipeline to ensure full reproducibility of the reported numbers.
- id: ad94a5fdb378
  severity: writing
  text: "Include a brief statistical analysis section describing the methodology for\
    \ aggregating per\u2011scene results (e.g., mean vs. median) and justification\
    \ for the chosen aggregation strategy."
artifact_hash: 306c5e78aff3c136de96c4c6956084c3af89239f10c2fba4682734d1809d3475
artifact_path: projects/PROJ-634-https-arxiv-org-abs-2605-27367/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-06T10:45:01.550811Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript introduces **SpatialBench**, a comprehensive benchmark covering 19 datasets, 546 scenes, and 41 model variants across six methodological paradigms. While the benchmark’s breadth is impressive, the statistical treatment of the reported results is insufficient for rigorous scientific conclusions.

**Key statistical concerns**

1. **Absence of variability estimates** – All tables (e.g., Table 1, Table 2, detailed per‑dataset tables) present single point estimates for metrics such as AbsRel, AUC@30, ATE, and F‑Score. No standard deviations, confidence intervals, or inter‑quartile ranges are provided, making it impossible to gauge the reliability of the numbers or to assess whether observed differences are meaningful.

2. **No significance testing** – The paper frequently claims that “full‑context attention defines the accuracy upper bound” or that “DA3‑Giant improves depth error by 47 %”. These statements are not backed by statistical tests (e.g., paired t‑tests, Wilcoxon signed‑rank) that would demonstrate that the improvements are statistically significant rather than due to random variation across scenes.

3. **Multiple‑comparison problem** – With 41 models evaluated on >100 scene‑regimes, the number of pairwise comparisons exceeds several hundred. The manuscript does not discuss any correction for multiple hypothesis testing, raising the risk of false‑positive claims about model superiority.

4. **Aggregation methodology** – The paper aggregates per‑scene results into “Average” columns, but it does not justify the use of arithmetic mean versus median, nor does it discuss the impact of outlier scenes (e.g., OOM failures) on the aggregates. This lack of transparency hampers reproducibility and interpretability.

5. **Reproducibility of stochastic components** – The evaluation pipeline involves random frame selection (e.g., set‑cover selection, dense‑regime striding) and stochastic training components (e.g., camera conditioning probability). The manuscript does not report random seeds or the number of repeats, which is essential for reproducing the exact numbers.

**Recommendations for improvement**

- **Report variability**: For each metric, include standard deviation or 95 % confidence intervals across scenes (or across multiple runs if stochastic). This can be added as an extra column or within parentheses in the tables.

- **Statistical testing**: When asserting that one model outperforms another, perform paired statistical tests on per‑scene metric differences and report the resulting p‑values. Highlight results that survive a reasonable significance threshold (e.g., p < 0.05).

- **Multiple‑comparison correction**: Apply a correction method (Bonferroni, Holm‑Bonferroni, or Benjamini‑Hochberg) to the family of tests performed across models and domains. Indicate which comparisons remain significant after correction.

- **Clarify aggregation**: Explain the choice of mean versus median, and consider reporting both. Exclude or specially mark OOM/timeout cases rather than folding them into the average without comment.

- **Reproducibility details**: Provide the random seeds used for frame selection, any stochastic data augmentation, and the number of evaluation repetitions. Release the exact evaluation scripts and configuration files.

Addressing these points will greatly strengthen the scientific rigor of the benchmark and ensure that the claimed performance gaps are statistically sound and reproducible.
