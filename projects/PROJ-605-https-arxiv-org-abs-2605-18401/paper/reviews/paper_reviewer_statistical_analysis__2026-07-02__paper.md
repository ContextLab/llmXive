---
action_items:
- id: e1fa52e7ed68
  severity: science
  text: The paper reports point estimates for performance gains (e.g., +7.9 pp on
    Terminal-Bench 2.0, Table 1) without providing confidence intervals, standard
    errors, or p-values. Given the task counts (N=89 for TB2, N=731 for SWE-Bench
    Pro), statistical significance testing (e.g., McNemar's test or bootstrap CIs)
    is required to validate that observed improvements are not due to random variance.
- id: 25e041afa7f5
  severity: science
  text: Multiple comparisons are performed across difficulty strata (Easy/Medium/Hard)
    and sub-benchmarks (Table 2) without correction (e.g., Bonferroni or Holm-Bonferroni).
    The paper highlights specific gains (e.g., +15.0 pp on Easy tasks) which may be
    inflated by selection bias; a corrected significance threshold or false discovery
    rate control is needed.
- id: b84d5f3682fe
  severity: science
  text: The 'Hard' subset of Terminal-Bench 2.0 contains only 30 tasks (Table 1).
    The reported variance in this stratum (e.g., -6.7 pp drop for online evolution)
    is likely unstable. The authors should report the standard deviation of the metric
    across runs or tasks, or aggregate results to a more robust level, to ensure the
    negative transfer claim is statistically sound.
artifact_hash: fcaf17c52a220725cfb9e8a31b0ca110c5bf54bf4640262b3d2d168e2f060f9e
artifact_path: projects/PROJ-605-https-arxiv-org-abs-2605-18401/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T15:11:16.350386Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in the manuscript is currently insufficient to support the strength of the quantitative claims made. While the experimental design (comparing baselines against offline/online evolution) is sound, the reporting of results lacks necessary statistical rigor.

First, the primary results in Table 1 (Terminal-Bench 2.0) and Table 2 (SWE-Bench Pro) present only point estimates (e.g., "58.9" vs "51.0"). There are no confidence intervals (CIs), standard errors, or p-values associated with these differences. For a benchmark with N=89 tasks, a 7.9 percentage point gain is substantial, but without a measure of variance (e.g., from multiple random seeds or bootstrap resampling), it is impossible to determine if this improvement is statistically significant or a result of random task selection variance. The authors must report 95% confidence intervals for all reported deltas.

Second, the paper conducts multiple hypothesis tests by breaking down results into difficulty levels (Easy, Medium, Hard) and specific sub-benchmarks (e.g., "ansib.", "openl." in Table 2) without addressing the multiple comparisons problem. Highlighting specific large gains (e.g., +15.0 pp on Easy tasks) without correcting for the number of comparisons performed increases the risk of Type I errors. The authors should apply a correction method (such as Bonferroni or Benjamini-Hochberg) or explicitly state that these are exploratory analyses.

Finally, the "Hard" subset in Terminal-Bench 2.0 consists of only 30 tasks. The observed performance drop of -6.7 pp for the online setting in this stratum is a large effect size on a small sample. The stability of this result is questionable without reporting the standard deviation across runs. If the variance is high, this "negative transfer" claim may not be robust. The authors should either increase the sample size for this analysis, aggregate the data, or provide error bars to demonstrate the reliability of the trend.
