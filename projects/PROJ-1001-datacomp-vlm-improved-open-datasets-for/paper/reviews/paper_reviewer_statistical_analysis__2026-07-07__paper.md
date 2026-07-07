---
action_items:
- id: b4aceb17370c
  severity: writing
  text: "Sections 4.2 and 5 report benchmark scores as single point estimates without\
    \ uncertainty (SD/SE/CI). Report mean \xB1 SD over \u22653 seeds for main results,\
    \ or explicitly state results are from a single run to avoid implying false precision."
- id: a73420732591
  severity: writing
  text: "Section 3.2 reports Pearson r=0.99 and Spearman \u03C1=0.99 for N=27 without\
    \ confidence intervals or p-values. Add 95% CIs for these correlation coefficients\
    \ to support the statistical significance of the claim."
- id: bd4067cdf437
  severity: writing
  text: Sections 3.1 and 4.1 report specific decimal improvements (e.g., +0.6pp) without
    reported variance. Without SD across seeds, these decimal claims are unsupported.
    Round differences to integers or report variance to justify the precision.
artifact_hash: d4a22931e6b886440cd41104bb215d7473154b2e0677ff1cb31fe0010e81d224
artifact_path: projects/PROJ-1001-datacomp-vlm-improved-open-datasets-for/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-07T10:42:21.158372Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical treatment in this paper generally aligns with ML field norms regarding the omission of formal hypothesis tests for benchmark comparisons. However, there is a consistent lack of uncertainty reporting for primary quantitative claims, which undermines the reliability of the reported improvements.

In **Sections 4.2 and 5**, benchmark scores (e.g., 68.4, 73.0) are presented as single point estimates. The manuscript does not specify the number of training seeds or provide standard deviations (SD), standard errors (SE), or confidence intervals (CI). In deep learning, performance varies across random seeds. Reporting a single number creates a false sense of precision. A reported gain of 0.6 percentage points is statistically indistinguishable from noise if the standard deviation across seeds is >0.5. The authors should report mean ± SD over at least 3 seeds for all main results or explicitly state that numbers come from a single run.

In **Section 3.2**, the authors report a Pearson correlation of $r=0.99$ and Spearman $\rho=0.99$ based on 27 data points. While the correlation is strong, the statistical significance (p-value) and 95% confidence interval are missing. With $N=27$, omitting the confidence interval leaves the inferential claim incomplete.

Finally, in **Sections 3.1 and 4.1**, specific point-difference improvements (e.g., "+1.1pp") are reported to one decimal place. Without accompanying variance metrics, these specific decimal claims are not statistically justified. If variance is not reported, the precision of the reported differences should be reduced (e.g., to integers) to avoid false precision.

These are reporting gaps rather than fundamental errors in test selection, but they prevent the numbers from meaningfully supporting the paper's claims of robust improvements.
