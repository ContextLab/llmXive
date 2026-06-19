---
action_items:
- id: c6cad327b7ea
  severity: science
  text: "The manuscript reports point\u2011wise performance gains (e.g., +7.9\u202F\
    pp on Terminal\u2011Bench\_2.0) without any statistical significance testing,\
    \ confidence intervals, or variance estimates. Add appropriate statistical analyses\
    \ (e.g., paired bootstrap, t\u2011tests) to demonstrate that observed gains are\
    \ not due to random variation."
- id: 8c07e508df48
  severity: science
  text: "Multiple comparisons are made across models, settings (online/offline), difficulty\
    \ levels, and benchmark domains. Apply a correction method (e.g., Bonferroni,\
    \ Holm\u2011\u0160id\xE1k, or false discovery rate) and report adjusted p\u2011\
    values or confidence intervals."
- id: 89bef54f51cd
  severity: science
  text: "The paper does not describe the number of random seeds, repetitions, or stochasticity\
    \ in the evaluation pipeline. Provide details on replication (seed values, number\
    \ of runs) and report mean\u202F\xB1\u202Fstandard deviation (or standard error)\
    \ for each metric."
- id: 7f686ca269f0
  severity: science
  text: "Assumptions underlying the chosen statistical tests (e.g., normality, independence\
    \ of task scores) are not discussed. Include diagnostic checks or justify the\
    \ use of non\u2011parametric methods if assumptions are violated."
- id: b5d964e13fc7
  severity: writing
  text: "Reproducibility of the statistical analysis is limited; the code for computing\
    \ deltas and aggregating scores is not referenced. Release the analysis scripts\
    \ and ensure they are version\u2011controlled."
artifact_hash: fcaf17c52a220725cfb9e8a31b0ca110c5bf54bf4640262b3d2d168e2f060f9e
artifact_path: projects/PROJ-605-https-arxiv-org-abs-2605-18401/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-19T13:47:35.486496Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The paper presents impressive absolute point improvements for both Terminal‑Bench 2.0 and SWE‑Bench Pro (e.g., +7.9 pp for GPT‑5.2 offline, +2.6 pp for online evolution). However, the statistical treatment of these results is insufficient. All tables report single point estimates without any measure of variability (standard deviation, confidence interval) or significance testing. Given that each benchmark comprises dozens to hundreds of tasks, the variability across tasks can be substantial; reporting only averages can mask high variance and may overstate the robustness of the gains.

Moreover, the authors compare multiple models (GPT‑5.2, GPT‑5.4 mini), multiple settings (online vs. offline), and several difficulty strata (Easy, Medium, Hard). This constitutes a large family of hypothesis tests, yet no correction for multiple comparisons is applied. Without such correction, the risk of false positives is elevated, especially when some deltas are modest (e.g., +1.1 pp). The manuscript should adopt a principled approach (e.g., Holm‑Šidák or Benjamini‑Hochberg) and report adjusted p‑values or confidence intervals for each reported gain.

The experimental setup section lacks details on stochasticity: it does not state how many random seeds were used, whether the agents were run multiple times per task, or how the “avg@5 Accuracy” and “avg@1 Resolve Rate” were aggregated. Providing mean ± SD (or SE) across seeds would allow readers to assess the stability of the reported improvements. If the evaluation is deterministic, this should be explicitly justified; otherwise, a bootstrap or permutation test could be employed to estimate confidence intervals.

Assumptions underlying any statistical test (e.g., normality of per‑task score differences, independence between tasks) are not discussed. The authors should either verify these assumptions (e.g., via Shapiro‑Wilk tests) or choose non‑parametric alternatives (e.g., Wilcoxon signed‑rank test) that are robust to violations.

Finally, reproducibility of the statistical analysis is limited. The manuscript does not provide the scripts used to compute deltas, aggregate scores, or perform any statistical tests. Releasing these scripts (with version control) and specifying random seeds would greatly enhance transparency and enable independent verification.

Addressing these points will strengthen the empirical claims and align the work with standard statistical reporting practices in the field.
